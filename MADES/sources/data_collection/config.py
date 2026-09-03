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

def get_tickers():
    return FRED_TICKERS, YFINANCE_TICKERS, OFFICIAL_TICKERS