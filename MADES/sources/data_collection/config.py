# Dicionário de tickers do FRED API
FRED_TICKERS = {
    # United States
    "US_FEDFUNDS": "FEDFUNDS",
    "US_FEDFUNDS_DAILY": "DFF",
    "US_CPI": "CPIAUCSL",
    "US_10Y": "DGS10",

    # Euro Area
    "ECB_MAIN_REFINANCING": "ECBMRRFR",

    # Germany
    "GERMANY_CPI": "DEUCPIALLMINMEI",

    # France
    "FRANCE_CPI": "FRACPIALLMINMEI",

    # Italy
    "ITALY_CPI": "ITACPIALLMINMEI",

    # United Kingdom
    "UK_CPI": "GBRCPIALLMINMEI",

    # Japan
    "JAPAN_INTERBANK_RATE": "IR3TIB01JPM156N",
    "JAPAN_CPI": "JPNCPIALLMINMEI",

    # China
    "CHINA_INTERBANK_RATE": "IR3TIB01CNM156N",
    "CHINA_CPI": "CHNCPIALLMINMEI",

    # India
    "INDIA_CALL_MONEY_RATE": "IRSTCI01INM156N",
    "INDIA_CPI": "INDCPIALLMINMEI",

    # Brazil
    "BRAZIL_CPI": "BRACPIALLMINMEI",

    # South Africa
    "SOUTH_AFRICA_CALL_MONEY_RATE": "IRSTCI01ZAM156N",
    "SOUTH_AFRICA_CPI": "ZAFCPIALLMINMEI",
}

# Dicionário de tickers do YFinance
YFINANCE_TICKERS = {
    # United States
    "US_DXY": "DX-Y.NYB",
    "NASDAQ_100": "^NDX",

    # Germany
    "DAX": "^GDAXI",

    # France
    "CAC_40": "^FCHI",

    # Italy
    "FTSE_MIB": "FTSEMIB.MI",

    # United Kingdom
    "FTSE_100": "^FTSE",
    "GBP_USD": "GBPUSD=X",

    # Canada
    "SP_TSX": "^GSPTSE",
    "USD_CAD": "USDCAD=X",

    # Japan
    "NIKKEI_225": "^N225",
    "USD_JPY": "USDJPY=X",

    # China
    "USD_CNY": "USDCNY=X",

    # India
    "NIFTY_50": "^NSEI",

    # Brazil
    "IBOVESPA": "^BVSP",
    "USD_BRL": "USDBRL=X",

    # South Africa
    "USD_ZAR": "USDZAR=X",

    # Cryptocurrency
    "BITCOIN": "BTC-USD",
}

# Dicionário de tickers/séries das outras APIs
OFFICIAL_TICKERS = {
    "UK_POLICY_RATE": "IUDBEDR",
    "CANADA_POLICY_RATE": "V39079",
    "BRAZIL_SELIC": "432",
    "CANADA_CPI": "18-10-0004-01",
}

# Defasagem de publicação (em dias corridos) de cada série.
# O FRED data os dados mensais pelo INÍCIO do mês de referência (o CPI de janeiro
# fica em 01/01), mas o número só é divulgado semanas depois. Sem essa defasagem,
# o forward fill coloca no dia 01/01 uma informação que o investidor só teria em
# meados de fevereiro (vazamento). Valores conservadores, ver pipeline2.md.
PUBLICATION_LAGS = {
    # CPI dos EUA: BLS divulga por volta do dia 10-15 do mês seguinte
    "US_CPI": 45,
    # CPIs nacionais (via OCDE/FRED e Statistics Canada): divulgação nacional até a
    # 3ª semana do mês seguinte
    "GERMANY_CPI": 55,
    "FRANCE_CPI": 55,
    "ITALY_CPI": 55,
    "UK_CPI": 55,
    "JAPAN_CPI": 55,
    "CHINA_CPI": 55,
    "INDIA_CPI": 55,
    "BRAZIL_CPI": 55,
    "SOUTH_AFRICA_CPI": 55,
    "CANADA_CPI": 55,
    # Médias mensais de juros: só são conhecidas depois que o mês termina
    "US_FEDFUNDS": 32,
    "JAPAN_INTERBANK_RATE": 35,
    "CHINA_INTERBANK_RATE": 35,
    "INDIA_CALL_MONEY_RATE": 35,
    "SOUTH_AFRICA_CALL_MONEY_RATE": 35,
    # Séries diárias do FRED são publicadas no dia útil seguinte
    "US_FEDFUNDS_DAILY": 1,
    "US_10Y": 1,
    # Taxas de política monetária (BCE, BoE, BoC, Selic) são anunciadas antes de
    # entrarem em vigor, e os preços de mercado fecham antes das 24h UTC (fechamento
    # do candle do BTC): defasagem 0
}

def get_tickers():
    return FRED_TICKERS, YFINANCE_TICKERS, OFFICIAL_TICKERS