# 02: A página Cidades vizinhas existe, com a tabela comparativa

**What to build:** quem clica em "Cidades vizinhas" na barra lateral encontra
hoje um título e a frase "Ainda nao construida". Pior, a navegação promete "a
lista inteira que o painel da Visao geral trunca" — e essa lista não existe: o
backend produz no máximo cinco vizinhas e o painel já mostra as cinco.

Este ticket entrega a página de verdade, com o que ela tem de próprio: uma tabela
comparativa com as cinco cidades vizinhas **mais a cidade escolhida**, todas lado
a lado. O painel da Visão geral lista; a tabela compara.

A cidade escolhida entra como referência, não como resultado: é dela que todas
as distâncias são medidas, e a interface precisa mostrar isso. Ela não tem
distância — distância de si mesma é tautologia, e um "0 km" pareceria um dado.

A ordenação e o mapa vêm em tickets próprios. Esta página já é demoável sem eles.

**Blocked by:** None (can start immediately). Não depende do ticket 01: a tabela
não usa coordenadas.

**Status:** ready-for-agent

- [ ] `/vizinhas` mostra a página construída, não mais a página vazia
- [ ] A tabela traz a cidade escolhida e as cidades vizinhas, na ordem da distância
- [ ] A cidade escolhida é visivelmente distinta das vizinhas
- [ ] A célula de distância da cidade escolhida não traz um número
- [ ] Cada linha mostra nome, país, distância, ícone, descrição e temperatura
- [ ] As unidades vêm do payload, nunca escritas na interface
- [ ] A frase "Ainda nao construida" e a promessa da lista truncada saem da navegação
- [ ] Sem cidade escolhida, a página instrui a buscar uma
- [ ] Enquanto o painel carrega, a página informa o carregamento
- [ ] Se o painel falha, a página mostra a mensagem de erro
- [ ] Numa cidade sem vizinhas, a página explica a ausência em vez de mostrar tabela vazia
- [ ] A página não faz requisição própria: lê o painel que a rota de layout já carregou
- [ ] O rodapé credita as fontes de dados
- [ ] A página respeita o tema escuro
- [ ] Reusa o componente de painel, o de ícone e os formatadores de distância e temperatura
