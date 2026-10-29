# Agenda e Divisão do Trabalho

## 06/08/26
***Decisão do Grupo***: Decisão do tema do trabalho - Market Analysis Driven by Event Studies (MADES). Previsão de Volatilidade e Rendimento (Yield) de Bitcoin a partir de fontes de dados heterogêneas: Indicadores Macroeconômicos em Cenários de Estresse, Estudos de Eventos e Análise de Sentimento.

A ideia é cruzar o comportamento do Bitcoin com indicadores da economia tradicional,
análise de sentimento e estudos de eventos para encontrar padrões, distorções e correlações.


## 13/08/26
O que foi feito:
- ***Leonardo Demore (dados estruturados):*** Investigação de fontes de dados e quais dados serão levantados; quais técnicas de pre-processing e feature engineering; como podemos ter certeza que a coleta dos dados foi boa;
- ***Julio Cesar (dados não-estruturados):*** Extração de Dados Brutos e não estruturados relacionados com o tema de grandes Datasets (notícias e discursos); 
- ***Victor Botelho (organização e validação):*** Estudo das fontes de dados históricos do mercado financeiro; organização da planilha da matéria e início deste relatório; organização do projeto, definição das tarefas de cada um, validação das conclusões dos integrantes;
- ***Decisões tomadas:*** decidimos qual rumo o projeto vai tomar: modelo classificador de compra e venda; o projeto vai usar escopo global e local (podemos filtrar); professor sugeriu clusterizar e fazer análise intra-cluster.


## 20/08/26
Expectativas do dia: Adicionar mais países a coleta de dados (G8, BRICS, CANADA, RUSSIA, JAPÃO, talvez mais países); pré-processamento dos dados, clusterização e análise estatística; obtenção dos dados não-estruturados e início do processamento dos mesmos.
O que foi feito:
- ***Leonardo Demore:***Adição de novos países para a coleta de dados, definição dos dados de mercado a serem utilizados de cada país, início do script de processamento, obtenção de APIkeys e início da coleta de dados estruturados;
- ***Julio Cesar:***Obtenção, extração e filtragem dos dados não-estruturados (extração de 48 mil linhas de 2020 a 2026). Análise dos temas relevantes desses dados, clusterização semântica dos eventos;
- ***Victor Botelho:***Avaliação, pesquisa e definição das APIs relevantes dos dados de cripto e mercado que fazem sentido para o projeto, verificação dos tickers do FRED e yfinance para quais indicadores do mercado queremos, organização do projeto e atualização do relatório;
- ***Decisões tomadas:***Descartamos coletar os dados da Rússia (por conta das sanções de 2022, a cobertura do FRED e do Yahoo Finance para Rússia ficou incompleta ou descontinuada em vários pontos); Vamos trabalhar o tempo na escala diária (mínimo possível nesses dados); Definição dos principais tickers do FRED.


## 27/08/26
Expectativas do dia: definição dos tickers restantes, coleta de dados estruturados e possível integração dos dados. Finalizar escolha das APIs, pré-processamento dos dados estruturados e não-estruturados.
O que foi feito:
- ***Leonardo Demore:***
Foco em fazer o código de coleta das variáveis (versão inicial finalizada), aplicação de padrões de projeto (uso de arquivos de configuração, definição de classes e métodos), começo do debug do código.
- ***Julio Cesar:***Eventos divididos em variáveis de categoria de organização e tag de assunto, totalizando, com a variável de sentimento, 15 variáveis. Haviam +80 variáveis com esparcidade absurda, esse foi o motivo da divisão em macro categorias. Além disso, foi realizada uma exploração básica, plotando tempo com sentimento e posteriormente, com volume de notícias publicadas.   
- ***Victor Botelho:***
Finalização da pesquisa: definição das variáveis da tabela (quais fontes vamos usar, verificação dos tickers e APIs diversas), ajuda com o código inicial, confecção do relatório e organização do projeto.
- ***Decisões tomadas:***
Nenhuma decisão específica tomada, apenas continuação do projeto

## 03/09/26
Expectativas do dia: debug completo do código e possível integração dos dados / Análise exploratória dos dados 
O que foi feito:
- ***Leonardo Demore:***
Debug completo do código de coleta de dados; início do código de análise exploratória 
- ***Julio Cesar:***
continuação no código de dados não estruturados; clusterização dos dados 
- ***Victor Botelho:***
Feita a apresentação do nosso projeto; ajuda com o debug do código
- ***Decisões tomadas:***
Nenhuma decisão específica tomada, apenas continuação do projeto


