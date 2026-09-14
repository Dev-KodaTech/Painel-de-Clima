# Campos disponíveis na API Open-Meteo

Type: research
Status: resolved

## Question

Quais campos a Open-Meteo entrega de fato, e quais dos nove painéis do print ela consegue alimentar?

## Answer

Verificado contra respostas ao vivo, não só contra a documentação.

**Alertas: não existem.** Confirmado por três vias — os 14 produtos da Open-Meteo não incluem alertas; `/v1/alerts` e `/v1/warnings` → 404; `current=weather_alerts` → 400. O mantenedor declara não haver plano (discussion #183). Proxies: `weather_code` 95/96/99, `wind_gusts_10m_max`, `cape`.

**Geocoding**: `count` default 10 (1–100). Campos: `latitude`, `longitude`, `name`, `country`, `country_code`, `admin1`–`admin4`, `timezone`, `population`, `elevation`, `postcodes[]`. Desambiguação confirmada: `Springfield&count=10` → MO, IL, MA, OH, TN, KY, GA, CO distintas.
- **Armadilha 1**: resultados são fuzzy ("Palmyra" apareceu numa busca por "Springfield").
- **Armadilha 2**: sem correspondência, a chave `results` **some** em vez de vir vazia → risco de `KeyError`.

**Current**: `temperature_2m`, `weather_code`, `apparent_temperature`, `is_day`, `relative_humidity_2m`, `wind_speed_10m`, `wind_gusts_10m`, etc.

**Hourly**: `temperature_2m`, `precipitation`, `precipitation_probability` + 40 outras. Até 16 dias (384 passos). `start_date`/`end_date` e `past_days` (máx 92) funcionam.

**Daily**: `temperature_2m_max`/`_min`, `weather_code`, `sunrise`, `sunset`, `precipitation_sum`, `precipitation_probability_max`, `uv_index_max`, `wind_gusts_10m_max`. Máx 16 dias, default 7.

**WMO**: códigos 0–99, ~28 emitidos. **A API devolve só o inteiro** — unidade literal `"wmo code"`, nenhum texto. O "Sunny Cloudy" do print é mapeamento nosso. 96/99 são documentados como Europa Central apenas.

**Fuso**: `timezone=auto` funciona. Timestamps em ISO8601 **sem sufixo de offset** (`2026-09-13T18:00`) — são locais da cidade; tratá-los como UTC desloca o gráfico em horas.

**Limites**: 600/min, 5.000/h, 10.000/dia, 300.000/mês, sem key. Requisições com >10 variáveis ou >2 semanas contam fracionado (>1 chamada).

**Cobertura do print**: 8 dos 9 painéis têm dados reais. Só Weather Alerts não tem.
