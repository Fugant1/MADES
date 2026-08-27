import pandas as pd
import yfinance as yf
from fredapi import Fred
import requests
import warnings
import os
from io import StringIO
from dotenv import load_dotenv
from config import get_tickers

class DataCollector:

    def __init__(self):
        warnings.filterwarnings('ignore')

        # Carrega variáveis de ambiente
        load_dotenv()

        # Inicializa a API do FRED
        self.fred = Fred(
            api_key=os.getenv("FRED_API_KEY")
        )

        # Período de coleta
        self.START_DATE = '2016-01-01'
        self.END_DATE = '2026-01-01'

        # Carrega os dicionários 
        self.fred_tickers, self.yfinance_tickers, self.official_series = get_tickers()

#-----------------------------------------------------------------------------

    def get_fred_data(self):
        """ 
        Coleta as séries configuradas no FRED,
        converte para frequência diária e salva em CSV
        """

        print("Coletando dados do FRED...")

        df_fred = pd.DataFrame() 

        # Loop com try/except para coletar cada uma das variáveis
        for col_name, ticker in self.fred_tickers.items():
            try:
                series = self.fred.get_series(
                    ticker,
                    observation_start=self.START_DATE,
                    observation_end=self.END_DATE
                )

                df_fred[col_name] = series

                print(f"{col_name} ({ticker}) coletado corretamente!")

            except Exception as e:
                print(f"Erro ao coletar {col_name} ({ticker}): {e}")

        if not df_fred.empty:
            # Padroniza o índice
            df_fred.index = pd.to_datetime(df_fred.index)
            df_fred.index.name = "Date"

            # Converte todas as séries para frequência diária
            # e faz forward fill
            df_fred = df_fred.resample("D").ffill()

            # Salva o CSV para verificar depois
            df_fred.to_csv("fred_data.csv")
            print("\nDados do FRED salvos em 'fred_data.csv'.")
            print(f"Dimensões: {df_fred.shape}")

        return df_fred

#-----------------------------------------------------------------------------

    def get_yf_data(self):
        """
        Coleta dados de mercado do Yahoo Finance.
        Para ativos financeiros, coleta o preço de fechamento.
        Para Bitcoin, coleta OHLCV completo.
        """
        
        print("Coletando dados do Yahoo Finance...")

        df_yf = pd.DataFrame()

        # Exclui Bitcoin, que será coletado separadamente com OHLCV completo
        market_tickers = {
            name: ticker
            for name, ticker in self.yfinance_tickers.items()
            if name != "BITCOIN"
        }

        tickers_list = list(market_tickers.values())

        # Baixa em lote para maior eficiência
        data = yf.download(
            tickers_list,
            start=self.START_DATE,
            end=self.END_DATE,
            auto_adjust=False,
            progress=False
        )

        # Seleciona o preço de fechamento de cada ativo
        for col_name, ticker in market_tickers.items():

            try:
                if ticker in data["Close"].columns:
                    df_yf[col_name] = data["Close"][ticker]
                    print(f"{col_name} ({ticker}) coletado corretamente!")
                else:
                    print(f"Nenhum dado encontrado para {ticker}")

            except Exception as e:
                print(f"Erro ao processar {ticker}: {e}")

        # Coleta o bitcoin separado (OHLCV) 
        print("Coletando Bitcoin...")

        btc_ticker = self.yfinance_tickers["BITCOIN"]

        try:
            btc_data = yf.download(
                btc_ticker,
                start=self.START_DATE,
                end=self.END_DATE,
                auto_adjust=False,
                progress=False
            )

            df_yf["BTC_Open"] = btc_data["Open"]
            df_yf["BTC_High"] = btc_data["High"]
            df_yf["BTC_Low"] = btc_data["Low"]
            df_yf["BTC_Close"] = btc_data["Close"]
            df_yf["BTC_Volume"] = btc_data["Volume"]

            print(f"Bitcoin ({btc_ticker}) coletado corretamente!")

        except Exception as e:
            print(f"Erro ao coletar Bitcoin: {e}")

        # Verificação 
        if df_yf.empty:
            print("Nenhum dado foi coletado do Yahoo Finance.")
            return df_yf

        # Padroniza o índice
        df_yf.index = pd.to_datetime(df_yf.index)
        df_yf.index.name = "Date"

        # Remove timezone, caso exista
        if df_yf.index.tz is not None:
            df_yf.index = df_yf.index.tz_localize(None)

        # Salva em CSV
        df_yf.to_csv("yfinance_data.csv")
        print("Dados salvos em 'yfinance_data.csv'")
        print(f"Dimensões: {df_yf.shape}")

        return df_yf

