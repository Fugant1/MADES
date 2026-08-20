import pandas as pd

def load_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return None

if __name__ == "__main__":
    file_path = "data/dados_bitcoin_gdelt_limpos.csv"
    df = load_data(file_path)
    if df is not None:
        print(df.head())

    print(f"{df['Temas'].nunique()}")

    # ... (código anterior) ...
    temas_limpos = df['Temas'].dropna()

    # 1. Quebra a string, remove duplicatas da mesma linha (usando set) e transforma de volta em lista
    tags_unicas_por_noticia = temas_limpos.apply(
        lambda x: list(set([tag.strip() for tag in x.replace(',', ';').split(';') if tag.strip() != '']))
    )

    # 2. Agora sim fazemos o explode (cada tag aparecerá no máximo 1 vez por notícia)
    todas_as_tags_sem_duplicatas = tags_unicas_por_noticia.explode()

    print("\nAs 40 tags presentes no maior número de NOTÍCIAS:")
    print(todas_as_tags_sem_duplicatas.value_counts().head(40))


    organizacoes = df['Organizacoes'].dropna()
    
    # 1. Quebra a string, remove duplicatas da mesma linha (usando set) e transforma de volta em lista
    tags_unicas_por_noticia = organizacoes.apply(
            lambda x: list(set([tag.strip() for tag in x.replace(',', ';').split(';') if tag.strip() != '']))
        )
    
    # 2. Agora sim fazemos o explode (cada tag aparecerá no máximo 1 vez por notícia)
    todas_as_tags_sem_duplicatas = tags_unicas_por_noticia.explode()
    
    print("\nAs 40 organizacoes presentes no maior número de NOTÍCIAS:")
    print(todas_as_tags_sem_duplicatas.value_counts().head(40))