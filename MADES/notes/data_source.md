# Dicionário de Dados 

## 1. Variáveis Brutas (Dataset Base)
Coleta direta via APIs `yfinance`, `fredapi`, `bank of England`, `bank of Canada`, `banco central do Brasil`, `statistics Canada`


| País/Bloco    | Categoria     | Variável                     | Código / Série         | Fonte dos dados         | Frequência    |
| ------------- | ------------- | ---------------------------- | ---------------------- | ----------------------- | ------------- |
| EUA           | Juros         | Fed Funds Rate               | `FEDFUNDS` / `DFF`     | FRED                    | Mensal/Diária |
| EUA           | Inflação      | US CPI                       | `CPIAUCSL`             | FRED                    | Mensal        |
| EUA           | Câmbio        | DXY                          | `DX-Y.NYB`             | yfinance                | Diária        |
| EUA           | Mercado       | Nasdaq-100                   | `^NDX`                 | yfinance                | Diária        |
| EUA           | Juros/Mercado | US 10-Year Treasury Yield    | `DGS10`                | FRED                    | Diária        |
| Alemanha      | Juros         | ECB Main Ref Rate            | `ECBMRRFR`             | FRED                    | Diária        |
| Alemanha      | Inflação      | Germany CPI                  | `DEUCPIALLMINMEI`      | FRED                    | Mensal        |
| Alemanha      | Mercado       | DAX                          | `^GDAXI`               | yfinance                | Diária        |
| França        | Juros         | ECB Main Ref Rate            | `ECBMRRFR`             | FRED                    | Diária        |
| França        | Inflação      | France CPI                   | `FRACPIALLMINMEI`      | FRED                    | Mensal        |
| França        | Mercado       | CAC 40                       | `^FCHI`                | yfinance                | Diária        |
| Itália        | Juros         | ECB Main Ref Rate            | `ECBMRRFR`             | FRED                    | Diária        |
| Itália        | Inflação      | Italy CPI                    | `ITACPIALLMINMEI`      | FRED                    | Mensal        |
| Itália        | Mercado       | FTSE MIB                     | `FTSEMIB.MI`           | yfinance                | Diária        |
| Reino Unido   | Juros         | BOE Official Rate            | `IUDBEDR`              | Bank of England         | Diária        |
| Reino Unido   | Inflação      | UK CPI                       | `GBRCPIALLMINMEI`      | FRED                    | Mensal        |
| Reino Unido   | Mercado       | FTSE 100                     | `^FTSE`                | yfinance                | Diária        |
| Reino Unido   | Câmbio        | GBP/USD                      | `GBPUSD=X`             | yfinance                | Diária        |
| Canadá        | Juros         | BOC Target Rate              | `V39079`               | Bank of Canada          | Diária        |
| Canadá        | Inflação      | Canada CPI                   | `18-10-0004-01`        | Statistics Canada       | Mensal        |
| Canadá        | Mercado       | S&P/TSX                      | `^GSPTSE`              | yfinance                | Diária        |
| Canadá        | Câmbio        | USD/CAD                      | `USDCAD=X`             | yfinance                | Diária        |
| Japão         | Juros         | Japan 3-Month Interbank Rate | `IR3TIB01JPM156N`      | FRED/OECD               | Mensal        |
| Japão         | Inflação      | Japan CPI                    | `JPNCPIALLMINMEI`      | FRED/OECD               | Mensal        |
| Japão         | Mercado       | Nikkei 225                   | `^N225`                | yfinance                | Diária        |
| Japão         | Câmbio        | USD/JPY                      | `USDJPY=X`             | yfinance                | Diária        |
| China         | Juros         | China 3-Month Interbank Rate | `IR3TIB01CNM156N`      | FRED/OECD               | Mensal        |
| China         | Inflação      | China CPI                    | `CHNCPIALLMINMEI`      | FRED/OECD               | Mensal        |
| China         | Câmbio        | USD/CNY                      | `USDCNY=X`             | yfinance                | Diária        |
| Índia         | Juros         | India Call Money Rate        | `IRSTCI01INM156N`      | FRED/OECD               | Mensal        |
| Índia         | Inflação      | India CPI                    | `CPI: Total for India` | FRED/OECD               | Mensal        |
| Índia         | Mercado       | NIFTY 50                     | `^NSEI`                | yfinance                | Diária        |
| Brasil        | Juros         | Selic Policy Rate            | `432`                  | Banco Central do Brasil | Diária        |
| Brasil        | Inflação      | Brazil CPI / IPCA            | `BRACPIALLMINMEI`      | FRED/OECD               | Mensal        |
| Brasil        | Mercado       | IBOVESPA                     | `^BVSP`                | yfinance                | Diária        |
| Brasil        | Câmbio        | USD/BRL                      | `USDBRL=X`             | yfinance                | Diária        |
| África do Sul | Juros         | South Africa Call Money Rate | `IRSTCI01ZAM156N`      | FRED/OECD               | Mensal        |
| África do Sul | Inflação      | South Africa CPI             | `ZAFCPIALLMINMEI`      | FRED/OECD               | Mensal        |
| África do Sul | Câmbio        | USD/ZAR                      | `USDZAR=X`             | yfinance                | Diária        |
| Alvo          | Cripto        | Bitcoin (OHLCV)              | `BTC-USD`              | yfinance                | Diária        |


---

## 2. Data Cleaning


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
