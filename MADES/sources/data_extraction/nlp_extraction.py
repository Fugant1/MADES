import pandas as pd
from google.cloud import bigquery

caminho_chave = "civil-song-468401-d4-27368e8236d4.json" 
client = bigquery.Client.from_service_account_json(caminho_chave)

# ==========================================
# 1. A QUERY COM FILTROS DE QUALIDADE
# ==========================================
query = """
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
  AND _PARTITIONTIME BETWEEN TIMESTAMP('2020-01-01') AND TIMESTAMP('2026-01-31')
QUALIFY ROW_NUMBER() OVER(PARTITION BY DocumentIdentifier ORDER BY DATE DESC) = 1
"""

# ==========================================
# 2. VALIDAÇÃO (DRY RUN)
# ==========================================
job_config_dry = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
dry_run_job = client.query(query, job_config=job_config_dry)
gb_processed = dry_run_job.total_bytes_processed / (1024 ** 3)

# Note que o valor em GB será parecido, pois o BigQuery cobra pela 
# coluna lida antes do filtro, mas o resultado final (as linhas baixadas)
# será MUITO menor, mais leve e de altíssima qualidade.
print(f"Essa query vai processar: {gb_processed:.2f} GB no servidor")


# ==========================================
# 3. EXTRAÇÃO PARA O PANDAS (ML)
# ==========================================
EXECUTAR_DE_VERDADE = True

if EXECUTAR_DE_VERDADE:
    print("Baixando dados limpíssimos...")
    # Passamos a opção create_bqstorage_client=False para forçar a API REST normal
    df = client.query(query).to_dataframe(create_bqstorage_client=False)  
    # Mostra o tamanho real em Megabytes que o Pandas ocupou na sua memória RAM
    tamanho_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"Tamanho REAL baixado para o seu PC: {tamanho_mb:.2f} MB")
    print(f"Quantidade de notícias encontradas: {len(df)} linhas")
    print(f"Sucesso! {len(df)} notícias únicas e confiáveis baixadas.")
    print(df.head())
    
    df.to_csv("dados_bitcoin_gdelt_limpos.csv", index=False)
    print("Dados salvos!")