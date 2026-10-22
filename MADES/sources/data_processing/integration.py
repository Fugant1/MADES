import pandas as pd
from pathlib import Path


class DataIntegration:
    """
    Junta a base estruturada (mercado + macro, já point-in-time) com a base
    diária de notícias do GDELT, usando o calendário do BTC.

    Alinhamento temporal: o candle diário do BTC (yfinance) vai de 00h a 24h UTC,
    e os timestamps do GDELT também estão em UTC. Assim, a linha do dia t contém
    apenas informação disponível até as 24h UTC de t: o fechamento do BTC, o
    fechamento das bolsas (todas fecham antes das 24h UTC), as séries macro já
    divulgadas e as notícias publicadas no dia t.
    """

    def __init__(self):
        script_dir = Path(__file__).parent.resolve()
        self.data_dir = script_dir.parent / "data"

    def run(self, struc=None, news=None):
        if struc is None:
            struc = pd.read_csv(self.data_dir / "struc_pit_dataframe.csv", index_col="Date", parse_dates=True)
        if news is None:
            news = pd.read_csv(self.data_dir / "news_daily.csv", index_col="Date", parse_dates=True)

        # Left join no calendário do BTC. Antes de 2017 não há notícias (NaN): essas
        # linhas ficam na base porque servem de aquecimento para as features de
        # mercado (médias móveis, volatilidade de 30 dias etc.)
        df = struc.join(news, how="left")

        # Dentro do período coberto pelo GDELT, dia sem notícia = contagem 0
        news_start, news_end = news.index.min(), news.index.max()
        dentro = (df.index >= news_start) & (df.index <= news_end)
        count_cols = [c for c in news.columns if c.endswith(("_count", "_sum"))]
        df.loc[dentro, count_cols] = df.loc[dentro, count_cols].fillna(0)

        df["has_news_coverage"] = dentro.astype(int)

        output = self.data_dir / "integrated_dataframe.csv"
        df.to_csv(output)
        print(f"Base integrada salva em '{output}' | {df.shape} | "
              f"notícias de {news_start.date()} a {news_end.date()}")
        return df


if __name__ == "__main__":
    DataIntegration().run()
