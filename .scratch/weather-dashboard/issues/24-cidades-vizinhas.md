# 24: Cidades vizinhas

**What to build:** a pessoa vê a temperatura de quatro a cinco cidades vizinhas numa tabela, cada uma com sua distância, para comparar com a região em volta. Funciona para qualquer cidade do mundo — inclusive isoladas, onde as vizinhas são distantes mas geograficamente sensatas, e de fronteira, onde aparecem cidades de países diferentes.

**Blocked by:** 21

**Status:** ready-for-agent

Pode correr **em paralelo** com 22 e 23: depende só da coordenada resolvida pelo 21.

Referência: [spec](../spec.md), seção "Seleção de cidades vizinhas".

- [ ] Dump `cities15000` do GeoNames versionado no repositório (3,2 MB comprimido)
- [ ] Carregado no **startup** via `lifespan` (~85 ms, ~8,8 MB em memória); busca linear, sem índice espacial
- [ ] Colunas lidas pelos índices corretos: `[7]` é `feature_code`, **não** `[6]` (que é `feature_class` e devolve zero cidades)
- [ ] Seleção por anéis: filtrar `PPL*`, excluir <15 km, anéis de 100/250/600/1500/5000/25000 km, maior população em cada, separação mínima de ~25 km
- [ ] Segunda chamada à API externa, multi-coordenada, pedindo **apenas** `current` para as vizinhas
- [ ] Bloco `nearby` no payload com `distance_km` **obrigatório** por item
- [ ] Tabela renderizada com nome, distância, ícone e temperatura
- [ ] Teste na costura de seleção: Berlim devolve vizinhas reais, não subúrbios do próprio município
- [ ] Teste: Basileia mistura três países sem tratamento especial
- [ ] Teste: Honolulu **não** devolve megalópole chinesa (regressão do raio fixo)
- [ ] Teste: Reykjavik e Papeete degradam para anéis largos em vez de lista vazia
- [ ] Teste: dataset carregado tem mais de 30.000 cidades após o filtro (regressão do índice errado)
