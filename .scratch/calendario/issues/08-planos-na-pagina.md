# 08: Planos na página

Status: done

**What to build:** a faixa de planos ao lado da grade, a criação de plano ao
clicar num dia, e o convite para entrar de quem não tem conta.

É a fatia que faz o Calendário ser a **primeira página mista** do app: previsão e
aptidão para qualquer um, planos só para o dono.

**Blocked by:** 06, 07

## A faixa

- [x] Lista dos planos ao lado da grade, ordenada por dia
- [x] Cada plano com título, dia, atividade e **a aptidão daquele dia para aquela
      atividade** — é o cruzamento que justifica a página existir
- [x] Apagar, com confirmação
- [x] Dias com plano são marcados na grade
- [x] Em tela estreita a faixa não pode empurrar a grade para fora — decidir o
      comportamento (abaixo da grade, recolhível) e verificar em largura de celular

## Criar

- [x] Clicar num dia abre o detalhe (fatia 06), e é de lá que se cria o plano
- [x] Campos: título, atividade. O dia vem do dia clicado — não se digita
- [x] **Sem campo de hora.** Se alguém for acrescentá-lo depois, precisa reabrir o
      verbete *Plano* e o ADR 0010: a aptidão é diária e o horizonte longo não tem
      dado horário
- [x] A atividade do seletor entra pré-escolhida — quem está olhando "lavar roupa"
      e clica numa quinta provavelmente quer um plano de lavar roupa
- [x] Criar um plano para um dia do horizonte longo é permitido, e a aptidão
      simplesmente não aparece ali. Planejar longe é legítimo; julgar longe não é

## Estados de conta

- [x] Sem conta: a grade e a aptidão funcionam normalmente, e no lugar da faixa
      vai um convite para entrar dizendo o que se ganha. **A página não pode
      exigir conta para nada além dos planos**
- [x] O convite preserva a cidade no link, com `useComCidade()` — o mesmo cuidado
      que o cabeçalho já toma
- [x] Com conta e sem planos: mensagem dizendo como criar o primeiro
- [x] `consultando`: não piscar o convite antes de saber se há conta. O
      `SeloDaConta` já resolve isso reservando espaço; seguir o precedente
- [x] Sessão expirada no meio de um envio: a página não pode perder o que foi
      digitado sem dizer nada. **É caminho novo** — todo o resto do app é leitura
      pública ou formulário de conta

## Planos de dias passados

- [x] Decidir e registrar a política (risco aberto na spec, story 28). Um plano de
      ontem não pode sumir sem aviso — a pessoa o criou e some sem ela pedir
- [x] Recomendação: continuam na lista, visualmente esmaecidos, agrupados
      separadamente. Sem aptidão, porque a previsão daquele dia já não existe

## Transversais

- [x] Teclado: criar e apagar sem mouse
- [x] Leitor de tela: cada plano anunciado com título, dia, atividade e aptidão
- [x] Trocar de cidade **não** mexe nos planos — eles são da conta, não da cidade.
      A aptidão exibida ao lado deles, sim, muda com a cidade. Vale um comentário
      no código: é a consequência menos óbvia de a página ser mista

## Comments

### As duas decisões que a issue delegou

**Planos de dias passados: ficam, esmaecidos, agrupados e sem aptidão.** É a
recomendação da própria issue, e virou o [ADR
0012](../../../docs/adr/0012-plano-passado-fica-e-perde-a-aptidao.md) porque a
metade que custou não foi "fica ou some" — foi a aptidão. Mostrar a aptidão que
o dia teve exigiria guardá-la junto do plano (proibido pelo verbete *Plano*) ou
buscar o `archive-api`, que é reanálise e não previsão: apresentar um julgamento
feito sobre medição com o mesmo rótulo de um feito sobre previsão apagaria a
fronteira entre medido e previsto. Então a faixa **diz** que não tem o que dizer,
em vez de deixar o branco que se leria como falha de carregamento.

**Tela estreita: a faixa empilha abaixo da grade** (`lg:flex-row`), e não recolhe
atrás de um botão. Recolher acrescentaria estado de UI, um controle a mais para
teclado e leitor de tela, e uma decisão de qual é o padrão; empilhar é o que o
grid da Visão geral e a tabela de vizinhas já fazem, e ninguém precisa aprender
nada. A grade vem primeiro porque é o que a página promete a quem chega — e é a
metade que funciona sem conta.

