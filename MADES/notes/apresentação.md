---
marp: true
theme: gaia
paginate: true
size: 16:9
backgroundColor: #f8fafc
color: #0f172a
---

<style>
section {
  font-family: Arial, sans-serif;
}

h1, h2, h3 {
  color: #0f172a;
}

h1 {
  font-size: 42px;
  margin-bottom: 12px;
}

h2 {
  font-size: 32px;
  color: #1d4ed8;
  margin-bottom: 12px;
}

p, li {
  font-size: 21px;
  line-height: 1.35;
}

ul, ol {
  margin-top: 0.35em;
  margin-bottom: 0.2em;
}

section {
  padding: 22px 48px 18px 48px;
}

.small {
  font-size: 18px;
}

.box {
  background: #eef2ff;
  border-left: 6px solid #3b82f6;
  border-radius: 10px;
  padding: 16px 20px;
  margin-top: 12px;
}
</style>

# MADES
## Market Analysis Driven by Event Studies

### Previsão de volatilidade e rendimento do Bitcoin usando dados macroeconômicos, mercado financeiro e sentimento de notícias

<div class="small">
Victor Silva Botelho • Leonardo Doro Demore • Julio Cesar A. A. Fuganti
</div>

---

# O problema

O Bitcoin é um ativo que combina alta volatilidade, sensibilidade ao risco e influência de eventos externos.

<div class="box">
A pergunta central do projeto é: <br>
<strong>quão relevante é o contexto macroeconômico e o sentimento do mercado para explicar o comportamento do Bitcoin?</strong>
</div>

- juros, inflação e política monetária;
- indicadores tradicionais de mercado;
- câmbio e ativos de risco;
- notícias e eventos globais;
- sentimento e cobertura de mídia.

---

# Nossa proposta

Construir uma base para relacionar o comportamento do Bitcoin com múltiplas fontes de informação.

### Objetivo

Analisar se indicadores macroeconômicos, notícias e eventos influenciam:

- retorno;
- volatilidade;
- tendência de compra/venda.

A análise é global, cobrindo as principais economias do mundo, e também regional, comparando padrões em Europa, Ásia, América e outros blocos relevantes.

---

# Fontes de dados

O projeto organiza dados estruturados de vários mercados e países.

### Principais fontes

- FRED
- Yahoo Finance
- Banco Central do Brasil
- Bank of England
- Bank of Canada
- Statistics Canada

### Variáveis consideradas

- juros: Selic, Fed Funds, BOE, BOC, ECB;
- inflação: CPI e IPCA;
- mercado: Nasdaq, DAX, CAC 40, FTSE, IBOVESPA;
- câmbio: USD/BRL, USD/JPY, USD/CAD, USD/ZAR;
- alvo: Bitcoin em OHLCV diário.

---

# Pipeline de coleta e organização

A coleta está estruturada em módulos com papéis bem definidos.

- `config.py`: dicionários de tickers;
- `data_collector.py`: coleta e exportação das séries;
- `main.py`: execução principal;
- `nlp_extraction.py`: extração de notícias e eventos;
- `nlp_processing.py`: análise inicial de temas e organizações.

Atualmente, estamos na etapa de debug do código de coleta. Quando essa etapa fechar, começaremos com análise exploratória e levantamento de hipóteses.

### Fluxo

1. definir tickers e fontes;
2. coletar séries por API;
3. ajustar datas e frequências;
4. exportar dados em CSV;
5. preparar cruzamento entre bases.

---

# Dados não estruturados e análise de sentimento

Além dos indicadores financeiros, o projeto coleta notícias e discursos relacionados ao Bitcoin.

### O que buscamos

- temas relevantes do mercado;
- entidades e organizações citadas;
- sentimento das notícias;
- eventos que alteram percepção de risco.

A extração usa GDELT e veículos como Reuters, Bloomberg, CoinDesk e Cointelegraph.

A ideia é ligar eventos externos ao comportamento do ativo e identificar mudanças no humor do mercado.

---

# Estratégia de modelagem

A etapa mais central da pesquisa é transformar dados em sinais utilizáveis.

### Feature engineering

- lags temporais: T-1, T-2, T-3;
- variações percentuais (deltas);
- SMA, RSI e Bollinger Bands;
- tratamento de frequência e ausências.

---

### Variável alvo

A previsibilidade é feita sobre o retorno futuro do Bitcoin:

$$R_{t+1} = \frac{P_{t+1} - P_t}{P_t}$$

E nosso modelo será um classificador multi-alvo, considerando estes três estados:

- compra;
- venda;
- manter.



# Status atual e próximos passos

### O que já foi feito

- definição do tema e hipótese;
- seleção de fontes e variáveis;
- estruturação inicial da coleta;
- extração de dados financeiros;

---

- processamento inicial de dados textuais;
- definição da lógica de target.

### O que falta

- concluir o debug da coleta;
- integrar as bases em um dataset único;
- alinhar frequências temporais;
- fazer análise exploratória;
- levantar hipóteses e validar relações;
- treinar modelos e comparar estratégias.

<div class="box">
O projeto ainda está em fase inicial, mas a base conceitual está bem definida.
</div>

---

# Conclusão

O projeto parte da ideia de que o Bitcoin não deve ser analisado apenas por séries históricas de preço.

Ele é tratado como um ativo sensível a:

- política monetária;
- indicadores macroeconômicos;
- sentimento do mercado;

Essa combinação de dados heterogêneos é o eixo central e define a direção do projeto.
