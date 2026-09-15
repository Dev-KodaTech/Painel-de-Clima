# Página Cidades vizinhas

Status: ready-for-agent

Origem: sessão de grilling + domain-modeling. Decisões registradas em
[ADR 0006](../../docs/adr/0006-vizinhas-e-comparacao-nao-lista-longa.md).

## Problem Statement

A barra lateral oferece "Cidades vizinhas" desde a navegação das seis páginas,
e a página não existe — quem clica encontra um título e a frase "Ainda nao
construida".

Pior: a frase promete "a lista inteira que o painel da Visao geral trunca", e
essa lista não existe. O backend produz no máximo cinco cidades vizinhas e o
painel da Visão geral já mostra as cinco. Não há nada truncado para revelar.

O que falta de verdade é outra coisa. O painel lista as vizinhas na ordem da
distância e mostra a temperatura de cada uma, mas não deixa comparar: para
saber onde está mais quente agora, a pessoa lê cinco números soltos e compara de
cabeça. E a distância em quilômetros não diz para que lado — "Potsdam, 26 km"
não conta se é norte ou sul, nem se as cinco estão todas do mesmo lado.

## Solution

Uma página que responde "como está a região em volta, e onde isso fica".

Duas partes. Uma **tabela comparativa** com as cinco cidades vizinhas **mais a
cidade escolhida**, ordenável por temperatura ou por distância — a cidade
escolhida sempre presente e visivelmente distinta, porque é a referência de quem
as distâncias são medidas, não mais uma linha.

E um **mapa** centrado na cidade escolhida, com as vizinhas marcadas, enquadrado
para caber todas. É o que transforma "26 km" em posição.

O mapa mostra onde as cidades ficam. Não mostra chuva, nuvem nem temperatura em
camadas: a API externa serve dados por coordenada e não serve tiles de mapa.

## User Stories

1. Como visitante, quero abrir a página Cidades vizinhas pela barra lateral, para ver a região em volta da cidade escolhida.
2. Como visitante, quero ver a cidade escolhida junto das vizinhas na mesma tabela, para comparar todas de uma vez.
3. Como visitante, quero que a cidade escolhida seja visivelmente distinta das vizinhas, para não confundir a referência com um resultado.
4. Como visitante, quero ordenar a tabela por temperatura, para descobrir onde está mais quente agora.
5. Como visitante, quero ordenar a tabela por distância, para voltar à ordem geográfica depois de ordenar por temperatura.
6. Como visitante, quero ver qual critério de ordenação está ativo, para saber o que estou olhando.
7. Como visitante, quero ver a distância de cada cidade vizinha, para julgar se "vizinha" significa 20 km ou 400 km.
8. Como visitante numa cidade isolada, quero ver que as vizinhas são distantes, para não supor uma vizinhança que não existe.
9. Como visitante, quero ver a temperatura atual de cada cidade vizinha, para comparar o clima regional.
10. Como visitante, quero ver o ícone e a descrição do tempo de cada vizinha, para comparar as condições e não só os números.
11. Como visitante, quero ver o país de cada vizinha, para entender quando a região atravessa fronteira.
12. Como visitante, quero ver um mapa com a cidade escolhida no centro, para situar geograficamente o que a tabela lista.
13. Como visitante, quero ver as cidades vizinhas marcadas no mapa, para saber para que lado cada uma fica.
14. Como visitante, quero que o mapa se enquadre para caber todas as cidades, para não precisar dar zoom manualmente ao abrir.
15. Como visitante, quero distinguir no mapa o marcador da cidade escolhida dos das vizinhas, para reconhecer o centro de referência.
16. Como visitante, quero clicar num marcador do mapa e ver de que cidade se trata, para ligar o ponto à linha da tabela.
17. Como visitante, quero mover e dar zoom no mapa, para explorar a região além do enquadramento inicial.
18. Como visitante que trocou de cidade, quero que a tabela e o mapa acompanhem a nova cidade escolhida, para não ver dados da anterior.
19. Como visitante sem cidade escolhida, quero uma instrução para buscar uma, em vez de uma página vazia ou quebrada.
20. Como visitante, quero ver o estado de carregamento enquanto o painel chega, para saber que algo está acontecendo.
21. Como visitante, quero uma mensagem clara quando o painel falha, para saber que o problema não é meu.
22. Como visitante numa cidade sem vizinhas, quero uma mensagem explicando a ausência, para não achar que a página quebrou.
23. Como visitante, quero ver o crédito das fontes de dados e do mapa, para saber de onde vem o que estou lendo.
24. Como visitante no tema escuro, quero que a página e o mapa acompanhem o tema, para não levar um clarão.
25. Como visitante de teclado, quero alcançar e acionar os controles de ordenação, para usar a página sem mouse.
26. Como visitante com leitor de tela, quero que a ordenação anuncie o estado atual, para saber por onde a tabela está ordenada.
27. Como visitante que chegou por um link compartilhado, quero ver a mesma região que quem compartilhou, para o link valer.

## Implementation Decisions

**A página não busca dados.** Lê as cidades vizinhas e as unidades do painel que
a rota de layout já carregou, via o contexto do outlet. Segue a regra do
[ADR 0003](../../docs/adr/0003-historico-e-buscado-na-pagina.md): dado que várias
páginas leem o painel, ele vai no layout. Nenhum endpoint novo, nenhuma
requisição nova.

