# 23: Precipitação e condições previstas

**What to build:** a pessoa vê quanto vai chover em cada um dos sete dias, comparado visualmente em barras, e é avisada de condições severas previstas — tempestade, vento forte ou chuva intensa — com o dia e a intensidade, deixando claro que são derivadas da previsão e não alertas oficiais. Numa semana tranquila, vê que não há nada severo em vez de um painel vazio.

**Blocked by:** 22

**Status:** ready-for-agent

Referência: [spec](../spec.md), seção "Derivação das condições severas".

- [ ] Painel de barras de precipitação para os 7 dias, lendo o bloco `daily` já existente
- [ ] Bloco `alerts` no payload, com `kind`, `date`, `label`, `icon`, `detail` e `also_days`
- [ ] Três gatilhos: `weather_code` ∈ {95,96,99}; `wind_gusts_10m_max` ≥ 60 km/h; `precipitation_sum` ≥ 20 mm
- [ ] **Dedup por categoria**: no máximo 1 card por tipo, representando o pior dia, com "(+N dias)" quando há repetição
- [ ] No máximo 2 cards exibidos, ordenados por data; um nível de severidade só
- [ ] Estado vazio explícito ("sem condições severas"), mantendo o tamanho do painel
- [ ] Painel **não** se chama "alertas"; cada card indica que é derivado da previsão
- [ ] Card mostra categoria, data e valor da métrica — **não** a temperatura que o design de referência exibe
- [ ] Teste: Wellington produz **1** card de vento, não 5 (regressão do dedup)
- [ ] Teste: Cairo e Singapura produzem lista vazia
- [ ] Teste: Miami produz 2 cards distintos (chuva e tempestade)
- [ ] Teste de fronteira: 59,9 vs 60,0 km/h; 19,9 vs 20,0 mm

Fixtures de 6 cidades contrastantes já gravadas em `../probe-alertas.json`.
