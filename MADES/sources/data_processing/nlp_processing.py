import numpy as np
import pandas as pd
from pathlib import Path
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import normalize
from sklearn.metrics import adjusted_rand_score, silhouette_score


class NewsProcessing:
    """
    Pipeline dos dados não estruturados (GDELT GKG).

    Etapas:
        1. load_news: junta os CSVs coletados e remove duplicatas por URL
        2. build_concept_matrix: matriz binária notícia x conceito (80 temas + 50 organizações)
        3. select_k / cluster_concepts: agrupa os conceitos por coocorrência (Ward)
        4. daily_features: agrega tudo por dia (UTC), no calendário do BTC

    Todas as decisões estão justificadas em pipeline2.md.
    """

    NEWS_FILES = ["dados_bitcoin_gdelt_limpos.csv", "dados_bitcoin_gdelt_limpos_2.csv"]

    # Stop-word de domínio: aparece em 99,64% das notícias (a busca foi por bitcoin)
    DOMAIN_STOPWORDS = {"ECON_BITCOIN"}

    N_THEMES = 80
    N_ORGS = 50

    # Critério de escolha de k: maior k cuja estabilidade (ARI médio no bootstrap) >= ARI_MIN
    K_RANGE = range(4, 21)
    ARI_MIN = 0.90
    N_BOOTSTRAP = 40

    # Limiar de tom para contar uma notícia como "negativa" / "positiva"
    TONE_NEG = -2.0
    TONE_POS = 2.0

    def __init__(self, seed=42):
        script_dir = Path(__file__).parent.resolve()
        self.data_dir = script_dir.parent / "data"
        self.seed = seed

        self.df = None
        self.features = None
        self.X = None
        self.k = None
        self.labels = None
        self.k_diagnostics = None

    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entities(raw):
        """GDELT guarda 'ENTIDADE,offset;ENTIDADE,offset'. Mantém só os nomes, sem repetir."""
        if pd.isna(raw):
            return []
        items = str(raw).replace(",", ";").split(";")
        return list({i.strip() for i in items if i.strip() and not i.strip().isdigit()})

    def load_news(self):
        frames = []
        for name in self.NEWS_FILES:
            path = self.data_dir / name
            if path.exists():
                frames.append(pd.read_csv(path))
            else:
                print(f"Aviso: {name} não encontrado em {self.data_dir}")

        df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["URL"]).reset_index(drop=True)
        df["EventTimestamp"] = pd.to_datetime(df["EventTimestamp"], utc=True)
        df["Date"] = df["EventTimestamp"].dt.tz_localize(None).dt.normalize()
        df = df.sort_values("EventTimestamp").reset_index(drop=True)

        # Tom ajustado pela fonte: cada veículo tem um "tom de base" diferente
        # (Bloomberg -1,7; CoinDesk -0,5) e a composição de fontes muda muito ao longo
        # dos anos. Subtraímos a média histórica da fonte calculada só com notícias
        # anteriores (expanding + shift), para não usar informação futura.
        prior_mean = (
            df.groupby("Source")["SentimentScore"]
            .transform(lambda s: s.expanding().mean().shift(1))
        )
        df["ToneAdj"] = df["SentimentScore"] - prior_mean.fillna(df["SentimentScore"].mean())

        self.df = df
        print(f"Notícias únicas: {len(df):,} | {df['Date'].min().date()} a {df['Date'].max().date()}")
        return df

    # ------------------------------------------------------------------

    def build_concept_matrix(self):
        themes = self.df["Temas"].apply(self._extract_entities)
        orgs = self.df["Organizacoes"].apply(self._extract_entities)

        theme_counts = themes.explode().value_counts()
        theme_counts = theme_counts[~theme_counts.index.isin(self.DOMAIN_STOPWORDS)]
        org_counts = orgs.explode().value_counts()

        self.features = (
            ["TAG_" + t for t in theme_counts.head(self.N_THEMES).index]
            + ["ORG_" + o for o in org_counts.head(self.N_ORGS).index]
        )
        idx = {f: i for i, f in enumerate(self.features)}

        X = np.zeros((len(self.df), len(self.features)), dtype=bool)
        for i, (t_list, o_list) in enumerate(zip(themes, orgs)):
            for t in t_list:
                j = idx.get("TAG_" + t)
                if j is not None:
                    X[i, j] = True
            for o in o_list:
                j = idx.get("ORG_" + o)
                if j is not None:
                    X[i, j] = True
        self.X = X

        cobertura = X.any(axis=1).mean()
        print(f"Matriz notícia x conceito: {X.shape} | cobertura: {cobertura:.2%} das notícias")
        return X

    def _concept_space(self, X):
        # Cada conceito vira um vetor sobre as notícias; L2 faz a distância euclidiana
        # equivaler à distância de cosseno (coocorrência angular)
        return normalize(X.astype(float).T)

    # ------------------------------------------------------------------

    def select_k(self):
        """
        O Silhouette cresce de forma monotônica até k = 60 nesta base (ele premia pares
        de conceitos quase duplicados), então não tem máximo interior e não serve para
        escolher k. Usamos dois critérios:
          - estabilidade: reamostramos as NOTÍCIAS com bootstrap, reagrupamos os conceitos
            e medimos o ARI contra o agrupamento da base completa;
          - salto no dendrograma: altura da fusão que levaria de k para k-1 clusters.
        Escolha: maior k com ARI médio >= ARI_MIN (agrupamento reprodutível).
        """
        Xc = self._concept_space(self.X)
        Z = linkage(Xc, method="ward")
        heights = Z[:, 2][::-1]
        base = {k: fcluster(Z, k, "maxclust") for k in self.K_RANGE}

        rng = np.random.default_rng(self.seed)
        ari = {k: [] for k in self.K_RANGE}
        for _ in range(self.N_BOOTSTRAP):
            sample = rng.integers(0, len(self.X), len(self.X))
            Zb = linkage(self._concept_space(self.X[sample]), method="ward")
            for k in self.K_RANGE:
                ari[k].append(adjusted_rand_score(base[k], fcluster(Zb, k, "maxclust")))

        diag = pd.DataFrame({
            "k": list(self.K_RANGE),
            "silhouette": [silhouette_score(Xc, base[k]) for k in self.K_RANGE],
            "ari_medio": [np.mean(ari[k]) for k in self.K_RANGE],
            "ari_min": [np.min(ari[k]) for k in self.K_RANGE],
            "salto_dendrograma": [heights[k - 2] - heights[k - 1] for k in self.K_RANGE],
        }).set_index("k")
        self.k_diagnostics = diag

        estaveis = diag[diag["ari_medio"] >= self.ARI_MIN]
        self.k = int(estaveis.index.max())
        print(f"k escolhido: {self.k} (ARI médio = {diag.loc[self.k, 'ari_medio']:.3f})")
        return self.k, diag

    def cluster_concepts(self, k=None):
        if k is None:
            k = self.k or self.select_k()[0]
        self.k = k
        Z = linkage(self._concept_space(self.X), method="ward")
        labels = fcluster(Z, k, "maxclust") - 1

        # Renumera os clusters pela cobertura (cluster 1 = o que aparece em mais notícias)
        cobertura = np.array([self.X[:, labels == c].any(axis=1).mean() for c in range(k)])
        ordem = np.argsort(-cobertura)
        remap = {old: new for new, old in enumerate(ordem)}
        self.labels = np.array([remap[c] for c in labels])
        return self.labels

    def cluster_table(self):
        """Tabela conceito -> cluster, com a frequência de cada conceito."""
        freq = self.X.mean(axis=0)
        tab = pd.DataFrame({
            "conceito": self.features,
            "tipo": ["tema" if f.startswith("TAG_") else "organizacao" for f in self.features],
            "cluster": self.labels + 1,
            "freq_noticias": freq,
        }).sort_values(["cluster", "freq_noticias"], ascending=[True, False])

        # Nome curto do cluster: os 3 conceitos mais frequentes
        nomes = (
            tab.groupby("cluster")["conceito"]
            .apply(lambda s: " | ".join(c.replace("TAG_", "").replace("ORG_", "") for c in s.head(3)))
        )
        tab["nome_cluster"] = tab["cluster"].map(nomes)
        return tab

    # ------------------------------------------------------------------

    def daily_features(self):
        """
        Agrega por dia UTC (mesmo fechamento do candle diário do BTC).
        Guardamos somas e contagens (e não só médias) para que médias móveis
        ponderadas possam ser calculadas depois de forma exata, inclusive
        em dias sem notícia.
        """
        df = self.df.copy()
        df["neg"] = (df["SentimentScore"] < self.TONE_NEG).astype(int)
        df["pos"] = (df["SentimentScore"] > self.TONE_POS).astype(int)

        g = df.groupby("Date")
        daily = pd.DataFrame({
            "news_count": g.size(),
            "news_tone_sum": g["SentimentScore"].sum(),
            "news_tone_adj_sum": g["ToneAdj"].sum(),
            "news_tone_mean": g["SentimentScore"].mean(),
            "news_tone_adj_mean": g["ToneAdj"].mean(),
            "news_tone_std": g["SentimentScore"].std(),
            "news_neg_count": g["neg"].sum(),
            "news_pos_count": g["pos"].sum(),
        })

        for c in range(self.k):
            flag = self.X[:, self.labels == c].any(axis=1)
            sub = df[flag].groupby("Date")
            daily[f"clu{c + 1}_count"] = sub.size()
            daily[f"clu{c + 1}_tone_adj_sum"] = sub["ToneAdj"].sum()

        # Calendário completo (dias sem notícia ficam com contagem 0 e médias NaN)
        full = pd.date_range(daily.index.min(), daily.index.max(), freq="D", name="Date")
        daily = daily.reindex(full)
        count_cols = [c for c in daily.columns if c.endswith(("_count", "_sum"))]
        daily[count_cols] = daily[count_cols].fillna(0)
        return daily

    # ------------------------------------------------------------------

    def run(self, k=None):
        self.load_news()
        self.build_concept_matrix()
        if k is None:
            self.select_k()
        self.cluster_concepts(k)

        daily = self.daily_features()
        tabela = self.cluster_table()

        daily.to_csv(self.data_dir / "news_daily.csv")
        tabela.to_csv(self.data_dir / "news_clusters.csv", index=False)
        if self.k_diagnostics is not None:
            self.k_diagnostics.to_csv(self.data_dir / "news_k_selection.csv")

        print(f"Base diária salva: {daily.shape} | clusters: {self.k}")
        return daily, tabela


if __name__ == "__main__":
    NewsProcessing().run()
