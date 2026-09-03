import pandas as pd
import yfinance as yf
from fredapi import Fred
from pathlib import Path
from io import StringIO, BytesIO
from zipfile import ZipFile
import requests
import warnings
import os
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

        # Define o path dos CSVs
        script_dir = Path(__file__).parent.resolve()
        self.data_dir = script_dir.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

#-----------------------------------------------------------------------------

    def get_fred_data(self):
        """ 
        Coleta as séries configuradas no FRED,
        converte para frequência diária e salva em CSV
        """
        print("Coletando dados do FRED...")
        
        # Dicionário temporário para armazenar as séries
        series_dict = {} 

        for col_name, ticker in self.fred_tickers.items():
            try:
                series = self.fred.get_series(
                    ticker,
                    observation_start=self.START_DATE,
                    observation_end=self.END_DATE
                )
                series_dict[col_name] = series
                print(f"{col_name} ({ticker}) coletado corretamente!")

            except Exception as e:
                print(f"Erro ao coletar {col_name} ({ticker}): {e}")

        # Verifica se o dicionário não está vazio
        if series_dict:
            # pd.concat alinha perfeitamente todos os índices de datas
            df_fred = pd.concat(series_dict, axis=1)
            
            df_fred.index = pd.to_datetime(df_fred.index)
            df_fred.index.name = "Date"

            # Converte para frequência diária e faz forward fill
            df_fred = df_fred.resample("D").ffill()

            # Salva em CSV
            fred_output = self.data_dir / "fred_data.csv"
            df_fred.to_csv(fred_output)
            print(f"\nDados do FRED salvos em {fred_output}.")
            print(f"Dimensões: {df_fred.shape}")
            
            return df_fred
        else:
            print("\nNenhum dado foi coletado do FRED.")
            return pd.DataFrame()

#-----------------------------------------------------------------------------

    def get_yf_data(self):
        """
        Coleta dados de mercado do Yahoo Finance (Preço de Fechamento).
        """
        print("Coletando dados de mercado do Yahoo Finance...")
        df_yf = pd.DataFrame()

        # Pega todos os tickers, exceto o Bitcoin
        market_tickers = {
            name: ticker
            for name, ticker in self.yfinance_tickers.items()
            if name != "BITCOIN"
        }

        if not market_tickers:
            print("Nenhum ticker de mercado configurado.")
            return df_yf

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
                # Trata a estrutura do yf.download dependendo se há 1 ou mais tickers
                if isinstance(data.columns, pd.MultiIndex):
                    if ticker in data["Close"].columns:
                        df_yf[col_name] = data["Close"][ticker]
                        print(f"{col_name} ({ticker}) coletado corretamente!")
                else:
                    df_yf[col_name] = data["Close"]
                    print(f"{col_name} ({ticker}) coletado corretamente!")
            except Exception as e:
                print(f"Erro ao processar {ticker}: {e}")

        if not df_yf.empty:
            df_yf.index = pd.to_datetime(df_yf.index)
            df_yf.index.name = "Date"
            
            if df_yf.index.tz is not None:
                df_yf.index = df_yf.index.tz_localize(None)

            # Salva em CSV
            yf_output = self.data_dir / "yfinance_data.csv"
            df_yf.to_csv(yf_output)
            print(f"\nDados salvos em '{yf_output}'")
            print(f"Dimensões: {df_yf.shape}")

        return df_yf

#-----------------------------------------------------------------------------

    def get_btc_data(self):
        """
        Coleta os dados completos de OHLCV do Bitcoin.
        """
        print("\nColetando dados do Bitcoin...")
        df_btc = pd.DataFrame()
        
        btc_ticker = self.yfinance_tickers.get("BITCOIN")
        if not btc_ticker:
            print("Ticker do Bitcoin não encontrado nas configurações.")
            return df_btc

        try:
            btc_data = yf.download(
                btc_ticker,
                start=self.START_DATE,
                end=self.END_DATE,
                auto_adjust=False,
                progress=False
            )

            df_btc["BTC_Open"] = btc_data["Open"]
            df_btc["BTC_High"] = btc_data["High"]
            df_btc["BTC_Low"] = btc_data["Low"]
            df_btc["BTC_Close"] = btc_data["Close"]
            df_btc["BTC_Volume"] = btc_data["Volume"]

            print(f"Bitcoin ({btc_ticker}) coletado corretamente!")

        except Exception as e:
            print(f"Erro ao coletar Bitcoin: {e}")
            return df_btc

        if not df_btc.empty:
            df_btc.index = pd.to_datetime(df_btc.index)
            df_btc.index.name = "Date"
            
            if df_btc.index.tz is not None:
                df_btc.index = df_btc.index.tz_localize(None)

            # Salva no diretório padrão configurado
            btc_output = self.data_dir / "btc_data.csv"
            df_btc.to_csv(btc_output)
            print(f"\nDados salvos em '{btc_output}'")
            print(f"Dimensões: {df_btc.shape}")

        return df_btc

