import numpy as np
import pandas as pd

"""
Engenharia de features e definição dos alvos.

Regra geral (anti-vazamento): toda feature da linha t usa apenas informação
disponível até as 24h UTC do dia t. Os alvos usam t+1 em diante e NUNCA
entram como feature.
"""

INDICES = ["NASDAQ_100", "DAX", "CAC_40", "FTSE_MIB", "FTSE_100", "SP_TSX", "NIKKEI_225", "NIFTY_50", "IBOVESPA"]
FX = ["US_DXY", "GBP_USD", "USD_CAD", "USD_JPY", "USD_CNY", "USD_BRL", "USD_ZAR"]
RATES = ["US_FEDFUNDS_DAILY", "US_10Y", "ECB_MAIN_REFINANCING", "UK_POLICY_RATE", "CANADA_POLICY_RATE",
         "BRAZIL_SELIC", "JAPAN_INTERBANK_RATE", "CHINA_INTERBANK_RATE", "INDIA_CALL_MONEY_RATE",
         "SOUTH_AFRICA_CALL_MONEY_RATE"]
CPIS = ["US_CPI", "GERMANY_CPI", "FRANCE_CPI", "ITALY_CPI", "UK_CPI", "JAPAN_CPI", "CHINA_CPI",
        "INDIA_CPI", "BRAZIL_CPI", "SOUTH_AFRICA_CPI", "CANADA_CPI"]

# Custo de uma operação de ida e volta: 0,10% de taxa por lado (taxa taker padrão
# de corretora spot) + 0,05% de slippage por lado = 0,30%
TAU_DEFAULT = 0.003


def _rsi(close, n=14):
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / down)