#-----------------------------------------------------------------------------

    def get_uk_policy_rate(self):
        print("Coletando BOE Official Rate...")

        boe_data = pd.DataFrame()

        try:

            # Série IUDBEDR - Official Bank Rate
            url = (
                "https://www.bankofengland.co.uk/boeapps/database/"
                "_iadb-fromshowcolumns.asp"
            )

            params = {
                "csv.x": "yes",
                "Datefrom": self.START_DATE,
                "Dateto": self.END_DATE,
                "SeriesCodes": self.official_series["UK_POLICY_RATE"],
                "CSVF": "TN",
                "UsingCodes": "Y",
                "VPD": "Y",
                "VFD": "N"
            }

            response = requests.get(
                url,
                params=params
            )

            response.raise_for_status()

            # O CSV do Bank of England possui algumas
            # linhas de metadados.
            lines = response.text.splitlines()

            # Localiza a linha do cabeçalho
            header_index = next(
                i
                for i, line in enumerate(lines)
                if "DATE" in line.upper()
            )

            boe_data = pd.read_csv(
                StringIO(
                    "\n".join(lines[header_index:])
                )
            )

            # Renomeia as colunas
            boe_data.columns = [
                "Date",
                "UK_POLICY_RATE"
            ]

            # Converte tipos
            boe_data["Date"] = pd.to_datetime(
                boe_data["Date"]
            )

            boe_data["UK_POLICY_RATE"] = pd.to_numeric(
                boe_data["UK_POLICY_RATE"],
                errors="coerce"
            )

            # Define Date como índice
            boe_data = boe_data.set_index("Date")
            boe_data.index.name = "Date"

            # Salva em CSV
            boe_data.to_csv("boe_data.csv")

            print("Dados salvos em 'boe_data.csv'")
            print(f"Dimensões: {boe_data.shape}")
            print("UK_POLICY_RATE coletado corretamente!")

        except Exception as e:

            print(
                f"Erro ao coletar "
                f"UK_POLICY_RATE: {e}"
            )

        return boe_data

#-----------------------------------------------------------------------------

    def get_canada_policy_rate(self):
        print("Coletando BOC Target Rate...")

        boc_data = pd.DataFrame()

        try:

            # Série V39079 - Bank of Canada Target Rate
            ticker = self.official_series["CANADA_POLICY_RATE"]

            url = (
                "https://www.bankofcanada.ca/valet/"
                f"observations/{ticker}/json"
            )

            response = requests.get(url)

            response.raise_for_status()

            observations = response.json()["observations"]

            boc_data = pd.DataFrame([
                {
                    "Date": obs["d"],
                    "CANADA_POLICY_RATE": obs[ticker]["v"]
                }
                for obs in observations
            ])

            # Converte tipos
            boc_data["Date"] = pd.to_datetime(
                boc_data["Date"]
            )

            boc_data["CANADA_POLICY_RATE"] = pd.to_numeric(
                boc_data["CANADA_POLICY_RATE"],
                errors="coerce"
            )

            # Define Date como índice
            boc_data = boc_data.set_index("Date")
            boc_data.index.name = "Date"

            # Restringe ao período desejado
            boc_data = boc_data.loc[
                self.START_DATE:self.END_DATE
            ]

            # Salva em CSV
            boc_data.to_csv("canada_policy_rate.csv")

            print("Dados salvos em 'canada_policy_rate.csv'")
            print(f"Dimensões: {boc_data.shape}")
            print("CANADA_POLICY_RATE coletado corretamente!")

        except Exception as e:

            print(
                f"Erro ao coletar "
                f"CANADA_POLICY_RATE: {e}"
            )

        return boc_data

