import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
from data_collection.config import PUBLICATION_LAGS



class DataProcessing:
    def __init__(self):
        # Carrega variáveis de ambiente
        load_dotenv()

        # Define o path dos CSVs
        script_dir = Path(__file__).parent.resolve()
        self.data_dir = script_dir.parent / "data"

        # Define as constantes do HuggingFace
        self.repo_id = "leodemore/btc-finance-historical-data"
        self.hf_token = os.getenv("HF_TOKEN")

    def unify_data(self):
        """
        Lê todos os CSVs na pasta 'data' e unifica usando
        as datas do Bitcoin.
        """
        print("\nIniciando a unificação de todas as bases de dados...")

        # Arquivo base
        btc_file = self.data_dir / "btc_data.csv"

        if not btc_file.exists():
            print("Erro: Arquivo btc_data.csv não encontrado!")
            return pd.DataFrame()

        # Carrega o Bitcoin como dataframe principal
        df_final = pd.read_csv(btc_file, index_col="Date", parse_dates=True)
        print(f"Base carregada: btc_data.csv | Dimensões iniciais: {df_final.shape}")

        # Lista dos outros arquivos
        other_files = [
            "fred_data.csv",
            "yfinance_data.csv",
            "uk_rate_data.csv",
            "canada_rate.csv",
            "selic_data.csv",
            "canada_cpi.csv"
        ]

        for file_name in other_files:
            file_path = self.data_dir / file_name
            if file_path.exists():
                print(f"Juntando: {file_name}...")

                # Lê o CSV atual
                df_temp = pd.read_csv(file_path, index_col="Date", parse_dates=True)

                # Faz o Left Join usando o índice de datas do Bitcoin
                df_final = df_final.join(df_temp, how="left")
            else:
                print(f"Aviso: Arquivo '{file_name}' não encontrado na pasta 'data'. Pulando...")

        # Trata os dados nulos gerados pelos mercados fechados usando forward fill
        df_final = df_final.ffill()

        # Desloca cada série pela sua defasagem de publicação (evita vazamento)
        df_final = self.apply_publication_lag(df_final)

        # Salva o dataset final
        output_file = self.data_dir / "unified_dataframe.csv"
        df_final.to_csv(output_file)

        print(f"\nUnificação concluída com sucesso!")
        print(f"Dataset salvo em: '{output_file}'")
        print(f"Dimensões Finais: {df_final.shape}")

        return df_final

    @staticmethod
    def apply_publication_lag(df, lags=PUBLICATION_LAGS):
        """
        Desloca cada série pela defasagem de publicação, para que o valor de
        um dia seja apenas o que já tinha sido divulgado até aquele dia.
        Exige calendário diário contínuo (o do BTC é), então shift(n) = n dias.
        """
        df = df.copy()
        gaps = df.index.to_series().diff().dropna()
        assert (gaps == pd.Timedelta(days=1)).all(), "o calendário precisa ser diário e contínuo"

        for col, lag in lags.items():
            if col in df.columns and lag > 0:
                df[col] = df[col].shift(lag)
        return df

    def clean_data(self):
        """
        Realiza a limpeza final dos dados verificando
        duplicatas e removendo valores nulos do início.
        """

        # Lê o df (com a data como índice, para a checagem de duplicatas valer para as datas)
        dataframe_path = self.data_dir / "unified_dataframe.csv"
        df = pd.read_csv(dataframe_path, index_col="Date", parse_dates=True)

        print("\nIniciando limpeza de dados (Data Cleaning)...")
        df_clean = df.copy()

        # Garante que o índice não tem duplicatas
        if df_clean.index.duplicated().any():
            df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

        # Remove os nulos do início da série (feriado de 2016 e a janela
        # aberta pela defasagem de publicação das séries mensais)
        before = len(df_clean)
        df_clean = df_clean.dropna()
        after = len(df_clean)

        print(f"Linhas iniciais removidas: {before - after}")
        print(f"Limpeza concluída. Dimensões: {df_clean.shape}")

        # Salva em CSV
        path = self.data_dir / "final_dataframe.csv"
        df_clean.to_csv(path)

    def push_to_huggingface(self):
        """
        Converte o DataFrame limpo para um Dataset do Hugging Face e
        faz o upload para o Hub.
        """
        from datasets import Dataset
        from huggingface_hub import login

        print(f"\nIniciando upload para o Hugging Face (Repositório: {self.repo_id})...")

        try:
            # Faz o login na API
            login(token=self.hf_token)

            # Lê o df com a data como índice e a transforma em coluna normal.
            # (Antes o CSV era lido sem index_col, o que criava as colunas
            # lixo 'index' e 'Unnamed: 0' no dataset publicado.)
            dataframe_path = self.data_dir / "final_dataframe.csv"
            df = pd.read_csv(dataframe_path, index_col="Date", parse_dates=True)
            df_upload = df.reset_index()

            # Converte de Pandas para Hugging Face Dataset
            hf_dataset = Dataset.from_pandas(df_upload, preserve_index=False)

            # Envia para o Hub
            hf_dataset.push_to_hub(self.repo_id)

            print("Upload concluído com sucesso!")
            print(f"O dataset já está disponível em: https://huggingface.co/datasets/{self.repo_id}")

        except Exception as e:
            print(f"Erro ao enviar para o Hugging Face: {e}")

    def load_from_huggingface(self, apply_lag=True, save=True):
        """
        Baixa a versão publicada no HuggingFace (para quem não tem as API keys).
        A versão publicada até 17/09 foi gerada SEM a defasagem de publicação,
        então por padrão aplicamos a defasagem aqui.
        """
        url = f"https://huggingface.co/datasets/{self.repo_id}/resolve/main/data/train-00000-of-00001.parquet"
        df = pd.read_parquet(url)
        df = df.drop(columns=["index", "Unnamed: 0"], errors="ignore")
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()

        # O dataset publicado começa em 04/01/2016 sem buracos; garantimos calendário contínuo
        df = df.asfreq("D").ffill()
        if apply_lag:
            df = self.apply_publication_lag(df)

        if save:
            output = self.data_dir / "struc_pit_dataframe.csv"
            df.to_csv(output)
            print(f"Base estruturada (point-in-time) salva em '{output}' | {df.shape}")
        return df