#-----------------------------------------------------------------------------

    def get_uk_rate(self):
        print("Coletando BOE Official Rate...")
        boe_data = pd.DataFrame()

        try:
            # Formata as datas para o padrão do Bank of England (DD/MMM/YYYY)
            start_boe = pd.to_datetime(self.START_DATE).strftime('%d/%b/%Y')
            end_boe = pd.to_datetime(self.END_DATE).strftime('%d/%b/%Y')

            url = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"

            params = {
                "csv.x": "yes",
                "Datefrom": start_boe,
                "Dateto": end_boe,
                "SeriesCodes": self.official_series["UK_POLICY_RATE"],
                "CSVF": "TN",
                "UsingCodes": "Y",
                "VPD": "Y",
                "VFD": "N"
            }

            # Define o User-Agent imitando o Google Chrome
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # Envia a requisição com os headers incluídos
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            # O CSV do Bank of England possui algumas linhas de metadados.
            lines = response.text.splitlines()

            # Localiza a linha do cabeçalho
            header_index = next(
                i for i, line in enumerate(lines) if "DATE" in line.upper()
            )

            boe_data = pd.read_csv(StringIO("\n".join(lines[header_index:])))

            # Renomeia as colunas
            boe_data.columns = ["Date", "UK_POLICY_RATE"]

            # Converte tipos
            boe_data["Date"] = pd.to_datetime(boe_data["Date"])
            boe_data["UK_POLICY_RATE"] = pd.to_numeric(boe_data["UK_POLICY_RATE"], errors="coerce")

            # Define Date como índice
            boe_data = boe_data.set_index("Date")
            boe_data.index.name = "Date"

            # Preenche finais de semana e feriados com forward fill
            boe_data = boe_data.resample("D").ffill()

            # Salva em CSV
            uk_rate_output = self.data_dir / "uk_rate_data.csv"
            boe_data.to_csv(uk_rate_output)

            print(f"Dados salvos em '{uk_rate_output}'")
            print(f"Dimensões: {boe_data.shape}")
            print("UK_POLICY_RATE coletado corretamente!")

        except StopIteration:
            print("Erro: Não foi possível encontrar a coluna 'DATE' no CSV retornado.")
        except Exception as e:
            print(f"Erro ao coletar UK_POLICY_RATE: {e}")

        return boe_data

#-----------------------------------------------------------------------------

    def get_selic(self):
        print("Coletando Selic Policy Rate...")
        selic_data = pd.DataFrame()

        try:
            # Garanta que o ticker para a Selic diária seja "11" no seu dicionário.
            # Se você usa a Selic Meta (fixada pelo Copom), o ticker é "432".
            ticker = self.official_series["BRAZIL_SELIC"] 

            # A URL do SGS aceita os parâmetros de data formatados
            start_br = pd.to_datetime(self.START_DATE).strftime("%d/%m/%Y")
            end_br = pd.to_datetime(self.END_DATE).strftime("%d/%m/%Y")

            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{ticker}/dados?formato=json&dataInicial={start_br}&dataFinal={end_br}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # Remova o params=params, pois já incluímos tudo na URL
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            selic_data = pd.DataFrame(response.json())

            if not selic_data.empty:
                # Renomeia as colunas
                selic_data = selic_data.rename(
                    columns={"data": "Date", "valor": "BRAZIL_SELIC"}
                )

                # Converte tipos (Avisando o Pandas que o dia vem antes do mês)
                selic_data["Date"] = pd.to_datetime(selic_data["Date"], dayfirst=True)
                selic_data["BRAZIL_SELIC"] = pd.to_numeric(selic_data["BRAZIL_SELIC"], errors="coerce")

                # Define Date como índice
                selic_data = selic_data.set_index("Date")
                selic_data.index.name = "Date"

                # Preenche finais de semana e feriados com forward fill
                selic_data = selic_data.resample("D").ffill()

                # Salva em CSV 
                selic_output = self.data_dir / "selic_data.csv"
                selic_data.to_csv(selic_output)

                print(f"Dados salvos em '{selic_output}'")
                print(f"Dimensões: {selic_data.shape}")
                print("BRAZIL_SELIC coletado corretamente!")
            else:
                print("Nenhum dado retornado pela API do Banco Central.")

        except Exception as e:
            print(f"Erro ao coletar BRAZIL_SELIC: {e}")

        return selic_data

