import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score, mean_squared_error
from lightgbm import LGBMRegressor, LGBMClassifier

"""
Validação walk-forward (janela expansiva por ano) e modelos baseline.

Por que walk-forward e não k-fold: em série temporal, k-fold embaralhado treina
com o futuro e testa no passado (vazamento). Aqui cada ano de teste só vê dados
anteriores a ele, como aconteceria em produção. O embargo remove do treino os
últimos dias cujo alvo (janela futura de 7 dias) invadiria o ano de teste.
"""

TEST_YEARS = list(range(2020, 2026))
EMBARGO_DAYS = 7
SEED = 42
# Regularização do HAR-X. Valor fixo (não otimizado no conjunto de teste, para não
# vazar); os resultados são praticamente iguais para alpha entre 10 e 100.
RIDGE_ALPHA = 10.0


def walk_forward_splits(index, test_years=TEST_YEARS, embargo=EMBARGO_DAYS):
    for y in test_years:
        start = pd.Timestamp(f"{y}-01-01")
        train = index < start - pd.Timedelta(days=embargo)
        test = (index >= start) & (index < pd.Timestamp(f"{y + 1}-01-01"))
        yield y, train, test


# ----------------------------------------------------------------------------
# Volatilidade
# ----------------------------------------------------------------------------

def _lgbm_reg():
    return LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=50,
                         subsample=0.8, subsample_freq=1, colsample_bytree=0.7, random_state=SEED, verbose=-1)


HAR_COLS = ["btc_rv_1d", "btc_rv_7d", "btc_rv_30d"]


def _har_X(data):
    return np.log(data[HAR_COLS].clip(lower=1e-4)).add_prefix("log_")


def volatility_walk_forward(data, feature_sets, target="target_logvol_7d"):
    """
    Compara: persistência (vol dos últimos 7 dias), HAR (Corsi, 2009) e LightGBM
    com diferentes conjuntos de features. Retorna previsões fora da amostra.
    """
    d = data.dropna(subset=[target] + HAR_COLS)
    preds = pd.DataFrame(index=d.index)
    preds["real"] = d[target]

    for y, tr, te in walk_forward_splits(d.index):
        ytr = d.loc[tr, target]
        preds.loc[te, "media_treino"] = ytr.mean()
        preds.loc[te, "persistencia"] = np.log(d.loc[te, "btc_rv_7d"].clip(lower=1e-4))

        har = LinearRegression().fit(_har_X(d.loc[tr]), ytr)
        preds.loc[te, "HAR"] = har.predict(_har_X(d.loc[te]))

        for nome, cols in feature_sets.items():
            # HAR-X: HAR + variáveis exógenas, linear com regularização (Ridge)
            Xtr = pd.concat([_har_X(d.loc[tr]), d.loc[tr, cols]], axis=1)
            Xte = pd.concat([_har_X(d.loc[te]), d.loc[te, cols]], axis=1)
            ridge = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=RIDGE_ALPHA))
            preds.loc[te, f"HARX_{nome}"] = ridge.fit(Xtr, ytr).predict(Xte)
            # LightGBM com as mesmas entradas (não linear)
            preds.loc[te, f"LGBM_{nome}"] = _lgbm_reg().fit(Xtr, ytr).predict(Xte)
    return preds


def volatility_metrics(preds):
    linhas = []
    modelos = [c for c in preds.columns if c != "real"]
    for y in sorted(preds.index.year.unique()):
        p = preds[preds.index.year == y]
        for mdl in modelos:
            linhas.append({"ano": y, "modelo": mdl,
                           "rmse": np.sqrt(mean_squared_error(p["real"], p[mdl])),
                           "r2_oos": 1 - ((p["real"] - p[mdl]) ** 2).sum() / ((p["real"] - p["media_treino"]) ** 2).sum()})
    por_ano = pd.DataFrame(linhas)
    geral = pd.DataFrame([{
        "modelo": mdl,
        "rmse": np.sqrt(mean_squared_error(preds["real"], preds[mdl])),
        "r2_oos": 1 - ((preds["real"] - preds[mdl]) ** 2).sum() / ((preds["real"] - preds["media_treino"]) ** 2).sum(),
        "corr": preds["real"].corr(preds[mdl]),
    } for mdl in modelos]).set_index("modelo")
    return geral, por_ano


def diebold_mariano(real, f1, f2, h=7):
    """
    Teste de Diebold-Mariano (perda quadrática): H0 = os dois modelos têm o mesmo
    erro esperado. d < 0 favorece f1. Variância de Newey-West com h-1 defasagens,
    porque o alvo de 7 dias faz os erros de dias vizinhos se sobreporem.
    """
    from scipy import stats
    d = ((real - f1) ** 2 - (real - f2) ** 2).dropna().values
    n = len(d)
    dc = d - d.mean()
    gamma = [np.sum(dc[k:] * dc[:n - k]) / n for k in range(h)]
    var = gamma[0] + 2 * sum((1 - k / h) * gamma[k] for k in range(1, h))
    stat = d.mean() / np.sqrt(var / n)
    return stat, 2 * stats.norm.sf(abs(stat))


