# 06: O clima de várias coordenadas num só endpoint

**What to build:** o backend já sabe buscar o clima atual de várias coordenadas
numa única chamada à API externa — é assim que as cidades vizinhas do painel são
montadas. Mas essa capacidade está enterrada dentro da montagem do painel, sem
endpoint próprio, e ninguém de fora alcança.

Este ticket a expõe: um endpoint recebe uma lista de coordenadas e devolve
temperatura, código e descrição de cada uma, **numa só chamada externa**. É o que
vai pintar os cartões dos locais salvos: uma requisição para a lista inteira, não
uma por cartão.

O caminho alternativo — chamar o painel completo por local salvo — foi rejeitado
e vale registrar por quê: o payload do painel tem cerca de 3,5 KB e traz previsão
de sete dias, condições previstas e cidades vizinhas que um cartão descarta
inteiras. Oito locais salvos custariam oito requisições e vinte e oito KB para
exibir vinte e quatro campos.

Não depende de conta nem de banco: é um endpoint de leitura como os outros, e
pode ser construído em paralelo com toda a cadeia de autenticação.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Um endpoint recebe várias coordenadas e devolve o clima atual de cada uma
- [ ] A resposta traz temperatura, código do tempo, descrição e ícone por coordenada
- [ ] A resposta preserva a ordem das coordenadas pedidas
- [ ] **Uma** chamada à API externa atende N coordenadas, verificado por contagem de requisições
- [ ] Lista vazia devolve resultado vazio sem chamar a API externa
- [ ] Coordenada fora de faixa é recusada
- [ ] Parâmetro malformado é recusado com mensagem clara
- [ ] O cache existente é reaproveitado, e uma segunda chamada igual não gasta cota
- [ ] A API externa fora do ar devolve o mesmo status que os demais endpoints já devolvem
- [ ] A leitura do parâmetro de coordenadas é função pura, testada diretamente
- [ ] Há limite de quantas coordenadas uma requisição aceita
- [ ] Os testes usam a costura HTTP, com a rede externa simulada
