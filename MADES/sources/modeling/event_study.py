import numpy as np
import pandas as pd
from scipy import stats

"""
Estudo de eventos (event study) sobre o retorno do BTC.

Modelo de retorno normal: média constante (mean-adjusted), estimada numa janela
anterior ao evento. É o modelo padrão em estudos de eventos com cripto, porque o
BTC negocia 7 dias por semana e não tem um "índice de mercado" natural para o
modelo de mercado (que exigiria descartar fins de semana).
"""


def detect_events(signal, threshold=2.0, direction="neg", min_gap=10, valid=None):
    """
    Marca dias em que o sinal (já padronizado, ex.: z-score do tom) cruza o limiar.
    min_gap: descarta eventos a menos de min_gap dias de um evento anterior do mesmo
    tipo (declustering), para as janelas não se sobreporem e os eventos serem
    aproximadamente independentes.
    """
    s = signal.copy()
    if valid is not None:
        s = s.where(valid)
    hits = s[s < -threshold] if direction == "neg" else s[s > threshold]

    eventos, ultimo = [], None
    for d in hits.index:
        if ultimo is None or (d - ultimo).days > min_gap:
            eventos.append(d)
            ultimo = d
    return pd.DatetimeIndex(eventos)


def abnormal_returns(r, events, window=(-5, 10), estimation=(-120, -11)):
    """Matriz evento x dia relativo com os retornos anormais (AR)."""
    rel = range(window[0], window[1] + 1)
    pos = {d: i for i, d in enumerate(r.index)}
    linhas = {}
    for e in events:
        if e not in pos:
            continue
        i = pos[e]
        if i + estimation[0] < 0 or i + window[1] >= len(r):
            continue
        mu = r.iloc[i + estimation[0]: i + estimation[1] + 1].mean()
        linhas[e] = [r.iloc[i + k] - mu for k in rel]
    return pd.DataFrame.from_dict(linhas, orient="index", columns=list(rel))


def car_table(ar, windows=((-5, -1), (0, 0), (1, 1), (1, 5), (1, 10))):
    """CAR médio em cada janela, com teste t (paramétrico) e Wilcoxon (não paramétrico)."""
    linhas = []
    for a, b in windows:
        car = ar.loc[:, a:b].sum(axis=1)
        t, p_t = stats.ttest_1samp(car, 0)
        p_w = stats.wilcoxon(car).pvalue if len(car) > 10 else np.nan
        linhas.append({
            "janela": f"[{a:+d}, {b:+d}]",
            "CAR_medio_%": car.mean() * 100,
            "CAR_mediano_%": car.median() * 100,
            "%_positivos": (car > 0).mean() * 100,
            "t": t, "p_t": p_t, "p_wilcoxon": p_w,
        })
    return pd.DataFrame(linhas).set_index("janela")


def placebo_test(r, events, candidate_days, window=(1, 5), n_iter=2000, seed=0, **kw):
    """
    Teste de permutação: sorteia o mesmo número de datas "falsas" entre os dias
    candidatos e compara o CAR médio real com a distribuição dos placebos.
    Robusto a caudas pesadas e à autocorrelação da volatilidade.
    """
    rng = np.random.default_rng(seed)
    real = abnormal_returns(r, events, **kw).loc[:, window[0]:window[1]].sum(axis=1).mean()
    cands = pd.DatetimeIndex(candidate_days)
    sims = []
    for _ in range(n_iter):
        fake = pd.DatetimeIndex(rng.choice(cands, size=len(events), replace=False)).sort_values()
        sims.append(abnormal_returns(r, fake, **kw).loc[:, window[0]:window[1]].sum(axis=1).mean())
    sims = np.array(sims)
    p = (np.sum(np.abs(sims - sims.mean()) >= abs(real - sims.mean())) + 1) / (n_iter + 1)
    return real, sims, p
