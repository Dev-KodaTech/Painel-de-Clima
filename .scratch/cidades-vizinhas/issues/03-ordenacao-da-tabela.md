# 03: A tabela ordena por temperatura e por distância

**What to build:** com a tabela na tela, a pergunta que ela ainda não responde é
"onde está mais quente agora?". Seis linhas em ordem de distância obrigam a
comparar seis números de cabeça.

Este ticket torna a tabela ordenável pelos dois critérios que fazem sentido:
temperatura e distância. Ordenar por temperatura começa pela mais quente, porque
é essa a pergunta que motiva ordenar por temperatura. Ordenar por distância
volta à ordem geográfica, que é a que o backend já entrega.

A cidade escolhida participa da ordenação por temperatura — ela é o termo de
comparação, e saber que ela é a mais fria das seis é exatamente o resultado
interessante. Na ordenação por distância ela fica em primeiro, por ser a origem.

A ordem é estado local da página e não viaja na URL: a ordenação de uma tabela
de seis linhas não é algo que alguém compartilhe, e o que importa no link — a
cidade escolhida — já viaja, conforme o ADR 0002.

**Blocked by:** 02 (a tabela precisa existir para ordenar)

**Status:** done

- [x] A tabela pode ser ordenada por temperatura e por distância
- [x] Ordenar por temperatura mostra a mais quente primeiro
- [x] Ordenar por distância mostra a mais próxima primeiro, com a cidade escolhida à frente
- [x] O critério ativo é visível
- [x] A ordenação é função pura e exportada, recebendo a cidade escolhida, as
      vizinhas e o critério, e devolvendo as linhas na ordem de exibição
- [x] Empate de temperatura tem desempate estável: a mesma entrada produz sempre a mesma ordem
- [x] Os controles são alcançáveis e acionáveis por teclado
- [x] Um leitor de tela anuncia por qual critério a tabela está ordenada
- [x] Trocar a cidade escolhida não deixa a tabela ordenada por um critério invisível
- [x] A ordem não é persistida e não aparece na URL

## Comments

**O `disabled` no botao da coluna ativa quebrava o teclado.** A primeira versao
desabilitava o botao do criterio ja ativo, com o argumento de que clicar nele
nao teria efeito. O efeito real era outro: `disabled` tira o elemento da ordem
de Tab, entao quem chegava nele pelo Tab e apertava Enter **perdia o foco para
o `<body>`** — o proximo Tab recomecava do topo da pagina. Quem usa teclado era
justamente quem pagava por uma decisao tomada pensando no mouse, contra o
criterio "os controles sao alcancaveis e acionaveis por teclado".

Ficou um botao comum cuja reativacao nao muda estado, com `aria-disabled` para
anunciar a quem ouve o que a cor e o triangulo dizem a quem enxerga. Verificado
no browser: o foco permanece no botao depois do Enter, e da para ordenar pelos
dois criterios e voltar sem tocar no mouse.

**A direcao de cada criterio mora num lugar so.** O sentido da ordenacao
aparecia em tres lugares — o sinal da comparacao, o valor de `aria-sort` e o
triangulo —, em dois arquivos, que precisavam concordar por vigilancia. Um
`aria-sort` discordando da ordem real e pior que anuncio nenhum, porque afirma
com confianca o que nao e verdade. Os tres saem agora da mesma entrada de
`CRITERIOS`, um `Record<Criterio, ...>` que o compilador exige completo.

**Um conflito com o ADR 0006, nao resolvido aqui.** O ADR justifica a ordem ser
estado local dizendo que "a ordem de uma tabela de **cinco** linhas nao e algo
que alguem compartilhe". Sao **seis** linhas: as cinco vizinhas mais a cidade
escolhida, que e a decisao central do proprio ADR. O numero nao muda o
argumento, e por isso a ordenacao segue sendo estado local. Corrigir o texto e
edicao do ADR — dominio, nao implementacao —, e fica registrado aqui em vez de
alterado de carona neste ticket.

**Um empate real na producao.** Berlim tem Potsdam e Oranienburg ambas a 27 km,
o que exercita o desempate estavel no criterio de distancia com dado de
verdade, e nao so no de temperatura. A ordem das duas segue a do backend.

**O arredondamento fazia a ordem parecer errada.** Ordenada por temperatura,
Berlim mostrava tres linhas seguidas lendo "19°C" (18,7 / 18,6 / 18,5). A ordem
estava certa — a ordenacao compara o numero do payload, nao o texto —, mas na
tela parecia arbitraria. A celula ganhou um `title` com o valor exato, via um
formatador novo em `formato.ts` para nao escrever numero com unidade a mao.

**Verificacao manual:** Berlim (cinco vizinhas, densa, com o empate de 27 km) e
Honolulu (quatro vizinhas, isolada, ate 337 km), nos dois temas, com teclado.
Nao foi encontrada uma cidade sem nenhuma vizinha — `ANEIS_KM` termina em
25.000 km justamente para que nao exista, como ja registrado no ticket 02.

**Sem testes automatizados**, conforme a spec: o frontend deste repo nao tem
suite, e cria-la e decisao separada. `ordenarLinhas` e pura e exportada, e a
costura fica pronta para o dia em que houver.