## 10/09/26 - SEMANA COM FERIADO


## 17/09/26
Expectativas do dia: Apresentação da Entrega 1 para o professor, análise e coleta de feedbacks e melhorias para o projeto.
O que foi feito:
- ***Leonardo Demore: Apresentação da Entrega 1, explicação dos tickers e formulação do pipeline.***
- ***Julio Cesar: Apresentação da Entrega 1, discussão sobre clusterização e coleta de feedbacks.***
- ***Victor Botelho: Apresentação da Entrega 1, organização interna do projeto e criação dos slides.***
- ***Decisões tomadas: Implementação de um pipeline visual para o projeto e inclusão na apresentação. Adicionar diversos gráficos para a EDA da Entrega 2, com análises das variáveis que contribua para a futura modelagem.***


## 24/09/26 - SEM AULA


## 01/10/26 - SEM AULA


## 08/10/26
Expectativas do dia: Auditar as duas bases antes da integração (vazamento de dados e vieses), levar o pipeline de notícias para script e juntar as duas trilhas numa base única.
O que foi feito:
- ***Leonardo Demore:***
Auditoria da base estruturada: identificamos um vazamento de dados. O FRED data CPI e juros mensais pelo início do mês de referência, então, com o forward fill, o CPI de janeiro aparecia em 01/01, cerca de 45 dias antes de ser divulgado. Implementação da defasagem de publicação por série (`PUBLICATION_LAGS` em `config.py` e `apply_publication_lag` no processamento); correção de dois bugs (colunas lixo `index`/`Unnamed: 0` no upload ao HuggingFace e checagem de duplicatas que olhava a numeração das linhas, e não as datas); função para baixar a base do HuggingFace já corrigida; atualização do `requirements.txt`.
- ***Julio Cesar:***
Pipeline de notícias levado do notebook para script (`nlp_processing.py`). Identificação do viés de composição das fontes (cada veículo tem um tom de base diferente, e a mistura de fontes muda entre os anos) e criação do tom ajustado pela fonte. Revisão da escolha do número de clusters: o Silhouette cresce sem parar até k = 60, então não serve para escolher k; adotamos um critério de estabilidade por bootstrap, que levou a k = 11 (o k = 10 da Entrega 1 era um corte instável). Geração da base diária de notícias (`news_daily.csv`). Notebook: `news_processing.ipynb`.
- ***Victor Botelho:***
Definição do alinhamento temporal das duas trilhas (dia UTC, mesmo fechamento do candle do BTC e dos timestamps do GDELT) e implementação da integração (`integration.py`), gerando a base integrada (3.650 dias × 74 colunas). Atualização do `main.py` para rodar o pipeline completo; organização dos dados do GDELT no repositório (`sources/data/`, fora do Git); início do registro de decisões (`pipeline2.md`) e atualização do relatório.
- ***Decisões tomadas:***
Aplicar a defasagem de publicação em todas as séries macro (CPI dos EUA 45 dias, demais CPIs 55, médias mensais de juros 32-35, séries diárias 1); usar o tom ajustado pela fonte; trocar o critério do k (Silhouette → estabilidade), passando para k = 11; agregar notícias por dia UTC guardando somas e contagens; manter os CSVs fora do Git (decisão do pipeline 1). Justificativas completas em `pipeline2.md`.


## 15/10/26
Expectativas do dia: Análise exploratória da base integrada, testando a hipótese central da trilha não estruturada: o sentimento das notícias antecipa a direção do BTC?
O que foi feito:
- ***Leonardo Demore:***
Implementação do estudo de eventos (`event_study.py`): eventos = choques de tom (z-score em relação aos 90 dias anteriores), modelo de média constante, declustering de 10 dias, CAR com teste t, Wilcoxon e teste placebo (1.000 sorteios). Resultado: o BTC acumula cerca de +4% nos 5 dias ANTES dos choques positivos de tom (placebo p = 0,004) e nada depois. Também testou se picos de volume de notícias antecedem a volatilidade (não antecedem).
- ***Julio Cesar:***
Análise de precedência entre sentimento e preço: correlação defasada (k de -10 a +10) e causalidade de Granger nos dois sentidos. O retorno do BTC antecede o tom (p < 0,001), mas o contrário não é significativo. Análise por cluster (22 testes com correção de Holm): nenhum tema antecipa o preço. Identificou que parte da relação volume de notícias × volatilidade é só o ciclo semanal (fim de semana tem menos notícias e menos volatilidade).
- ***Victor Botelho:***
Validação da base integrada e da correção do vazamento (comparação antes/depois do CPI), montagem do notebook `integrated_eda.ipynb` e consolidação das conclusões; atualização do `pipeline2.md` e deste relatório.
- ***Decisões tomadas:***
Conclusão principal: o sentimento diário do GDELT REAGE ao preço, não o antecipa (três evidências independentes). Decidimos não assumir que "GDELT dá a direção": a hipótese passa a ser testada fora da amostra na modelagem, com uma ablação (modelos com e sem as features de notícias). Usar o estudo de eventos com modelo de média constante (o BTC negocia 7 dias por semana) e teste placebo (os retornos têm caudas pesadas).


