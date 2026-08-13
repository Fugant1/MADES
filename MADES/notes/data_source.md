# Dicionário de Dados e Fonte de Dados

---

## 1. Tratamento de Dados Base
*   **Problema de Calendário:** Feriados distintos entre os 4 países geram valores nulos (NaNs).
*   **Solução:** Aplicação de **Forward Fill** (`method='ffill'` no Pandas) em todo o DataFrame imediatamente após a coleta bruta, antes de calcular qualquer média ou variação temporal.

---

## 2. Variáveis Brutas (Dataset Base)
Coleta direta via APIs `yfinance` e `fredapi`. 

| Fonte Econômica / Bloco | Categoria | Variável / Ticker | Fonte | Frequência |
| :--- | :--- | :--- | :--- | :--- |
| **EUA** | Juros | Fed Funds Rate (`FEDFUNDS`) | FRED | Mensal/Diária |
| **EUA** | Inflação | US CPI (`CPIAUCSL`) | FRED | Mensal |
| **EUA** | Mercado | DXY (`DX-Y.NYB`) | yfinance | Diária |
| **EUA** | Mercado | Nasdaq-100 (`^NDX`) | yfinance | Diária |
| **EUA** | Mercado | US10Y (`^TNX`) | yfinance | Diária |
| **Europa** | Juros | ECB Main Ref Rate (`ECBMAINREF`) | FRED | Mensal/Diária |
| **Europa** | Inflação | Eurozone CPI (`CP0000EZ19M086NES`)| FRED | Mensal |
| **Europa** | Câmbio | EUR/USD (`EURUSD=X`) | yfinance | Diária |
| **China** | Juros | PBOC Rate (`INTDSRCNM193N`) | FRED | Mensal/Diária |
| **China** | Inflação | China CPI (`CHNCPIALLMINMEI`) | FRED | Mensal |
| **China** | Câmbio | USD/CNY (`CNY=X`) | yfinance | Diária |
| **Índia** | Juros | RBI Repo Rate (`INDIR3TIB01STM`) | FRED | Mensal/Diária |
| **Índia** | Inflação | India CPI (`INDCPIALLMINMEI`) | FRED | Mensal |
| **Índia** | Mercado | NIFTY 50 (`^NSEI`) | yfinance | Diária |
| **Alvo** | Cripto | Bitcoin (`BTC-USD`) (OHLCV) | yfinance | Diária |

---

## 3. Feature Engineering 
Para capturar a inércia do mercado, as variáveis brutas acima passarão pelas seguintes transformações matemáticas:

### A. Atrasos Temporais (Lags)
*   Deslocamento para o passado para que o modelo entenda a tendência.
*   **Configuração:** $T-1$, $T-2$ e $T-3$ (dias anteriores) usando `.shift()` para variáveis de mercado diárias.

### B. Deltas (Variações e Retornos)
*   Transformação de valores absolutos em velocidade.
*   **Fórmula Base de Retorno:**
    $$R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$$
*   **Configuração:** Retorno diário (ativos financeiros) e variação percentual mensal (CPI).

### C. Indicadores Técnicos (Momento e Volatilidade)
*   Aplicação da biblioteca `ta` nas variáveis mais voláteis (Bitcoin, Nasdaq e DXY).
*   **SMA (Média Móvel Simples):** 7 e 14 dias.
*   **RSI (Força Relativa):** 14 dias.
*   **Bollinger Bands:** Média, Superior e Inferior (20 dias).

---

## 4. Definição da Variável Alvo (Target)
O modelo fará a previsão de classes usando o retorno de $T+1$ do Bitcoin, calculado pela fórmula:
$$R_{t+1} = \frac{P_{t+1} - P_t}{P_t}$$

As classes serão definidas com base em um threshold ($\tau$) matemático:
*   **Classe 1 (Compra):** Se $R_{t+1} > \tau$
*   **Classe -1 (Venda):** Se $R_{t+1} < -\tau$
*   **Classe 0 (Manter):** Se $-\tau \le R_{t+1} \le \tau$

Esse threshold será definido primeiramente como a soma das taxas da corretora (fees) + custo de execução da ordem (slippage). Depois disso, vamos testar esse threshold baseline com variações, treinando modelos em cada um deles para selecionar aquele que entregar o melhor desempenho financeiro.

> **⚠️ Alerta de Prevenção de Data Leakage:** Todas as colunas com dados do futuro ($T+1$) serão removidas do dataset de treinamento antes da modelagem.
