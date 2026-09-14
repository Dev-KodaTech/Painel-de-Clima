# 25: Localização pelo navegador

**What to build:** a pessoa clica num botão e o painel carrega a cidade onde ela está, sem precisar digitar. Se negar a permissão, o painel continua usável normalmente pela busca. Se estiver longe de qualquer cidade cadastrada, nada é sugerido, em vez de aparecer uma cidade a centenas de quilômetros.

**Blocked by:** 24

**Status:** resolved

Depende do 24 por reaproveitar o dataset carregado e a busca haversine.

Referência: [spec](../spec.md), seção "Localização pelo navegador".

- [x] `GET /api/cities?lat=&lon=` devolve no máximo uma candidata, no mesmo formato do modo texto
- [x] `q` e `lat`/`lon` são mutuamente exclusivos; ambos ou nenhum devolve `400`
- [x] Raio máximo de **50 km**; acima disso, resposta vazia
- [x] Botão de localização ao lado da busca — permissão pedida **só** ao clicar, nunca no carregamento
- [x] Resolvida a cidade, o painel carrega direto; o nome aparece no campo de busca para correção
- [x] Permissão negada: estado inicial normal, sem mensagem de erro
- [x] `navigator.geolocation` ausente: botão não é renderizado
- [x] Timeout de 10 s com aviso discreto
- [x] `/api/weather` **não muda** — continua recebendo cidade
- [x] Teste: coordenada urbana acerta abaixo de 5 km; coordenada remota devolve vazio
- [x] Teste: parâmetros inválidos devolvem `400`

## Comments

Implementado. Notas do que a implementacao verificou ou mudou:

- **O reverse geocoding mora em `reverso.py`, separado de `vizinhas.py`.** A pergunta e outra: vizinhas seleciona um *conjunto* por relevancia (aneis, populacao, separacao minima), enquanto aqui a resposta e uma so e a distancia decide. Compartilham `distancia_km` e o dataset, nada mais.
- **`CidadeLocal` ganhou `id` e `timezone`** (colunas `[0]` e `[17]`). Sem eles a candidata do modo coordenada nao teria o formato do modo texto, e o frontend trataria dois tipos de candidata. `country` vai vazio e `admin1` nulo porque o dump traz pais e estado so como codigos (`BR`, `16`), nao como nomes exibiveis — nenhum dos dois e novidade para quem consome, ja que a API externa omite `country` para territorios (ticket 24) e `admin1` falta para lugares pequenos.
- **O contexto seguro entrou no teste do botao.** `"geolocation" in navigator` e `true` em HTTP puro, onde toda chamada falha com `POSITION_UNAVAILABLE`: o botao apareceria e so saberia dizer "nao foi possivel", que e o oposto do que a tabela de fallbacks pede para esse caso. `window.isSecureContext` trata `localhost` como seguro, entao o desenvolvimento nao muda.
- Medido nas 12 coordenadas da tabela do ticket 13: as populadas acertam abaixo de 0,5 km e as quatro remotas devolvem vazio.

### Achados da revisao

Aplicados:

- **O centro de Sao Paulo devolvia `Se` (23.832 hab.), nao `Sao Paulo` (12,4 milhoes).** As duas estao a **0,4 km** da coordenada: a distancia pura decidia o empate por ruido de arredondamento, e o cabecalho do painel leria "Se" para quem esta na maior cidade do pais. E a mesma armadilha que `vizinhas` ja documenta para os bairros de Berlim, e que aqui tinha passado despercebida porque a tabela do ticket 13 registra justamente "Centro de SP -> Se, BR" como se fosse o resultado certo. Agora a populacao desempata dentro de 1 km (`EMPATE_KM`). A folga e pequena de proposito: "a maior cidade num raio" e o criterio que o ticket 08 descartou, e a 2 km Hounslow tem de continuar Hounslow em vez de virar Londres, que esta a 17 km. Ha teste para os dois lados.
- **`?q=&lat=..&lon=..` devolvia `422`, nao `400`.** O `min_length=1` do Pydantic roda *antes* do corpo do handler, entao o vazio era rejeitado antes de a exclusao mutua ser avaliada — e o erro real ali e ter mandado os dois modos. O vazio passou a ser tratado no corpo, junto da exclusao.

Descartado:

- A revisao apontou Feature Envy em `cidade_na_coordenada`, que le nove campos de `CidadeLocal`. Fica onde esta: `weather.py` e o modulo de montagem de payload e ja abriga `para_cidade`, que faz a mesma conversao a partir do dicionario da API externa. As duas conversoes sao o par que pertence junto.
- A revisao sugeriu um tipo `Coordenada` para o par `lat`/`lon` que viaja por toda parte. Procede como observacao, mas `vizinhas.selecionar` e `distancia_km` ja usam floats soltos no codigo existente: seria refatoracao do repositorio inteiro, nao deste ticket.