## 22/10/26
Expectativas do dia: Modelagem baseline com validação walk-forward: previsão de volatilidade (dados estruturados) e de direção (com e sem notícias), e um backtest que combina as duas.
O que foi feito:
- ***Leonardo Demore:***
Modelos de volatilidade dos próximos 7 dias: persistência, HAR, GARCH(1,1)-t, HAR-X e LightGBM. O HAR tem R² fora da amostra de cerca de 0,28 (positivo nos 6 anos de teste) e é significativamente melhor que o GARCH (Diebold-Mariano, p < 0,001). Volatilidade de mercado melhora pouco (R² 0,295, não significativo); usar todas as features piora muito (sobreajuste).
- ***Julio Cesar:***
Classificadores de direção (regressão logística e LightGBM) com ablação das notícias e intervalo de confiança da AUC por bootstrap em blocos. O melhor modelo tem AUC de cerca de 0,53 (BTC + mercado); só com notícias, cerca de 0,50, e somar as notícias não melhora. Teste do classificador de 3 classes (compra/manter/venda) para τ de 0,1% a 1% e análise de importância das features.
- ***Victor Botelho:***
Engenharia de features e definição dos alvos (`features.py`: 120+ features sem vazamento; τ = 0,30% = custo de ida e volta), esquema de validação walk-forward com embargo (`models.py`), backtest com custos combinando direção e alvo de volatilidade; consolidação dos resultados (`modeling_baseline.ipynb`), atualização do `pipeline2.md` e deste relatório.
- ***Decisões tomadas:***
Validação walk-forward por ano (teste de 2020 a 2025) com embargo de 7 dias; τ = 0,30%; HAR como benchmark de volatilidade e modelos parcimoniosos (sem níveis de juros, que mudam de patamar entre regimes). Resultado: "estruturado → volatilidade" confirmado; "GDELT → direção" não confirmado com notícias diárias. Próximos passos propostos: estudo de eventos com eventos agendados (FOMC, CPI, ETFs), GDELT intradiário e previsão de dias extremos.


## 29/10/26
Expectativas do dia: ---
O que foi feito: --- 
- ***Leonardo Demore: APRESENTAÇÃO***
- ***Julio Cesar: APRESENTAÇÃO***
- ***Victor Botelho: APRESENTAÇÃO***
- ***Decisões tomadas: ---***


## 05/11/26
Expectativas do dia:
O que foi feito:
- ***Leonardo Demore:***
- ***Julio Cesar:***
- ***Victor Botelho:***
- ***Decisões tomadas:***


## 12/11/26
Expectativas do dia:
O que foi feito:
- ***Leonardo Demore:***
- ***Julio Cesar:***
- ***Victor Botelho:***
- ***Decisões tomadas:***


## 19/11/26
Expectativas do dia:
O que foi feito:
- ***Leonardo Demore:***
- ***Julio Cesar:***
- ***Victor Botelho:***
- ***Decisões tomadas:***


## 26/11/26
Expectativas do dia:
O que foi feito:
- ***Leonardo Demore:***
- ***Julio Cesar:***
- ***Victor Botelho:***
- ***Decisões tomadas:***


## 03/12/26
Expectativas do dia:
O que foi feito:
- ***Leonardo Demore:***
- ***Julio Cesar:***
- ***Victor Botelho:***
- ***Decisões tomadas:***


## 10/12/26
Expectativas do dia:
O que foi feito:
- ***Leonardo Demore:***
- ***Julio Cesar:***
- ***Victor Botelho:***
- ***Decisões tomadas:***
