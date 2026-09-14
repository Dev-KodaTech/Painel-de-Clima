# 25: Localização pelo navegador

**What to build:** a pessoa clica num botão e o painel carrega a cidade onde ela está, sem precisar digitar. Se negar a permissão, o painel continua usável normalmente pela busca. Se estiver longe de qualquer cidade cadastrada, nada é sugerido, em vez de aparecer uma cidade a centenas de quilômetros.

**Blocked by:** 24

**Status:** ready-for-agent

Depende do 24 por reaproveitar o dataset carregado e a busca haversine.

Referência: [spec](../spec.md), seção "Localização pelo navegador".

- [ ] `GET /api/cities?lat=&lon=` devolve no máximo uma candidata, no mesmo formato do modo texto
- [ ] `q` e `lat`/`lon` são mutuamente exclusivos; ambos ou nenhum devolve `400`
- [ ] Raio máximo de **50 km**; acima disso, resposta vazia
- [ ] Botão de localização ao lado da busca — permissão pedida **só** ao clicar, nunca no carregamento
- [ ] Resolvida a cidade, o painel carrega direto; o nome aparece no campo de busca para correção
- [ ] Permissão negada: estado inicial normal, sem mensagem de erro
- [ ] `navigator.geolocation` ausente: botão não é renderizado
- [ ] Timeout de 10 s com aviso discreto
- [ ] `/api/weather` **não muda** — continua recebendo cidade
- [ ] Teste: coordenada urbana acerta abaixo de 5 km; coordenada remota devolve vazio
- [ ] Teste: parâmetros inválidos devolvem `400`
