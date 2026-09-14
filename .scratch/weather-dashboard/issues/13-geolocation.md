# Geolocation do navegador

Type: grilling
Status: resolved
Blocked by: 09

## Question

Como o frontend sugere a cidade a partir da localização do navegador?

## Answer

### Reverse geocoding é local, sem custo novo

O [ticket 08](08-criterio-proximidade.md) estabeleceu que a Open-Meteo **não tem reverse geocoding** (`/v1/reverse` → 404; `/v1/search` exige `name`). Mas o `cities15000` já estará carregado para a tabela de cidades próximas, e a mesma busca haversine dá a cidade mais próxima de uma coordenada. **Nenhum download, dependência ou chamada de API a mais.**

### Raio máximo: 50 km

Medido contra o dataset real em 12 coordenadas de densidade oposta:

| Coordenada | Cidade mais próxima | Distância |
|---|---|---|
| Centro de Berlim | Mitte, DE | 0,0 km |
| Centro de Tóquio | Tokyo, JP | 0,1 km |
| Centro de SP | Sé, BR | 0,3 km |
| Interior de MG | Serro, BR | 0,5 km |
| Subúrbio de Londres | Hounslow, GB | 2,2 km |
| Alasca interior | Fairbanks, US | 4,3 km |
| Amazônia profunda | Coari, BR | 95,7 km |
| Atacama | Antofagasta, CL | 149,9 km |
| Interior da Austrália | Alice Springs, AU | 341,6 km |
| Saara central | Murzuk, LY | 377,9 km |
| Sibéria central | Aykhal, RU | 519,4 km |
| Meio do Pacífico | Papeete, PF | 1.043,8 km |

**Há um corte natural e nenhum meio-termo**: toda área povoada acerta abaixo de 5 km, e o caso seguinte já salta para 95 km. Ou o usuário está numa cidade, ou está longe de qualquer uma. 50 km é folgado para o primeiro grupo e exclui todo o segundo — o limiar exato não é sensível, qualquer valor entre 10 e 90 km produz o mesmo resultado nestes 12 casos.

Acima de 50 km, **não sugerir nada**: cair no estado inicial normal, com o campo de busca vazio. Sugerir "Alice Springs" a quem está a 341 km dela seria pior que não sugerir.

### Fluxo

1. **Atrás de um botão**, nunca no load. Pedido automático de permissão no primeiro acesso é negado por reflexo, e a negação é lembrada pelo browser — queima a única chance. Um ícone de alvo ao lado do campo de busca.
2. Obtida a coordenada, o frontend chama `GET /api/cities?lat=&lon=` (novo modo do endpoint existente, decidido abaixo).
3. O backend devolve a cidade mais próxima **ou vazio** se passar de 50 km.
4. O frontend **preenche o campo de busca e carrega o painel direto.** O usuário pediu explicitamente ao clicar no botão; exigir uma segunda confirmação é fricção sem propósito. O nome fica visível no campo, então corrigir é trivial.

### Endpoint: modo novo em `/api/cities`, não rota nova

`GET /api/cities?lat=<float>&lon=<float>` devolve o mesmo formato de candidata que `?q=`, com no máximo um item. Motivo: é a mesma operação (resolver algo em candidata de cidade) sobre o mesmo dataset, e o frontend reaproveita o tipo. `q` e `lat`/`lon` são mutuamente exclusivos; enviar ambos ou nenhum é `400`.

`/api/weather` **não muda** — continua recebendo cidade, conforme o [ticket 09](09-payload.md). O fluxo resolve a coordenada em cidade primeiro, o que mantém o painel com um caminho de dados só.

### Fallbacks

| Situação | Comportamento |
|---|---|
| Permissão negada | Estado inicial normal, sem mensagem de erro — foi escolha do usuário |
| `navigator.geolocation` ausente | Botão não é renderizado |
| Contexto não-HTTPS | Idem: a API exige secure context e `localhost` conta como seguro, então dev funciona |
| Timeout (usar 10 s) | Aviso discreto: "Não foi possível obter sua localização" |
| Mais de 50 km da cidade mais próxima | Estado inicial normal, sem sugestão |

### Correção ao ticket 08

A resolução do [ticket 08](08-criterio-proximidade.md) lista as colunas do `cities15000` com índice de um a menos. Verificado no arquivo real (19 campos): `[1]`=nome, `[4]`=lat, `[5]`=lon, **`[6]`=feature_class (`P`)**, **`[7]`=feature_code (`PPL*`)**, `[8]`=country_code, `[10]`=admin1, `[14]`=population, `[17]`=timezone. Filtrar por `[6]` retorna **zero** cidades — erro que custa uma sessão de depuração se passar para o spec.
