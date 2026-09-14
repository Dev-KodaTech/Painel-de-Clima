# Cache, endpoints e mapeamento WMO

Type: grilling
Status: resolved
Blocked by: 01

## Question

Como o backend se organiza: cache, formato dos endpoints, e onde mora o mapeamento WMO→texto/ícone?

## Answer

**Cache**: em memória, TTL 10 min, chave por coordenada arredondada. Os dados atualizam a cada ~15 min (`interval: 900s`); um `dict` com timestamp basta, sem Redis. Mantém o app dentro do rate limit mesmo com refresh agressivo — relevante porque uma chamada com muitas variáveis conta fracionado a mais de 1.

**Endpoints**: dois.
- `GET /api/weather?city=...` → payload completo dos nove painéis
- `GET /api/cities?q=...` → autocomplete/desambiguação

Separados porque o autocomplete dispara a cada tecla e não pode arrastar o forecast junto.

**Mapeamento WMO**: no **backend**. Devolve `weather_code`, `description` e `icon` já resolvidos. O frontend não conhece a tabela WMO, o que mantém honesta a regra de que todo dado vem do backend.

**A forma exata do payload** de `/api/weather` não foi decidida aqui — virou o ticket [Forma do payload de /api/weather](09-payload.md).
