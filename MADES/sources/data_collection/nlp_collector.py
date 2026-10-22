import os
from pathlib import Path
from dotenv import load_dotenv

"""
Coleta das notícias do GDELT GKG via BigQuery.

A base atual foi coletada em duas execuções desta query:
    - dados_bitcoin_gdelt_limpos.csv   -> 2020-01 a 2026-01 (48.649 notícias)
    - dados_bitcoin_gdelt_limpos_2.csv -> 2017-01 a 2019-12 (30.554 notícias)
Os CSVs ficam em sources/data/ (fora do Git, ver pipeline2.md).

A chave da conta de serviço do Google Cloud NÃO fica no repositório: o caminho
vem da variável de ambiente GOOGLE_APPLICATION_CREDENTIALS (arquivo .env).
"""

QUERY = """
    SELECT
  PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING)) AS EventTimestamp,
  SourceCommonName AS Source,
  DocumentIdentifier AS URL,
  CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) AS SentimentScore,

  -- As duas minas de ouro para o seu One-Hot Encoding:
  V2Themes AS Temas,
  V2Organizations AS Organizacoes

FROM
  `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE
  (LOWER(V2Persons) LIKE '%bitcoin%' OR LOWER(V2Themes) LIKE '%bitcoin%')
  AND SourceCommonName IN ('bloomberg.com', 'reuters.com', 'coindesk.com', 'cointelegraph.com', 'theblock.co')
  AND _PARTITIONTIME BETWEEN TIMESTAMP('{start}') AND TIMESTAMP('{end}')
QUALIFY ROW_NUMBER() OVER(PARTITION BY DocumentIdentifier ORDER BY DATE DESC) = 1
"""


def collect_news(start, end, output_name, execute=False):
    """
    Faz um dry run (estimativa de custo em GB) e, se execute=True, baixa as
    notícias do período e salva em sources/data/<output_name>.
    """
    from google.cloud import bigquery

    load_dotenv()
    client = bigquery.Client.from_service_account_json(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    query = QUERY.format(start=start, end=end)

    # Dry run: o BigQuery cobra pela coluna lida antes do filtro
    job_config_dry = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    gb_processed = client.query(query, job_config=job_config_dry).total_bytes_processed / (1024 ** 3)
    print(f"Essa query vai processar: {gb_processed:.2f} GB no servidor")

    if not execute:
        return None

    # create_bqstorage_client=False força a API REST normal
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    print(f"Notícias únicas baixadas: {len(df)} | {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

    data_dir = Path(__file__).parent.parent.resolve() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(data_dir / output_name, index=False)
    print(f"Dados salvos em {data_dir / output_name}")
    return df


if __name__ == "__main__":
    collect_news("2017-01-01", "2019-12-31", "dados_bitcoin_gdelt_limpos_2.csv", execute=False)
