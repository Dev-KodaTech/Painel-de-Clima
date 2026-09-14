# 23: Precipitação e condições previstas

**What to build:** a pessoa vê quanto vai chover em cada um dos sete dias, comparado visualmente em barras, e é avisada de condições severas previstas — tempestade, vento forte ou chuva intensa — com o dia e a intensidade, deixando claro que são derivadas da previsão e não alertas oficiais. Numa semana tranquila, vê que não há nada severo em vez de um painel vazio.

**Blocked by:** 22

**Status:** resolved

Referência: [spec](../spec.md), seção "Derivação das condições severas".

- [x] Painel de barras de precipitação para os 7 dias, lendo o bloco `daily` já existente
- [x] Bloco `alerts` no payload, com `kind`, `date`, `label`, `icon`, `detail` e `also_days`
- [x] Três gatilhos: `weather_code` ∈ {95,96,99}; `wind_gusts_10m_max` ≥ 60 km/h; `precipitation_sum` ≥ 20 mm
- [x] **Dedup por categoria**: no máximo 1 card por tipo, representando o pior dia, com "(+N dias)" quando há repetição
- [x] No máximo 2 cards exibidos, ordenados por data; um nível de severidade só
- [x] Estado vazio explícito ("sem condições severas"), mantendo o tamanho do painel
- [x] Painel **não** se chama "alertas"; cada card indica que é derivado da previsão
- [x] Card mostra categoria, data e valor da métrica — **não** a temperatura que o design de referência exibe
- [x] Teste: Wellington produz **1** card de vento, não 5 (regressão do dedup)
- [x] Teste: Cairo e Singapura produzem lista vazia
- [x] Teste: Miami produz 2 cards distintos (chuva e tempestade)
- [x] Teste de fronteira: 59,9 vs 60,0 km/h; 19,9 vs 20,0 mm

Fixtures de 6 cidades contrastantes já gravadas em `../probe-alertas.json`.
