# 04: O mapa da região

**What to build:** a tabela diz "Potsdam, 26 km", e 26 km não diz para que lado.
Nem se as cinco vizinhas estão todas do mesmo lado, nem se a cidade escolhida
está no meio delas ou na beira.

Este ticket entrega o mapa: a cidade escolhida no centro, as vizinhas marcadas em
volta, enquadrado para caber todas. É o que transforma uma distância em posição.

O enquadramento é calculado das coordenadas, nunca um zoom fixo: as vizinhas de
Berlim cabem em dezenas de quilômetros e as de Honolulu em milhares, e um zoom
fixo erraria os dois.

O mapa mostra **onde as cidades ficam**. Não mostra chuva, nuvem nem temperatura
em camadas: a API externa serve dados por coordenada e não serve tiles, e camadas
de radar exigiriam um segundo fornecedor com chave própria — enquanto o glossário
descreve "a API externa" no singular.

**Blocked by:** 01 (as coordenadas precisam chegar ao frontend) e 02 (a página
precisa existir)

**Status:** ready-for-agent

- [ ] O mapa aparece na página Cidades vizinhas, com a cidade escolhida no centro
- [ ] As cidades vizinhas aparecem marcadas
- [ ] O marcador da cidade escolhida é distinto dos das vizinhas
- [ ] O enquadramento inicial cabe todas as cidades, sem zoom manual
- [ ] O enquadramento funciona tanto numa região densa quanto numa cidade isolada
- [ ] Clicar num marcador identifica a cidade
- [ ] O mapa pode ser movido e ampliado
- [ ] Trocar a cidade escolhida reenquadra o mapa na nova região
- [ ] O mapa é destruído ao sair da página, sem deixar instância órfã
- [ ] Montar e desmontar duas vezes em desenvolvimento não duplica o mapa nem quebra
- [ ] O crédito do OpenStreetMap aparece, como a licença exige
- [ ] Os tiles não ficam gritantes no tema escuro
- [ ] O mapa é um componente próprio, recebendo cidade escolhida e vizinhas como props
- [ ] Sem camadas meteorológicas, sem chave de API, sem conta em serviço de mapas
- [ ] O peso que a dependência acrescenta ao bundle foi verificado e registrado
