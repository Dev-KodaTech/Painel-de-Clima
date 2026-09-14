# 24: Cidades vizinhas

**What to build:** a pessoa vê a temperatura de quatro a cinco cidades vizinhas numa tabela, cada uma com sua distância, para comparar com a região em volta. Funciona para qualquer cidade do mundo — inclusive isoladas, onde as vizinhas são distantes mas geograficamente sensatas, e de fronteira, onde aparecem cidades de países diferentes.

**Blocked by:** 21

**Status:** resolved

Pode correr **em paralelo** com 22 e 23: depende só da coordenada resolvida pelo 21.

Referência: [spec](../spec.md), seção "Seleção de cidades vizinhas".

- [x] Dump `cities15000` do GeoNames versionado no repositório (3,2 MB comprimido)
- [x] Carregado no **startup** via `lifespan` (~85 ms, ~8,8 MB em memória); busca linear, sem índice espacial
- [x] Colunas lidas pelos índices corretos: `[7]` é `feature_code`, **não** `[6]` (que é `feature_class` e devolve zero cidades)
- [x] Seleção por anéis: filtrar `PPL*`, excluir <15 km, anéis de 100/250/600/1500/5000/25000 km, maior população em cada, separação mínima de ~25 km
- [x] Segunda chamada à API externa, multi-coordenada, pedindo **apenas** `current` para as vizinhas
- [x] Bloco `nearby` no payload com `distance_km` **obrigatório** por item
- [x] Tabela renderizada com nome, distância, ícone e temperatura
- [x] Teste na costura de seleção: Berlim devolve vizinhas reais, não subúrbios do próprio município
- [x] Teste: Basileia mistura três países sem tratamento especial
- [x] Teste: Honolulu **não** devolve megalópole chinesa (regressão do raio fixo)
- [x] Teste: Reykjavik e Papeete degradam para anéis largos em vez de lista vazia
- [x] Teste: dataset carregado tem mais de 30.000 cidades após o filtro (regressão do índice errado)

## Comments

Implementado. Notas do que a implementacao verificou ou mudou:

- **Indice `[7]` confirmado no arquivo real**: `feature_class` (`[6]`) vale `'P'` nas 34.136 linhas, entao filtra-lo por `PPL` devolve zero cidades sem erro algum. `feature_code` (`[7]`) devolve 34.134. O teste de carga (>30.000) trava a regressao.
- **O dump vai comprimido** (3,2 MB) e nao expandido (8,4 MB): descomprimir custa 29 ms dos 214 ms de carga, e poupa 5 MB no repositorio.
- **Quarta armadilha de formato da API externa, nao documentada na spec**: a chave `country` *some* da resposta do geocoding para territorios e regioes especiais — Papeete (PF), Noumea (NC), Hong Kong (HK), Macau (MO), Saint-Denis (RE). O `min_length=1` herdado do ticket 21 devolvia `422` e deixava essas cidades **sem painel algum** — inclusive Papeete, que e o caso de cidade isolada que este ticket existe para servir. `country` passou a aceitar vazio; quem confirma a cidade e `country_code`, sempre presente.
- **A resposta multi-coordenada e assimetrica**: varias coordenadas devolvem lista, uma so devolve objeto. O cliente normaliza para lista sempre; ha teste de contrato para as duas formas.
- **A sigla do pais entrou na tabela** (`28 km · FR`): sem ela, as vizinhas de Basileia se leem como suicas, e a historia 27 pede justamente que a diferenca de pais apareca.
- Medido: carga 214 ms / ~13 MB, selecao ~30 ms, payload 3,4 KB.

### Achados da revisao

Aplicados:

- **Honolulu completava a lista com Los Angeles (4.120 km)** — esgotado o arquipelago, a quinta linha vinha do continente, que e a "megalopole distante" que o criterio de raio fixo produzia. A lista agora termina quando a proxima vizinha esta mais de 7x mais longe que a anterior: Honolulu devolve quatro, e o ticket pede "quatro a cinco". Cidade isolada de verdade nao e punida — as vizinhas de Papeete tem saltos de 1,0x entre si e continuam cinco.
- **O teste de Honolulu proibia um nome, nao um comportamento**: barrar `"Shanghai"` deixava passar Los Angeles. Agora afirma a propriedade (todas no Havai, todas abaixo de 1.000 km).
- `distance_km` passou a `int` no contrato: o valor sempre foi arredondado, e `float` prometia precisao que uma estimativa sobre a esfera nao tem.
- Imports no topo e `BERLIM` proprio em `test_nearby.py`, como os demais modulos de teste fazem; typo `vizenhas`.
- Teste de `/api/cities` para territorio sem `country`, cobrindo o endpoint que vem antes do painel.

Descartado:

- A revisao apontou que `/api/cities` devolveria `500` para Papeete porque `Cidade.country` e obrigatorio. Nao procede: `para_cidade` faz `bruto.get("country", "")` antes do modelo, entao o endpoint devolve `200`. Verificado com a resposta real da API e no browser — Papeete busca, seleciona e renderiza. O teste novo trava isso.
- A revisao chamou os aneis de "cumulativos, nao anelares". E deliberado: uma banda estrita devolveria vazio para quem nao tem vizinha naquela faixa, e "expandir ate encher" e justamente o que trata isolamento.
