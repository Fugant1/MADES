import pandas as pd
from pathlib import Path
from datasets import Dataset
from huggingface_hub import login
import os
from dotenv import load_dotenv



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

        # Salva o dataset final
        output_file = self.data_dir / "unified_dataframe.csv"
        df_final.to_csv(output_file)
        
        print(f"\nUnificação concluída com sucesso!")
        print(f"Dataset salvo em: '{output_file}'")
        print(f"Dimensões Finais: {df_final.shape}")
        
        return df_final

    def clean_data(self):
        """
        Realiza a limpeza final dos dados verificando  
        duplicatas e removendo valores nulos do início.
        """

        # Lê o df
        dataframe_path = self.data_dir / "unified_dataframe.csv"
        df = pd.read_csv(dataframe_path)

        print("\nIniciando limpeza de dados (Data Cleaning)...")
        df_clean = df.copy()

        # Garante que o índice não tem duplicatas
        if df_clean.index.duplicated().any():
            df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

        # Remove os nulos do início da série (3 linhas)
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

        print(f"\nIniciando upload para o Hugging Face (Repositório: {self.repo_id})...")
        
        try:
            # Faz o login na API
            login(token=self.hf_token)

            # Lê o df
            dataframe_path = self.data_dir / "final_dataframe.csv"
            df = pd.read_csv(dataframe_path)
            
            # Reseta o índice para que a 'Date' vire uma coluna normal no HF
            df_upload = df.copy().reset_index()
            
            # Converte de Pandas para Hugging Face Dataset
            hf_dataset = Dataset.from_pandas(df_upload)
            
            # Envia para o Hub
            hf_dataset.push_to_hub(self.repo_id)
            
            print("Upload concluído com sucesso!")
            print(f"O dataset já está disponível em: https://huggingface.co/datasets/{self.repo_id}")
            
        except Exception as e:
            print(f"Erro ao enviar para o Hugging Face: {e}")