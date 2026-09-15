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

**Status:** done

- [x] `/vizinhas` mostra a página construída, não mais a página vazia
- [x] A tabela traz a cidade escolhida e as cidades vizinhas, na ordem da distância
- [x] A cidade escolhida é visivelmente distinta das vizinhas
- [x] A célula de distância da cidade escolhida não traz um número
- [x] Cada linha mostra nome, país, distância, ícone, descrição e temperatura
- [x] As unidades vêm do payload, nunca escritas na interface
- [x] A frase "Ainda nao construida" e a promessa da lista truncada saem da navegação
- [x] Sem cidade escolhida, a página instrui a buscar uma
- [x] Enquanto o painel carrega, a página informa o carregamento
- [x] Se o painel falha, a página mostra a mensagem de erro
- [x] Numa cidade sem vizinhas, a página explica a ausência em vez de mostrar tabela vazia
- [x] A página não faz requisição própria: lê o painel que a rota de layout já carregou
- [x] O rodapé credita as fontes de dados
- [x] A página respeita o tema escuro
- [x] Reusa o componente de painel, o de ícone e os formatadores de distância e temperatura

## Comments

**Um conserto fora do escopo, registrado aqui.** O criterio "se o painel falha,
a pagina mostra a mensagem de erro" nao era alcancavel sem mexer no cliente da
API: `pegar`, em `frontend/src/api/client.ts`, tipava `detail` como `string`,
mas o 422 do FastAPI manda uma **lista** de objetos de validacao. A lista e
truthy, passava pelo `??` e ia inteira para a tela como
`[object Object],[object Object]`.

O defeito e anterior a este ticket e atinge todas as paginas — reproduzido na
Visao geral, que existe desde antes. O conserto e uma funcao de tres linhas que
olha a forma do valor em vez de confiar na anotacao, e vale para o app inteiro.

Sobra uma aspereza que este ticket nao resolve: a frase do 422 vem em ingles
("Input should be less than or equal to 90"), porque e do FastAPI. So aparece
com URL corrompida a mao, e traduzir mensagem de validacao do backend e outro
assunto.

**A tabela vazia nao tem como acontecer em producao.** `ANEIS_KM` termina em
25.000 km — meia circunferencia da Terra — e o comentario do backend diz que e
para garantir que nenhuma coordenada devolva lista vazia; `_sem_a_cauda_solta`
nunca corta o indice 0. O ramo fica porque o tipo permite a lista vazia e o
painel da Visao geral ja trata o mesmo caso, mas foi verificado com o payload
adulterado, nao com uma cidade real.