def _zscore_past(s, window):
    """z-score em relação à janela ANTERIOR (exclui o próprio dia)."""
    m = s.shift(1).rolling(window, min_periods=window // 2).mean()
    sd = s.shift(1).rolling(window, min_periods=window // 2).std()
    # Janela sem variação (ex.: cluster raro, sempre 0) -> z indefinido
    return (s - m) / sd.replace(0, np.nan)


def btc_features(df):
    out = pd.DataFrame(index=df.index)
    close, high, low = df["BTC_Close"], df["BTC_High"], df["BTC_Low"]
    r = np.log(close).diff()

    out["btc_ret_1d"] = r
    out["btc_ret_lag1"] = r.shift(1)
    out["btc_ret_lag2"] = r.shift(2)
    out["btc_ret_7d"] = np.log(close / close.shift(7))
    out["btc_ret_30d"] = np.log(close / close.shift(30))

    # Volatilidade realizada (componentes do modelo HAR: diária, semanal, mensal)
    out["btc_rv_1d"] = r.abs()
    out["btc_rv_7d"] = np.sqrt((r ** 2).rolling(7).mean())
    out["btc_rv_30d"] = np.sqrt((r ** 2).rolling(30).mean())
    # Volatilidade de Parkinson: usa a amplitude máxima-mínima do dia
    park = np.log(high / low) ** 2 / (4 * np.log(2))
    out["btc_parkinson_7d"] = np.sqrt(park.rolling(7).mean())
    out["btc_downside_rv_7d"] = np.sqrt((r.clip(upper=0) ** 2).rolling(7).mean())

    logvol = np.log(df["BTC_Volume"].replace(0, np.nan))
    out["btc_volume_chg"] = logvol.diff()
    out["btc_volume_z30"] = _zscore_past(logvol, 30)

    out["btc_rsi14"] = _rsi(close, 14)
    out["btc_sma7_gap"] = close / close.rolling(7).mean() - 1
    out["btc_sma14_gap"] = close / close.rolling(14).mean() - 1
    sma20, sd20 = close.rolling(20).mean(), close.rolling(20).std()
    out["btc_boll_pctb"] = (close - (sma20 - 2 * sd20)) / (4 * sd20)
    out["btc_drawdown_365"] = close / close.rolling(365, min_periods=30).max() - 1
    return out


def market_macro_features(df):
    out = pd.DataFrame(index=df.index)

    rets = np.log(df[INDICES + FX]).diff()
    for c in INDICES + FX:
        out[f"{c.lower()}_ret_1d"] = rets[c]
        out[f"{c.lower()}_ret_5d"] = np.log(df[c] / df[c].shift(5))
    out["global_equity_ret_1d"] = rets[INDICES].mean(axis=1)
    out["global_equity_rv_30d"] = np.sqrt((rets[INDICES].mean(axis=1) ** 2).rolling(30).mean())
    out["nasdaq_rv_30d"] = np.sqrt((rets["NASDAQ_100"] ** 2).rolling(30).mean())

    # Juros: nível e variação em 90 dias (pontos percentuais)
    for c in RATES:
        out[f"{c.lower()}_level"] = df[c]
        out[f"{c.lower()}_chg90"] = df[c] - df[c].shift(90)
    out["us_10y_chg5"] = df["US_10Y"] - df["US_10Y"].shift(5)
    out["us_term_spread"] = df["US_10Y"] - df["US_FEDFUNDS_DAILY"]

    # Inflação acumulada em 12 meses (sobre as séries já defasadas)
    for c in CPIS:
        out[f"{c.lower()}_yoy"] = np.log(df[c] / df[c].shift(365))
    out["global_cpi_yoy"] = out[[f"{c.lower()}_yoy" for c in CPIS]].mean(axis=1)

    out["is_weekend"] = (df.index.dayofweek >= 5).astype(int)
    return out


def news_features(df, n_clusters):
    """Features do GDELT. Médias são ponderadas pelo número de notícias (somas / contagens)."""
    out = pd.DataFrame(index=df.index)
    cnt = df["news_count"]
    tone = df["news_tone_adj_sum"]

    out["news_log_count"] = np.log1p(cnt)
    out["news_count_z30"] = _zscore_past(np.log1p(cnt), 30)

    def wmean(num, den, w):
        return num.rolling(w).sum() / den.rolling(w).sum().replace(0, np.nan)

    for w in [1, 3, 7, 30]:
        out[f"news_tone_{w}d"] = wmean(tone, cnt, w)
    # Dias sem notícia: o tom de 1 dia não existe; usa o último conhecido
    out["news_tone_1d"] = out["news_tone_1d"].ffill()
    out["news_tone_z90"] = _zscore_past(out["news_tone_1d"], 90)
    out["news_tone_mom"] = out["news_tone_3d"] - out["news_tone_30d"]
    out["news_neg_share_7d"] = wmean(df["news_neg_count"], cnt, 7)
    out["news_pos_share_7d"] = wmean(df["news_pos_count"], cnt, 7)
    out["news_tone_disp_7d"] = df["news_tone_std"].rolling(7, min_periods=1).mean()

    for c in range(1, n_clusters + 1):
        cc, ct = df[f"clu{c}_count"], df[f"clu{c}_tone_adj_sum"]
        out[f"clu{c}_share_7d"] = wmean(cc, cnt, 7)
        out[f"clu{c}_tone_7d"] = wmean(ct, cc, 7)
        out[f"clu{c}_count_z30"] = _zscore_past(np.log1p(cc), 30)
    return out


def build_targets(df, tau=TAU_DEFAULT):
    out = pd.DataFrame(index=df.index)
    r = np.log(df["BTC_Close"]).diff()
    r_next = r.shift(-1)
    simple_next = np.expm1(r_next)

    out["target_ret_1d"] = r_next
    out["target_up"] = (r_next > 0).astype(float).where(r_next.notna())
    out["target_class"] = np.select([simple_next > tau, simple_next < -tau], [1, -1], 0).astype(float)
    out.loc[r_next.isna(), "target_class"] = np.nan
    # Volatilidade realizada dos PRÓXIMOS 7 dias (t+1 ... t+7), em log
    fwd_var = (r ** 2).rolling(7).mean().shift(-7)
    out["target_logvol_7d"] = np.log(np.sqrt(fwd_var))
    out["target_absret_1d"] = r_next.abs()
    return out


def build_dataset(df, n_clusters, tau=TAU_DEFAULT, start="2017-02-01"):
    """
    Junta features e alvos. Começa em fev/2017: o GDELT começa em jan/2017 e as
    features de notícia precisam de ~30 dias de aquecimento.
    """
    feats = pd.concat([btc_features(df), market_macro_features(df), news_features(df, n_clusters)], axis=1)
    feats = feats.replace([np.inf, -np.inf], np.nan)
    data = pd.concat([feats, build_targets(df, tau)], axis=1).loc[start:]

    # Níveis de juros ficam fora dos conjuntos de modelagem: são quase constantes por
    # anos e mudam de patamar entre regimes, então um modelo treinado em 2017-2019
    # (juro zero) não tem como generalizar para 2022-2023 (juro alto). Usamos as
    # variações (chg90), que são comparáveis entre regimes.
    groups = {
        "btc": [c for c in feats.columns if c.startswith("btc_")],
        "mercado_macro": [c for c in market_macro_features(df.iloc[:400]).columns if not c.endswith("_level")],
        "noticias": [c for c in feats.columns if c.startswith(("news_", "clu"))],
        # Conjuntos enxutos para o HAR-X (poucas variáveis com motivação econômica)
        "mercado_vol": ["btc_parkinson_7d", "btc_downside_rv_7d", "btc_volume_z30",
                        "nasdaq_rv_30d", "global_equity_rv_30d", "is_weekend"],
        "noticias_atencao": ["news_log_count", "news_count_z30", "news_neg_share_7d", "news_tone_disp_7d"],
    }
    return data, groups
