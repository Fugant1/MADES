SSC0957 - Prática em Ciência de Dados II
2026 - Professor Alexandre Delbem

Alunos:
VICTOR SILVA BOTELHO - 15645421  
LEONARDO DORO DEMORE - 15674786  
JULIO CESAR A. A. FUGANTI - 15638592

Tema do Trabalho:
MADES - Market Analysis Driven by Event Studies

Previsão de Volatilidade e Rendimento (Yield) de Bitcoin a partir de Indicadores Macroeconômicos em Cenários de Estresse, Estudos de Eventos e Análise de Sentimento.

A ideia é cruzar o comportamento do Bitcoin com indicadores da economia tradicional, análise de sentimento e estudos de eventos para encontrar padrões, distorções e correlações.
- Múltiplas fontes de dados heterogêneas: APIs de exchanges para volume e preços de fechamento, dados de protocolos on-chain para taxas de recompensa (yield), e fontes governamentais (como o Banco Central) para taxas de juros fiduciárias e inflação.
- Muitas variáveis e critérios: Preço, volume de transações em 24h, APY (Annual Percentage Yield), taxa Selic/Fed Funds rate, e índices de volatilidade (VIX).
- Resolução espaço-temporal distintas: Nosso grande desafio técnico. Dados macroeconômicos costumam ser divulgados mensalmente ou a cada 45 dias, enquanto dados de mercado rodam a cada minuto ou hora. Precisamos tratar essas frequências distintas.
- Qualidade, quantidade e erros grosseiros: Vamos precisar lidar com flash crashes (quedas abruptas de preço por erro de liquidez), falhas de API ou lacunas de dados em dias de manutenção de redes.
- Análise do comportamento Principal: Avaliar a tendência geral de correlação entre o aperto monetário tradicional e a fuga de capital (ou busca por yields alternativos) nos ativos digitais. É possível aplicar análises de variância (ANOVA) e estatística inferencial para validar se diferentes regimes econômicos alteram significativamente os rendimentos.
- Modelagem de casos especiais (Extremos): Usar arquiteturas neurais, como Restricted Boltzmann Machines (RBM) ou Redes BAM, para tentar reconhecer os "padrões extremos" que antecedem choques de liquidez ou picos anômalos de rentabilidade no mercado.