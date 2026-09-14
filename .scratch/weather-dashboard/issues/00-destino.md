# Destino e escopo do esforço

Type: grilling
Status: resolved

## Question

O pedido diz "Implemente", mas `/wayfinder` planeja. Onde termina este mapa: num spec, no app rodando, ou só na decisão de design?

## Answer

**Spec pronto para implementar.** O nó deste esforço são decisões de escopo, não volume de código; resolvidas elas, o build é mecânico.

Nove decisões fechadas por grilling na sessão de charting:

| # | Decisão | Resultado |
|---|---|---|
| Q1 | Destino | spec pronto para implementar |
| Q2 | Weather Alerts | derivar do forecast |
| Q3 | Mapa regional | tabela de cidades próximas |
| Q4 | Ícones | Meteocons open-source |
| Q5 | Estados extra | entram, menos dark mode |
| Q6 | Geolocation | entra, último ticket |
| Q7 | Cache | memória, TTL 10min, chave por coord arredondada |
| Q8 | Endpoints | `/api/weather` + `/api/cities` |
| Q9 | Mapeamento WMO | no backend |

**Achado que reformulou o escopo**: o diretório estava vazio. Não existe "frontend e backend existente"; o scaffold entra no spec.