Uma terceira decisão que a issue não previa: **a faixa lista todos os planos da
conta**, e não só os dos dezesseis dias. Restringi-la à janela faria um plano de
dezembro desaparecer da tela até dezembro chegar, que é exatamente o "sumir sem
aviso" que a story 28 proíbe. Daí `PosicaoDoPlano` ter quatro estados: cada um
pede uma frase diferente, e colapsá-los faria a faixa dizer a mesma coisa sobre
um plano de ontem e um de dezembro.

### O que a verificação contra a página rodando encontrou

Verificado com o backend real e o Postgres, em São Paulo e em Belém, nos dois
temas, por teclado, e em três larguras. **Dois defeitos só apareceram ali, e os
dois passavam no compilador e no lint:**

- **O botão de apagar não existia para leitor de tela.** O `aria-hidden` estava
  no `<div>` que envolve o título *e* o botão, em vez de só no título — a linha
  inteira saía da árvore de acessibilidade, e com ela o único jeito de apagar um
  plano sem mouse. O requisito "apagar sem mouse" falhava exatamente assim, sem
  aparecer em lugar nenhum: o Playwright não achou o botão pelo nome acessível, e
  foi isso que denunciou.

- **O esmaecimento do passado reprovava no contraste.** `opacity-60` no item
  inteiro multiplica todo texto dentro dele contra o fundo: medido, 4,18:1 no
  título, 2,33:1 na linha de data e atividade e **1,68:1** na frase da aptidão,
  no tema claro. É a mordida do INMET pela terceira vez, agora por um caminho
  novo — não uma cor mal escolhida, mas uma opacidade que rebaixa cores que já
  tinham sido medidas. O erro estava em tratar "esmaecido" como propriedade do
  item; o que o ADR pede é que ele **pareça** secundário sem deixar de ser
  legível, porque um plano de ontem não é rascunho: a pessoa precisa lê-lo para
  decidir apagá-lo. Virou fundo recuado e borda apagada, com o texto intacto — a
  mesma solução que a célula do horizonte longo já usa, e pelo mesmo motivo: a
  distinção vive na moldura, não na tinta do texto.

Medido depois da correção, nos dois temas: tudo acima de 4,5:1 (título 15,52 /
13,82; data e atividade 4,83 / 7,07; frases de ausência 4,83 / 7,07).

**A troca de cidade foi medida, não deduzida.** Os mesmos cinco planos em São
Paulo e em Belém, com uma requisição só de `/api/planos` nas duas: o dia 19 é
*mediano* para lavar roupa em São Paulo e **ruim** em Belém, e nenhum plano foi
tocado. É o caso tropical que o ADR 0011 previu, aparecendo sozinho em dado real.

Também verificado: o convite não pisca antes de a conta ser conhecida (com
`/api/quem-sou` atrasado em 1,2 s, zero amostras em catorze o mostraram); a
sessão morta no meio do envio devolve "Entre para continuar" **com o título
intacto no campo**; falhar em carregar os planos não toca a grade (dezesseis
células, seis pintadas); e o build de produção renderiza igual ao dev — conferido
porque a fatia 06 levou uma mordida de classe que existia em dev e não no `dist`.

Uma ressalva honesta: **a rolagem horizontal a 375 px é anterior a esta fatia** e
não é dela — vem do `Cabecalho` (o alternador de tema, o cromo e os dois links,
todos `shrink-0`), e acontece igual sem faixa nenhuma. A faixa e a grade cabem na
área de conteúdo sem transbordar, que é o que esta issue exigia.

### O que a revisão (`/code-review`) mudou

O eixo de spec achou **uma armadilha de teclado real**, e ela é o achado mais
grave da fatia:

- **O `radiogroup` do formulário era inalcançável por `Tab`.** `GrupoDeRadio`
  fazia `tabIndex={ativa ? 0 : -1}`, e com **nenhuma** opção selecionada todas
  recebiam `-1`: o grupo inteiro sumia da ordem de tabulação. Como criar exige
  atividade, quem navega por teclado não conseguia criar plano nenhum no estado
  **inicial documentado da página** (sem `?atividade=` na URL). O mouse
  funcionava, então o defeito era invisível sem testar o teclado naquele estado
  exato.

  O `SeletorDeAtividade` nunca expôs isso porque a primeira opção dele é
  "Nenhuma" — há sempre uma ativa. O `CriarPlano` foi o primeiro grupo
  legitimamente sem escolha inicial. A correção foi no `GrupoDeRadio`, e não em
  quem chama: a promessa quebrada é a do papel `radiogroup`, e qualquer grupo
  futuro sem escolha inicial herdaria a mesma armadilha. É o padrão WAI-ARIA —
  sem seleção, a primeira opção recebe a parada. Verificado depois: a criação por
  teclado completa naquele estado, e a Tendência (que divide o componente)
  continua com uma parada só, na opção selecionada, com as setas funcionando.

