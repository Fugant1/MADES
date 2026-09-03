from data_collection.data_collector import DataCollector
from data_processing.struc_data_processing import DataProcessing

def collect_data():
    """
    Coleta os dados separadamente. Após executar uma vez, os 
    dados ficarão salvos na pasta 'data', separados pela fonte.
    Após unificar e limpar todos os CSV, vamos disponibilizar
    no HuggingFace para download. 
    """

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
    # Faz a coleta dos dados das APIs (rodar apenas 1 vez)
    # collect_data()

    # Instancia o objeto que processa os dados
    processer = DataProcessing()

    # Unifica os dados 
    #processer.unify_data()

    # Limpa os dados (análise inicial feita no notebook)
    #processer.clean_data()

    # Por fim, envia o dataframe clean para salvar no HuggingFace
    #processer.push_to_huggingface()



if __name__ == "__main__":
    main()