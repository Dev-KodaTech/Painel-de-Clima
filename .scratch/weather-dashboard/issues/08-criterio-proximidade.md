# Critério de cidades próximas

Type: research
Status: resolved
Blocked by: 03

## Question

Como escolher as 4–5 localidades da tabela "Locations / Temperature", dado que o geocoding da Open-Meteo **não** tem busca por proximidade?

## Answer

**Geocodificar por nome (1 chamada) → escolher vizinhas localmente de `cities15000` → buscar todas as temperaturas numa única chamada multi-coordenada.** Duas requisições HTTP por carga do painel, sem API key.

### Achado central: multi-coordenada funciona

`latitude=52.52,48.85,41.89&longitude=13.41,2.35,12.48` → HTTP 200. Testado ao vivo com 3, 5, 60 e 200 pares; nenhum teto documentado ou observado.

- Resposta é um **array** de objetos normais, **na ordem de entrada** — dá para casar posicionalmente com a lista de cidades.
- Elementos após o primeiro ganham `location_id` (1, 2, …; o 0 é omitido).
- `timezone=auto` resolve **por localização** (verificado: Europe/Zurich, Europe/Paris, Europe/Berlin numa resposta só).
- Contagens diferentes entre lat e lon erram limpo: `"Parameter 'latitude' and 'longitude' must have the same number of elements"`.

**Peso no rate limit**: a regra de >10 variáveis / >2 semanas é expressa **por localização**. Uma requisição curta com poucas variáveis pesa 1 independentemente de quantas coordenadas carregue. **O painel de 6 cidades custa 1 chamada, não 6.**

### Caminhos mortos (ambos definitivos)

- **Reverse geocoding não existe.** `/v1/search?latitude=..&longitude=..` → erro, `name` é obrigatório. `/v1/reverse` → 404. Nenhum parâmetro de lat/long na documentação. (Existe `/v1/get?id=<geonameId>`, direção inversa, não ajuda.) **Impacta o ticket 13**: geolocation precisa de reverse local.
- **Busca por região não existe.** `name=California` → apenas lugares *chamados* California (California, Missouri, pop 4.396; Califon, NJ). Nunca Los Angeles. `name=Bavaria` → Bavaria, Veneto IT; nenhuma cidade alemã. Não há parâmetro `admin1`; passá-lo é silenciosamente ignorado. Funcionam `countryCode=DE` e a sintaxe `name=Munich,Bavaria`, mas ambos exigem saber um nome — **não dá para enumerar uma região**.

### Dataset: `cities15000` cru

3,2 MB zipado / 8,0 MB em disco / 34.136 linhas, TSV, CC-BY 4.0, de `download.geonames.org/export/dump/`. Colunas úteis (índices 0-based, **verificados no arquivo real de 19 campos** — ver [ticket 13](13-geolocation.md)): `[1]`=nome, `[4]`=lat, `[5]`=lon, `[6]`=feature_class (`P`), **`[7]`=feature_code (`PPL*`)**, `[8]`=country_code, `[10]`=admin1, `[14]`=population, `[17]`=timezone.

Pacotes descartados por peso: `geonamescache` (MIT, mas **179 MB** instalado — embute cities500/1000/5000/15000 como JSON), `reverse_geocoder` (LGPL, puxa numpy 38 MB + scipy 102 MB, e não traz população para ranquear). `geopy` não tem dataset embutido; serve só para `geopy.distance`.

### Algoritmo de seleção

Os critérios ingênuos **foram testados e falharam**:
- "maior cidade em 150 km, expandindo" → Reykjavik para Londres/Paris/Berlim; Honolulu para cinco megalópoles chinesas a 8.000+ km.
- "pontuar por população/distância" → subúrbios: Berlim → Heiligensee, Friedrichshagen, Teltow.

O que funcionou em todos os casos de borda:
1. filtrar `feature_code` que começa com `PPL`
2. excluir o que está a menos de ~15 km (a própria cidade)
3. caminhar anéis de raio crescente: 100 / 250 / 600 / 1500 / 5000 / 25000 km
4. em cada anel, pegar as de maior população
5. exigir separação mínima de ~25 km entre as escolhidas (evita subúrbios do mesmo metrô)

40–55 ms sobre 34k linhas com haversine simples; nenhum índice espacial é necessário nesta escala.

**Resultados testados**: Berlim → Potsdam 27 km, Oranienburg 28, Eberswalde 45, Brandenburg 59, Frankfurt (Oder) 80. Basileia (tri-fronteira) → Mulhouse FR 29, Freiburg DE 52, Berna CH 69, Zürich CH 75 — **mistura três países sem caso especial**, porque nada no algoritmo olha país. Reykjavik (isolada) → Reykjanesbær 35, Akureyri 249, depois Glasgow 1.339 / Dublin 1.497. Papeete → Avarua CK 1.146, Auckland 4.094. Nuuk → Reykjavík ~1.400, depois Nova York, Londres, Moscou.

A escala de anéis é o que trata isolamento: regiões densas nunca saem do anel de 100 km, e só lugares genuinamente remotos caem nos largos. Cidade isolada e fronteira nacional saem resolvidas pela estrutura, não por exceções.

### Decisões que isto força

- **Mostrar a distância na tabela.** Para Papeete, "Auckland — 4.094 km" é honesto; apresentá-la sem rótulo como "cidade próxima" engana.
- **`cities15000` corta em 15 mil habitantes**, então vizinhas menores somem (Windsor CA não aparece para Detroit). Usar `cities5000` (5,4 MB / 69.711 linhas) se isso importar.
- **Atribuição CC-BY 4.0** é exigida tanto pelo GeoNames quanto pelo uso gratuito da Open-Meteo — precisa de um rodapé no painel, que o print não tem.

### Asset

Implementação de referência funcionando, incluindo o teste ponta a ponta que geocodifica Basileia, seleciona 5 vizinhas e puxa temperatura atual + máx/mín diária das 6 numa única requisição: `/private/tmp/claude-501/-Users-kobori-Dev-Mattpocock-app/7d9d6a73-c546-4fa7-acf1-5cf8c836363d/scratchpad/near3.py` (scratchpad — copiar para o projeto se for aproveitar).
