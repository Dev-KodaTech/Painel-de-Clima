# Forma do payload de /api/weather

Type: grilling
Status: resolved
Blocked by: 06, 07, 08

## Question

Qual a estrutura JSON exata que `/api/weather` devolve para alimentar os nove painéis de uma vez?

## Answer

Exemplo completo validado contra dados reais de Berlim: `../payload-exemplo.json` (**4,8 KB indentado, 3,5 KB minificado**).

### Custo: duas chamadas à Open-Meteo, não uma

Medido ao vivo. As variáveis pedidas numa chamada multi-coordenada **valem para todas as coordenadas** — não dá para pedir "tudo para a principal, só temperatura para as vizinhas". Pedir tudo para as 6 traz 168 horas + 7 dias por vizinha, que o painel descarta.

| Estratégia | Bytes | Requisições |
|---|---|---|
| 1 chamada, 6 coords, todas as variáveis | 32.791 | 1 |
| **2 chamadas (principal completa + vizinhas só `current`)** | **7.417** | **2** |

**77% de economia de banda.** Ambas pesam 1 no rate limit (poucas variáveis, 7 dias), logo 2 de 10.000 diárias — irrelevante, e o cache de 10 min corta mais. **Banda vence.**

### Estrutura: um objeto por painel

Chaves de primeiro nível: `location`, `current`, `hourly`, `daily`, `sun`, `alerts`, `nearby`, `units`, `attribution`. Agrupado, não achatado: cada painel do print lê uma chave, e o frontend não precisa saber quais campos vieram de qual bloco da Open-Meteo.

- **`location`**: `name`, `country`, `country_code`, `admin1`, `latitude`, `longitude`, `timezone`, `utc_offset_seconds`.
- **`current`** (card do dia): `observed_at`, `temperature`, `apparent_temperature`, `weather_code`, `description`, `icon`, `is_day`, `high`, `low`. `high`/`low` vêm de `daily[0]` — o print mostra "High : 29° Low : 15" no card do dia, e a API não os traz em `current`.
- **`hourly`** (Temperature Trend): lista de `{time, temperature}`.
- **`daily`** (Forecast Summary + Precipitation Levels): 7 × `{date, weather_code, description, icon, high, low, precipitation_mm}`. **Um só bloco alimenta os dois painéis** — o print mostra os mesmos 7 dias em ambos.
- **`sun`**: `sunrise`, `sunset` do dia corrente.
- **`alerts`**: 0–2 × `{kind, date, label, icon, detail, also_days}` pela regra do [ticket 07](07-regra-alertas.md). `detail` é `"86 km/h"` ou `"27.9 mm"`, `null` para tempestade; `also_days` alimenta o "(+4 dias)".
- **`nearby`**: 5 × `{name, temperature, weather_code, icon, distance_km}`. `distance_km` é exigência do [ticket 08](08-criterio-proximidade.md) — "Auckland 4.094 km" sem rótulo enganaria.
- **`units`**: `{temperature:"°C", precipitation:"mm", wind_speed:"km/h", distance:"km"}`. **Fixas**, não parametrizáveis: o print só mostra °C e unidade configurável multiplica estado no frontend sem o design pedir. Vão no payload mesmo assim para o frontend nunca ter string de unidade hard-coded.
- **`attribution`**: string pronta. CC-BY 4.0 é exigido por Open-Meteo e GeoNames.

### Timestamps

Todos ISO8601 **local à cidade, sem sufixo de offset**, exatamente como a Open-Meteo devolve — mais `timezone` e `utc_offset_seconds` em `location`. O frontend **nunca** deve passá-los por `new Date()` sem tratar: a armadilha do [ticket 01](01-campos-open-meteo.md) desloca o gráfico em horas. Regra: exibir como vieram, tratando-os como horário de parede da cidade.

### Achado: a janela do gráfico horário precisa ser decidida

`hourly` começa às **00:00 do dia corrente**, não "agora". A resposta de teste veio às 02:00 → 22 das 24 horas seriam futuro, mas às 22:00 quase todo o gráfico seria passado. O print mostra 0 AM a 7 PM com um marcador em 9 AM, sugerindo o dia inteiro.

**Decisão: enviar as 24 horas do dia corrente** (00:00–23:00), casando com o print. O frontend marca a hora atual. Alternativas descartadas: janela rolante ±12 h (não bate com o print) e as 168 horas (25 KB para exibir 24).

### Pydantic

Os modelos espelham essa estrutura 1:1 — `Location`, `Current`, `HourlyPoint`, `DailyPoint`, `Sun`, `Alert`, `NearbyCity`, `Units`, `WeatherResponse`. Servem de contrato e geram o schema OpenAPI de graça.