def garch_forecast(r, test_years=TEST_YEARS, horizon=7):
    """
    GARCH(1,1) com erros t de Student, reestimado a cada ano de teste (só com
    dados anteriores) e filtrado dia a dia com os parâmetros fixos.
    Retorna o log da volatilidade média prevista para os próximos `horizon` dias.
    """
    from arch import arch_model

    r = r.dropna() * 100
    out = pd.Series(index=r.index, dtype=float)
    for y in test_years:
        start = pd.Timestamp(f"{y}-01-01")
        end = pd.Timestamp(f"{y + 1}-01-01")
        res = arch_model(r[r.index < start], vol="GARCH", p=1, q=1, dist="t", mean="Constant").fit(disp="off")
        filt = arch_model(r[r.index < end], vol="GARCH", p=1, q=1, dist="t", mean="Constant").fix(res.params)
        fc = filt.forecast(horizon=horizon, start=start, reindex=False)
        var = fc.variance.mean(axis=1)
        out.loc[var.index] = np.log(np.sqrt(var) / 100)
    return out.dropna()


# ----------------------------------------------------------------------------
# Direção
# ----------------------------------------------------------------------------

def _logit():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                         LogisticRegression(C=0.05, class_weight="balanced", max_iter=2000))


def _lgbm_clf():
    return LGBMClassifier(n_estimators=200, learning_rate=0.02, num_leaves=7, min_child_samples=100,
                          subsample=0.8, subsample_freq=1, colsample_bytree=0.6, reg_lambda=5.0,
                          class_weight="balanced", random_state=SEED, verbose=-1)


def direction_walk_forward(data, feature_sets, target="target_up"):
    """
    Classificação da direção do dia seguinte. Retorna, para cada modelo e
    conjunto de features, a classe prevista e a probabilidade de alta
    (no caso binário) ou da classe "compra" (no caso de 3 classes).
    """
    d = data.dropna(subset=[target])
    preds = pd.DataFrame(index=d.index)
    preds["real"] = d[target]
    pos_label = 1.0

    for y, tr, te in walk_forward_splits(d.index):
        ytr = d.loc[tr, target]
        maj = ytr.mode().iloc[0]
        preds.loc[te, "maioria_pred"] = maj
        preds.loc[te, "maioria_proba"] = (ytr == pos_label).mean()

        for nome, cols in feature_sets.items():
            for tag, factory in [("logit", _logit), ("LGBM", _lgbm_clf)]:
                m = factory().fit(d.loc[tr, cols], ytr)
                classes = list(m.classes_)
                proba = m.predict_proba(d.loc[te, cols])
                preds.loc[te, f"{tag}_{nome}_pred"] = m.predict(d.loc[te, cols])
                preds.loc[te, f"{tag}_{nome}_proba"] = proba[:, classes.index(pos_label)]
    return preds


def direction_metrics(preds, n_boot=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    real = preds["real"]
    binario = set(real.unique()) <= {0.0, 1.0}
    linhas = []
    for col in [c for c in preds.columns if c.endswith("_pred")]:
        nome = col[:-5]
        linha = {"modelo": nome,
                 "acuracia_balanceada": balanced_accuracy_score(real, preds[col]),
                 "f1_macro": f1_score(real, preds[col], average="macro")}
        if binario and preds[f"{nome}_proba"].nunique() > 1:
            proba = preds[f"{nome}_proba"].values
            auc = roc_auc_score(real, proba)
            boots = []
            for _ in range(n_boot):
                # bootstrap em blocos de 30 dias, preservando a dependência temporal
                starts = rng.integers(0, len(real) - 30, len(real) // 30)
                idx = np.concatenate([np.arange(s, s + 30) for s in starts])
                if len(np.unique(real.values[idx])) == 2:
                    boots.append(roc_auc_score(real.values[idx], proba[idx]))
            linha.update({"auc": auc, "auc_ic95_inf": np.percentile(boots, 2.5),
                          "auc_ic95_sup": np.percentile(boots, 97.5)})
        linhas.append(linha)
    return pd.DataFrame(linhas).set_index("modelo")


def feature_importance(data, cols, target="target_up", top=20):
    d = data.dropna(subset=[target])
    m = _lgbm_clf().fit(d[cols], d[target])
    imp = pd.Series(m.booster_.feature_importance("gain"), index=cols)
    return (imp / imp.sum()).sort_values(ascending=False).head(top)


# ----------------------------------------------------------------------------
# Backtest: direção (notícias) x tamanho da posição (volatilidade)
# ----------------------------------------------------------------------------

def backtest(ret_next, signal, size=None, cost=0.0015):
    """
    ret_next: retorno simples de t+1 (o que se ganha ao ficar posicionado do fim de t ao fim de t+1)
    signal: posição desejada em [0, 1] decidida no fim de t (long/flat, sem venda a descoberto)
    size: multiplicador de tamanho (ex.: alvo de volatilidade), também decidido em t
    cost: custo por unidade negociada (taxa + slippage de um lado = 0,15%)
    """
    pos = signal if size is None else signal * size
    pos = pos.clip(0, 1)
    turnover = pos.diff().abs().fillna(pos.abs())
    pnl = pos * ret_next - turnover * cost
    return pnl


def performance(pnl, periods=365):
    eq = (1 + pnl).cumprod()
    anos = len(pnl) / periods
    cagr = eq.iloc[-1] ** (1 / anos) - 1
    vol = pnl.std() * np.sqrt(periods)
    sharpe = pnl.mean() / pnl.std() * np.sqrt(periods) if pnl.std() > 0 else np.nan
    mdd = (eq / eq.cummax() - 1).min()
    return {"CAGR_%": cagr * 100, "vol_anual_%": vol * 100, "sharpe": sharpe, "max_drawdown_%": mdd * 100,
            "retorno_total_%": (eq.iloc[-1] - 1) * 100}
