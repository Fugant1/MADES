import pandas as pd
import yfinance as yf
from fredapi import Fred
import warnings
import os
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# ==========================================
# CONFIGURAÇÕES INICIAIS

load_dotenv()

fred = Fred(api_key=os.getenv("FRED_API_KEY"))

START_DATE = '2016-01-01'
END_DATE = '2026-01-31'

# ==========================================
# DICIONÁRIOS DE TICKERS 

FRED_SERIES = {
    # United States
    "US_FEDFUNDS": "FEDFUNDS",
    "US_CPI": "CPIAUCSL",

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

    # Canada
    "CANADA_CPI": "CANCPIALLMINMEI",

    # Japan
    "JAPAN_CPI": "JAPCPIALLMINMEI",

    # China
    "CHINA_CPI": "CHNCPIALLMINMEI",

    # India
    "INDIA_CPI": "INDCPIALLMINMEI",

    # Brazil
    "BRAZIL_CPI": "BRACPIALLMINMEI",

    # South Africa
    "SOUTH_AFRICA_CPI": "ZAFCPIALLMINMEI",
}


YF_TICKERS = {
    "DXY": "DX-Y.NYB",
    "NASDAQ_100": "^NDX",
    "US10Y": "^TNX",

    "DAX": "^GDAXI",
    "CAC40": "^FCHI",
    "FTSE_MIB": "FTSEMIB.MI",

    "FTSE100": "^FTSE",
    "GBPUSD": "GBP=X",

    "SP_TSX": "^GSPTSE",
    "USDCAD": "CAD=X",

    "NIKKEI225": "^N225",
    "USDJPY": "JPY=X",

    "USDCNY": "CNY=X",

    "NIFTY50": "^NSEI",

    "IBOVESPA": "^BVSP",
    "USDBRL": "BRL=X",

    "JSE_ALL_SHARE": "^J203.JO",
    "USDZAR": "ZAR=X",
}

BTC_TICKER = "BTC-USD"

def get_fred_data():
    # Inicializa o DataFrame que armazenará as séries macroeconômicas
    print("Coletando dados macroeconômicos do FRED...")
    df_fred = pd.DataFrame()

    # Consulta cada série configurada 
    for col_name, ticker in FRED_SERIES.items():
        try:
            series = fred.get_series(ticker, observation_start=START_DATE, observation_end=END_DATE)
            df_fred[col_name] = series
        except Exception as e:
            print(f"Erro ao coletar {ticker}: {e}")
    
    if not df_fred.empty:
        # Padroniza o índice e propaga o último valor mensal para os dias seguintes
        df_fred.index.name = 'Date'
        # Resample para converter dados mensais em diários mantendo o último valor
        df_fred = df_fred.resample('D').ffill()
    return df_fred

def get_yf_data():
    # Inicializa o DataFrame que armazenará os dados de mercado
    print("Coletando dados de mercado do Yahoo Finance...")
    df_yf = pd.DataFrame()
    
    # Baixa os ativos de mercado
    tickers_list = list(YF_TICKERS.values())
    
    # Baixando em lote para eficiência
    data = yf.download(tickers_list, start=START_DATE, end=END_DATE)
    
    # Seleciona o preço de fechamento de cada ativo 
    for col_name, ticker in YF_TICKERS.items():
        try:
            df_yf[col_name] = data['Close'][ticker]
        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")

    # Coletando os dados completos do Bitcoin
    print("Coletando Bitcoin (OHLCV)...")
    # Mantém as colunas de abertura, máxima, mínima, fechamento e volume 
    btc_data = yf.download('BTC-USD', start=START_DATE, end=END_DATE)
    df_yf['BTC_Open'] = btc_data['Open']
    df_yf['BTC_High'] = btc_data['High']
    df_yf['BTC_Low'] = btc_data['Low']
    df_yf['BTC_Close'] = btc_data['Close']
    df_yf['BTC_Volume'] = btc_data['Volume']
    
    # Padroniza o índice de datas e remove o fuso horário para permitir a junção 
    df_yf.index.name = 'Date'
    df_yf.index = df_yf.index.tz_localize(None) # Evita conflito de timezone no Join
    return df_yf

def main():
    print("Iniciando Pipeline de Extração...")
    
    # Coleta dos dados
    df_yf = get_yf_data()
    df_fred = get_fred_data() 
    
    # Junção dos dados FRED e YFINANCE
    print("Unindo os datasets...")
    df_final = df_yf.join(df_fred, how='outer')
    
    # Tratamento de Feriados e Calendários Distintos (Forward Fill)
    print("Aplicando Forward Fill e limpando nulos iniciais...")
    df_final.ffill(inplace=True)
    df_final.dropna(inplace=True)
    
    # Exportação
    parquet_file = 'base_df.parquet'
    csv_file = 'base_df.csv'
    
    df_final.to_parquet(parquet_file, engine='pyarrow')
    df_final.to_csv(csv_file)
    print(f"Sucesso! Dados salvos em {parquet_file} e {csv_file}")

if __name__ == '__main__':
    main()