#-----------------------------------------------------------------------------

    def get_canada_rate(self):
        print("Coletando BOC Target Rate...")
        boc_data = pd.DataFrame()

        try:
            # Série V39079 - Bank of Canada Target Rate
            ticker = self.official_series["CANADA_POLICY_RATE"]

            url = f"https://www.bankofcanada.ca/valet/observations/{ticker}/json"

            # Passando as datas direto para a API deixar o download mais leve
            params = {
                "start_date": self.START_DATE,
                "end_date": self.END_DATE
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            observations = response.json().get("observations", [])

            # Usando .get() para evitar KeyError caso falte algum dado em dias específicos
            boc_data = pd.DataFrame([
                {
                    "Date": obs.get("d"),
                    "CANADA_POLICY_RATE": obs.get(ticker, {}).get("v")
                }
                for obs in observations
            ])

            if not boc_data.empty:
                # Converte tipos
                boc_data["Date"] = pd.to_datetime(boc_data["Date"])
                boc_data["CANADA_POLICY_RATE"] = pd.to_numeric(
                    boc_data["CANADA_POLICY_RATE"], errors="coerce"
                )

                # Define Date como índice
                boc_data = boc_data.set_index("Date")
                boc_data.index.name = "Date"

                # Preenche finais de semana e feriados
                boc_data = boc_data.resample("D").ffill()

                # Salva em CSV
                canada_rate_output = self.data_dir / "canada_rate.csv"
                boc_data.to_csv(canada_rate_output)

                print(f"Dados salvos em '{canada_rate_output}'")
                print(f"Dimensões: {boc_data.shape}")
                print("CANADA_POLICY_RATE coletado corretamente!")
            else:
                print("Nenhum dado retornado pela API do Bank of Canada.")

        except Exception as e:
            print(f"Erro ao coletar CANADA_POLICY_RATE: {e}")

        return boc_data

#-----------------------------------------------------------------------------

    def get_canada_cpi(self):
        print("Coletando Canada CPI...")
        cpi_data = pd.DataFrame()

        try:
            # Captura a string original (ex: "18-10-0004-01")
            raw_id = str(self.official_series["CANADA_CPI"])
            
            # Remove hifens e pega apenas os primeiros 8 dígitos (ex: "18100004")
            table_id = raw_id.replace("-", "")[:8]

            url = f"https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/{table_id}/en"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            download_info = response.json()
            csv_url = download_info.get("object")

            if not csv_url:
                print("URL de download não encontrada na resposta da API.")
                return cpi_data

            # 1. Baixa o arquivo ZIP
            zip_response = requests.get(csv_url, headers=headers)
            zip_response.raise_for_status()

            # 2. Abre o ZIP na memória e seleciona o arquivo correto
            with ZipFile(BytesIO(zip_response.content)) as z:
                # O StatCan manda a base e os metadados. Pegamos o que NÃO tem "MetaData" no nome.
                data_filename = [f for f in z.namelist() if "MetaData" not in f][0]
                
                with z.open(data_filename) as f:
                    cpi_data = pd.read_csv(f)

            if not cpi_data.empty:
                # Seleciona Canadá
                cpi_data = cpi_data[cpi_data["GEO"] == "Canada"]

                # Seleciona todos os itens (CPI total)
                cpi_data = cpi_data[cpi_data["Products and product groups"] == "All-items"]

                # Mantém somente as colunas necessárias
                cpi_data = cpi_data[["REF_DATE", "VALUE"]]

                # Renomeia as colunas
                cpi_data = cpi_data.rename(
                    columns={"REF_DATE": "Date", "VALUE": "CANADA_CPI"}
                )

                # Converte tipos
                cpi_data["Date"] = pd.to_datetime(cpi_data["Date"])
                cpi_data["CANADA_CPI"] = pd.to_numeric(cpi_data["CANADA_CPI"], errors="coerce")

                # Define Date como índice
                cpi_data = cpi_data.set_index("Date")
                cpi_data.index.name = "Date"

                # Restringe ao período desejado
                cpi_data = cpi_data.loc[self.START_DATE:self.END_DATE]

                # Preenche os dias do mês com o último valor de CPI divulgado
                cpi_data = cpi_data.resample("D").ffill()

                # Salva em CSV
                canada_cpi_output = self.data_dir / "canada_cpi.csv"
                cpi_data.to_csv(canada_cpi_output)

                print(f"Dados salvos em '{canada_cpi_output}'")
                print(f"Dimensões: {cpi_data.shape}")
                print("CANADA_CPI coletado corretamente!")

        except Exception as e:
            print(f"Erro ao coletar CANADA_CPI: {e}")

        return cpi_data