**O backend não muda.** Continuam cinco cidades vizinhas no máximo. Aumentar
esse número foi considerado e rejeitado — ver ADR 0006: a seleção é curada por
anéis, população e separação mínima, e degrada a partir da sexta.

**A página entra pelo registro de páginas construídas**, do mesmo jeito que a
Tendência entrou. A frase "Ainda nao construida" sai da navegação, e a promessa
da lista truncada sai junto, porque é falsa.

**A ordenação é estado local do componente**, não viaja na URL. Diferente da
janela temporal da Tendência: a ordem de uma tabela de seis linhas não é algo
que alguém compartilhe, e a cidade escolhida — que é o que importa no link — já
viaja pela URL conforme o [ADR 0002](../../docs/adr/0002-cidade-na-url.md).

**A cidade escolhida na tabela não tem distância.** Distância de si mesma é
tautologia, e exibir "0 km" a faria parecer um dado. A célula fica vazia ou
traz um traço.

**A ordenação por temperatura é decrescente por padrão** (mais quente primeiro),
porque a pergunta que motiva ordenar por temperatura é "onde está mais quente".
A ordenação por distância é crescente, que é a ordem em que o backend já entrega.

**Mapa com Leaflet e tiles do OpenStreetMap.** Sem chave, sem conta, sem cota
para gerenciar. Mapbox foi rejeitado por exigir token num projeto que hoje não
tem nenhum segredo. O crédito do OpenStreetMap entra na mesma linha de rodapé
que já credita Open-Meteo e GeoNames, e é obrigatório pela licença.

**Sem camadas meteorológicas no mapa.** Radar e camadas de precipitação
exigiriam um segundo fornecedor com chave própria, e o glossário descreve "a API
externa" no singular.

**O mapa é um componente próprio**, recebendo a cidade escolhida e as vizinhas
como props, para que possa ser reusado se um dia outra página quiser um mapa.

**O enquadramento inicial é calculado das coordenadas**, não um zoom fixo: as
vizinhas de Berlim cabem em dezenas de quilômetros, as de Honolulu em milhares.

**Leaflet monta sobre um elemento do DOM e não é React.** O componente precisa
criar o mapa uma vez, atualizar marcadores quando a cidade muda, e destruir o
mapa ao desmontar — sob StrictMode, que monta e desmonta duas vezes em
desenvolvimento.

**O tema escuro afeta o mapa.** Os tiles padrão do OpenStreetMap são claros e
ficariam gritantes no tema escuro. A página respeita o tema pelos tokens de cor
já existentes; o tratamento dos tiles fica a cargo de quem implementar, sendo
aceitável um filtro CSS sobre a camada.

**Reuso obrigatório:** o componente de painel, o componente de ícone do tempo,
os formatadores de distância e temperatura, e os tokens de cor semânticos. As
unidades vêm do payload, nunca escritas à mão na interface.

## Testing Decisions

**Um bom teste aqui exercita o comportamento externo**: dado um conjunto de
cidades vizinhas, o que sai ordenado e em que ordem. Não testa como o estado da
ordenação é guardado, nem a existência de funções internas.

**A costura é uma só, e é a função de ordenação** — uma função pura que recebe
a cidade escolhida, as vizinhas e o critério, e devolve as linhas na ordem de
exibição. É o único lugar desta entrega com lógica que pode estar errada.

**Mas o frontend deste repo não tem testes unitários**, por decisão registrada
no ticket 12 do esforço original: TypeScript cobre a classe de erro que importa.
Esta entrega **não introduz uma suíte de testes no frontend** — seria inverter
uma decisão do projeto de carona numa página.

O que fica no lugar: a função de ordenação é escrita como função pura e
exportada, de modo que a costura exista no dia em que o repo decidir testar o
frontend. A decisão de criar essa suíte é separada e não pertence a esta spec.

**Nenhum teste de backend**, porque o backend não muda. As vizinhas já têm doze
testes unitários e nove testes HTTP, e a página não toca nessa lógica.

**Verificação manual obrigatória** antes de fechar: uma cidade densa (Berlim,
vizinhas em dezenas de km), uma isolada (Honolulu, que tem quatro vizinhas e
não cinco — o caso que prova o enquadramento adaptativo e a lista curta), e uma
cidade sem nenhuma vizinha, se encontrável.

## Out of Scope

- **Camadas meteorológicas no mapa** — exigem segundo fornecedor e chave.
- **Aumentar o número de cidades vizinhas** — rejeitado no ADR 0006.
- **Mapa nas outras páginas** — o componente fica reusável, mas só esta página o usa.
- **Salvar uma cidade vizinha como local salvo** — depende de conta; ver a spec de locais salvos.
- **Ordenação persistida entre visitas** — é estado local, some ao sair.
- **Testes automatizados de frontend** — decisão do projeto, não desta página.
- **Responsividade para celular** — segue o estado atual do projeto, que é desktop.

## Further Notes

O mapa é a primeira dependência de frontend que manipula o DOM fora do React, e
a primeira que carrega imagens de um terceiro. Vale conferir o peso que ela
acrescenta ao bundle.

A cidade escolhida aparecer dentro de uma tabela chamada "cidades vizinhas" é a
tensão de vocabulário desta página: ela não é uma vizinha. O glossário é
explícito sobre a cidade vizinha existir sempre em relação à escolhida — o
rótulo da tabela e o tratamento visual da linha precisam sustentar essa
diferença, não apagá-la.