O eixo de standards achou quatro coisas, todas reais:

- **Dois acentos em comentário de código** (`Pôr`, `espremê-la`), contra a regra
  da casa de acentuar só texto exibido e `.md`
- **Um bloco de documentação órfão**: o comentário de `cruzados` ficou separado
  da sua declaração quando `daConta` entrou no meio, e passou a ler como se fosse
  sobre outra coisa. Num repo cuja regra é que a razão mora junto da decisão, uma
  razão desgarrada é pior que nenhuma
- **`MAXIMO_DO_TITULO` duplicado do backend** — e o comentário nomeava a regra
  que ele mesmo quebrava. A duplicação fica, mas a razão passou a ser honesta:
  ao contrário do rótulo da atividade, **este número o backend não manda** (não
  há campo de onde lê-lo), e as alternativas eram inventar um endpoint de
  configuração ou deixar o campo sem `maxLength` — trocando um aviso imediato por
  um `422` depois do envio, no formulário em que perder o que se digitou é o
  risco que esta fatia existe para cobrir
- **`jaPassou` citava um chamador que não existe** ("a contagem do título"). O
  comentário passou a dizer os três pontos reais, e a registrar quem
  deliberadamente **não** a chama — a exibição de aptidão, que decide por
  `julgamento` e `posicao`

Uma quinta observação — um `aria-hidden` aninhado e morto — foi conferida e
removida: o pai já esconde a subárvore, e um atributo inútil ao lado de um
comentário que argumenta cuidadosamente *onde* o `aria-hidden` vai enfraquece o
argumento.

### O alinhamento da grade, quebrado desde a fatia 06 e achado agora

Reportado a olho na página rodando: **hoje, 17 de setembro de 2026, uma
quinta-feira, aparecia sob "Dom"** — e com ela as quinze células seguintes. A
grade inteira estava deslocada quatro colunas.

A causa é uma colisão entre duas decisões da fatia 06, e nenhuma das duas está
errada sozinha. A célula virou `<button>` (para ganhar foco, `Enter` e papel), e
o `<li>` recebeu `display: contents` para não ser uma caixa a mais no grid.
Só que **um elemento com `display: contents` não gera caixa, logo não é item do
grid, e toda colocação posta nele é ignorada**. O `gridColumnStart` continuava no
`<li>`, onde a fatia 04 o havia posto: o computador de estilo o aceitava
(`grid-column-start: 5` estava lá, medido no DOM), e o layout o descartava. Quem
virou item do grid foi o botão, com `auto`, caindo na primeira coluna livre.

Por que nada pegou isso antes:

- **O anúncio sempre esteve certo.** Ele vem de `dataPorExtenso`, não da posição
  — a célula dizia "quinta-feira, 17 de setembro" enquanto era desenhada sob
  "Dom". Toda a verificação por leitor de tela e por teclado passava.
- **`colunasVaziasAntesDe` sempre esteve certa.** Conferida de novo:
  `2026-09-17` dá `4`, e a coluna `5`. O defeito não era de aritmética de data,
  que era o lugar onde se procuraria.
- **O compilador e o lint não têm como ver.** É semântica de CSS, não de tipos.

A correção é mover o `gridColumnStart` para o **botão**, que é o item do grid de
verdade. Verificado em três cidades de fusos diferentes — São Paulo, Auckland
(onde a data local já é o dia 18, uma sexta) e Honolulu: as dezesseis células de
cada uma caem na coluna do seu dia da semana, zero erradas. Conferido também no
build de produção, e que a marca de plano, a pintura da aptidão e a fronteira do
dia 8 continuam nas células certas.

Vale como precedente: **o `display: contents` do `<li>` custa a colocação no
grid**, e qualquer coisa que dependa de posição precisa ir no botão. Está escrito
no comentário ao lado do `style`, que é onde alguém olharia antes de movê-lo de
volta.
