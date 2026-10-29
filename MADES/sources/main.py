from data_processing.struc_data_processing import DataProcessing
from data_processing.nlp_processing import NewsProcessing
from data_processing.integration import DataIntegration

def collect_data():
    """
    Coleta os dados separadamente. Após executar uma vez, os
    dados ficarão salvos na pasta 'data', separados pela fonte.
    Após unificar e limpar todos os CSV, vamos disponibilizar
    no HuggingFace para download.
    """
    from data_collection.data_collector import DataCollector

    collector = DataCollector()

    # Além de salvar os CSVs em disco, também retornamos ele na memória
    # Não utilizamos essas variáveis na nossa lógica
    fred_data = collector.get_fred_data()
    yf_data = collector.get_yf_data()
    btc_data = collector.get_btc_data()
    uk_data = collector.get_uk_rate()
    selic_data = collector.get_selic()
    canada_rate = collector.get_canada_rate()
    canada_cpi = collector.get_canada_cpi()

def main():
    # ------------------------------------------------------------------
    # Trilha estruturada
    # ------------------------------------------------------------------
    # Faz a coleta dos dados das APIs (rodar apenas 1 vez, exige API keys)
    # collect_data()

    # Instancia o objeto que processa os dados
    processer = DataProcessing()

    # Unifica os dados (já aplica a defasagem de publicação das séries macro)
    #processer.unify_data()

    # Limpa os dados (análise inicial feita no notebook)
    #processer.clean_data()

    # Por fim, envia o dataframe clean para salvar no HuggingFace
    #processer.push_to_huggingface()

    # Sem API keys: baixa a versão do HuggingFace e aplica a defasagem
    processer.load_from_hf_struc(apply_lag=True)

    # Baixa as notícias do GDELT (as duas coletas) para sources/data/
    processer.load_from_hf_nstruc()

    # ------------------------------------------------------------------
    # Trilha não estruturada (usa os CSVs do GDELT baixados acima)
    # ------------------------------------------------------------------
    NewsProcessing().run()

    # ------------------------------------------------------------------
    # Integração das duas trilhas -> data/integrated_dataframe.csv
    # ------------------------------------------------------------------
    DataIntegration().run()

    # A análise e a modelagem estão nos notebooks:
    #   notebooks/news_processing.ipynb, integrated_eda.ipynb, modeling_baseline.ipynb



if __name__ == "__main__":
    main()