#-----------------------------------------------------------------------------

    def get_selic(self):
        print("Coletando Selic Policy Rate...")

        selic_data = pd.DataFrame()

        try:

            # Série 432 - Selic
            ticker = self.official_series["BRAZIL_SELIC"]

            url = (
                "https://api.bcb.gov.br/dados/serie/"
                f"bcdata.sgs.{ticker}/dados"
            )

            params = {
                "formato": "json",
                "dataInicial": pd.to_datetime(
                    self.START_DATE
                ).strftime("%d/%m/%Y"),
                "dataFinal": pd.to_datetime(
                    self.END_DATE
                ).strftime("%d/%m/%Y")
            }

            response = requests.get(
                url,
                params=params
            )

            response.raise_for_status()

            selic_data = pd.DataFrame(
                response.json()
            )

            # Renomeia as colunas
            selic_data = selic_data.rename(
                columns={
                    "data": "Date",
                    "valor": "BRAZIL_SELIC"
                }
            )

            # Converte tipos
            selic_data["Date"] = pd.to_datetime(
                selic_data["Date"],
                dayfirst=True
            )

            selic_data["BRAZIL_SELIC"] = pd.to_numeric(
                selic_data["BRAZIL_SELIC"],
                errors="coerce"
            )

            # Define Date como índice
            selic_data = selic_data.set_index("Date")
            selic_data.index.name = "Date"

            # Salva em CSV
            selic_data.to_csv("selic_data.csv")

            print("Dados salvos em 'selic_data.csv'")
            print(f"Dimensões: {selic_data.shape}")
            print("BRAZIL_SELIC coletado corretamente!")

        except Exception as e:

            print(
                f"Erro ao coletar "
                f"BRAZIL_SELIC: {e}"
            )

        return selic_data

#-----------------------------------------------------------------------------

    def get_canada_cpi(self):
        print("Coletando Canada CPI...")

        cpi_data = pd.DataFrame()

        try:

            # Tabela 18-10-0004-01
            table_id = self.official_series["CANADA_CPI"]

            url = (
                "https://www150.statcan.gc.ca/"
                "t1/wds/rest/"
                f"getFullTableDownloadCSV/"
                f"{table_id}/en"
            )

            response = requests.get(url)

            response.raise_for_status()

            download_info = response.json()

            # URL do arquivo CSV
            csv_url = download_info["object"]

            cpi_data = pd.read_csv(csv_url)

            # Seleciona Canadá
            cpi_data = cpi_data[
                cpi_data["GEO"] == "Canada"
            ]

            # Seleciona todos os itens (CPI total)
            cpi_data = cpi_data[
                cpi_data[
                    "Products and product groups"
                ] == "All-items"
            ]

            # Mantém somente as colunas necessárias
            cpi_data = cpi_data[
                ["REF_DATE", "VALUE"]
            ]

            # Renomeia as colunas
            cpi_data = cpi_data.rename(
                columns={
                    "REF_DATE": "Date",
                    "VALUE": "CANADA_CPI"
                }
            )

            # Converte tipos
            cpi_data["Date"] = pd.to_datetime(
                cpi_data["Date"]
            )

            cpi_data["CANADA_CPI"] = pd.to_numeric(
                cpi_data["CANADA_CPI"],
                errors="coerce"
            )

            # Define Date como índice
            cpi_data = cpi_data.set_index("Date")
            cpi_data.index.name = "Date"

            # Restringe ao período desejado
            cpi_data = cpi_data.loc[
                self.START_DATE:self.END_DATE
            ]

            # Salva em CSV
            cpi_data.to_csv("canada_cpi.csv")

            print("Dados salvos em 'canada_cpi.csv'")
            print(f"Dimensões: {cpi_data.shape}")
            print("CANADA_CPI coletado corretamente!")

        except Exception as e:

            print(
                f"Erro ao coletar "
                f"CANADA_CPI: {e}"
            )

        return cpi_data