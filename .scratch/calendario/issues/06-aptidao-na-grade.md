# 06: Aptidão na grade

Status: done

**What to build:** o seletor de atividade no topo da página e a grade que se pinta
inteira pela aptidão da atividade escolhida.

**Blocked by:** 04, 05

## O seletor

- [x] As quatro atividades no topo, com uma escolhida por vez
- [x] A escolha governa a grade inteira: escolher "lavar roupa" pinta os sete dias
      pela aptidão de lavar roupa
- [x] Um estado sem atividade escolhida, em que a grade mostra só previsão — é
      como a fatia 04 a deixou, e é o estado inicial
- [x] Navegável por teclado

## Vai para a URL?

- [x] Decidir e registrar. O precedente está dividido: a janela temporal da
      Tendência viaja na URL (`janelaNaUrl.ts`) porque governa a página inteira e
      é compartilhável; a ordenação da tabela de vizinhas **não** viaja, porque
      "a ordem de uma tabela de cinco linhas não é algo que alguém compartilhe"
      (ADR 0006)
- [x] Recomendação: **vai para a URL**, com o mesmo formato de `janelaNaUrl.ts`
      (o valor default omitido). A atividade governa a página inteira, como a
      janela, e "manda o link do calendário mostrando quando dá para lavar roupa"
      é um compartilhamento plausível — ao contrário da ordem de uma tabela
      — **Decidido: vai para a URL**, pela recomendação e pelos dois critérios
      que o ADR 0006 usou para mandar a ordenação da tabela para o outro lado.
      Registrado no cabeçalho de `atividadeNaUrl.ts`. Duas consequências que a
      issue não previa e que a implementação resolveu: o parâmetro é escrito com
      `replace` (escolher as quatro atividades em sequência empilharia quatro
      entradas no histórico, e o "voltar" andaria uma atividade por clique em
      vez de sair da página); e o estado **sem** atividade remove o parâmetro em
      vez de escrever vazio, pelo mesmo motivo que `comJanela` omite o default

## A pintura

- [x] Cada célula do horizonte curto reflete a aptidão da atividade escolhida
- [x] **Texto além de cor.** Story 11 — a aptidão precisa ser lida por quem não
      distingue as cores, e anunciada por leitor de tela. É a mesma exigência que
      as cores de severidade do INMET carregam
- [x] Contraste verificado nos dois temas. O precedente já mordeu: as três cores
      do INMET reprovaram com texto branco e exigiram texto preto fixo
- [x] Os dias 8 a 16 **não** se pintam, e a página diz por quê — senão parece que
      falhou. A mesma explicação da fronteira da fatia 04 pode absorver isto
- [x] O motivo da reprovação visível — no detalhe do dia, não em todas as células
      ao mesmo tempo

## O detalhe do dia

- [x] Clicar num dia abre o detalhe daquele dia
- [x] O detalhe mostra a previsão completa e as **quatro** aptidões, não só a
      escolhida — quem clicou num dia quer saber sobre o dia
- [x] Com o motivo de cada uma
- [x] Fechável por teclado

## Estados

- [x] Nenhum dia bom na semana para a atividade escolhida: mensagem clara de que
      o tempo não colabora, **não** um estado de erro (ADR 0011, e a mesma
      distinção que `status_dos_alertas` faz entre "sem alerta" e "sem resposta")
- [x] O rótulo de que a aptidão é derivada da previsão e nossa — mesma obrigação
      que o ADR 0001 impôs a cada card de condição prevista, e pelo mesmo motivo:
      é o que impede que se leia como recomendação de autoridade

## Comments

### O que a verificação contra a página rodando encontrou

A fatia foi verificada com o backend real, em São Paulo e em Belém, nos dois
temas e pelo teclado. **Um defeito só apareceu ali, e ele passava no
compilador e no lint:**

- **A grade não pintava nenhuma cor.** As utilitárias `border-line` e `bg-card`
  são emitidas **depois** das de aptidão no CSS gerado (medido no `dist`:
  posição 12243 contra 11819), e a célula do horizonte curto pedia as duas
  famílias ao mesmo tempo — a de aptidão perdia por ordem de regra, não por
  especificidade. Os tipos estavam certos, as classes existiam no CSS e a
  célula renderizava; só não mudava de cor. A correção foi fazer **cor de traço
  e de fundo saírem da mesma expressão**, de modo que o par em conflito não
  tenha como ser emitido

### As cores, medidas antes de escolhidas

O precedente do INMET já tinha mordido uma vez, então a medida veio antes. O
que ela mostrou mudou o desenho: **o preenchimento de nível é quase invisível
contra o cartão** — 1,10:1 o verde, 1,11:1 o âmbar, 1,22:1 o vermelho, todos
muito abaixo dos 3:1 de elemento não-textual. Um fundo suave sozinho não
distinguiria a célula pintada da célula sem pintura.

Daí cada nível carregar **também** uma cor de traço e de texto, medida sobre o
preenchimento e sobre o cartão, porque hoje e o horizonte longo não têm o mesmo
fundo das demais. Claro: boa 4,57/5,02 · média 4,51/5,02 · ruim 5,30/6,47.
Escuro: boa 7,66/9,45 · média 7,89/9,87 · ruim 5,35/5,96. Todas acima de 4,5:1.

As seis cores são **tokens no `index.css`**, e não constantes em TypeScript: o
tema vive num atributo do `<html>` e o seu estado em React é local do
`Cabecalho`, então uma cor escolhida em JS no render ficaria congelada no tema
em que a grade montou — alternar o tema repintaria a página e deixaria a
aptidão para trás.

### Hoje não é pintado pela aptidão, e isso é deliberado

A pintura vence o fundo de cartão, mas **não** vence o azul de hoje. O dia
corrente é o único ponto fixo da grade, e trocar o azul por verde o faria
desaparecer exatamente quando a grade fica mais cheia de cor. A célula de hoje
diz a sua aptidão pela palavra — que é o canal que nunca depende de cor de
qualquer modo, e é por isso que ele existe.

### A célula virou botão

`onClick` no `<li>` daria o clique sem dar o foco, o `Enter`, o `Espaço` nem o
papel. O `<li>` ficou com `display: contents` — continua sendo o item da lista
para a semântica e deixa de ser caixa no grid para o layout, de modo que o
botão ocupa a célula sem que a altura mínima precise ser mantida em dois
lugares.

### O primeiro diálogo do repo

Não havia precedente de modal — o `BuscaCidade` trata `Escape` no próprio campo
e não abre camada. O `DetalheDoDia` carrega o mínimo para não ser armadilha de
teclado: papel declarado, foco movido para dentro ao abrir, `Escape` de
qualquer lugar, **foco de volta para a célula que o abriu**, e clique no fundo
fecha. Verificado: `Enter` abre, `Escape` fecha, o foco volta para a célula
exata.

Não é `<dialog>` nativo: ele renderiza no *top layer*, e o repo inteiro depende
de tokens herdados — um diálogo de três parágrafos não valia a investigação.

### A semana sem dia bom, verificada por injeção

Nenhuma cidade real tinha os sete dias reprovados na janela testada, então o
estado foi forçado interceptando a resposta. Confirmado o que o ADR 0011 exige:
mensagem **sem** `role="alert"`, a grade continua com as dezesseis células e os
sete dias pintados de ruim, e o motivo de cada um a um clique.

### Duas explicações que já existiam absorveram as novas

A nota da fronteira ganhou a frase da story 14 (por que os dias distantes não
têm aptidão) em vez de um aviso próprio: é a mesma causa da frase que ela já
dava, e duas notas diriam a mesma coisa duas vezes. A frase só aparece com uma
atividade escolhida — sem escolha, explicar a ausência de algo que ninguém
pediu seria ruído.

### O que a revisão (`/code-review`) mudou

Os dois eixos encontraram coisa real, e o achado mais grave é **exatamente o
que a issue mandava não repetir**.

- **O contraste reprovava, e reprovava pelo motivo que a issue nomeia.** As seis
  cores foram medidas com cuidado — mas só contra a palavra do nível. O resto da
  célula continuou com os tokens cinzas, agora sobre um fundo colorido que não
  existia quando eles foram escolhidos. Medido: `ink-2` (a mínima) cai para
  4,40 / 4,34 / **3,96** sobre os três preenchimentos claros, e `ink-3` ("sem
  dado") para 2,31 / 2,28 / **2,08** — todos abaixo de 4,5:1.

  É **a mordida do INMET ao contrário**: lá o texto branco reprovou sobre as
  três cores de severidade, aqui o cinza reprova sobre os três preenchimentos.
  A lição que ficou daquela vez era medir o texto contra o fundo que ele *vai*
  ter, e ela não foi aplicada inteira. O texto secundário da célula pintada
  passou a usar a **cor do nível**, que já tinha sido medida sobre aquele
  fundo. Verificado no navegador depois da correção: 4,51 e 5,30 no claro, 7,89
  e 5,35 no escuro

- **A mensagem de semana ruim não cobria a semana que a story descreve.** A
  condição era "todos `ruim`", e a story 15 fala de uma semana em que *nenhum
  dia serve* — sete dias `media` são exatamente isso, e ficavam em silêncio. Um
  único `media` no meio de seis `ruim` também calava tudo, e essa é a semana
  típica de uma cidade que o ADR 0011 manda aceitar como sempre-ruim. Virou
  **"nenhum `boa`"**

- **A palavra da aptidão era anunciada duas vezes.** O `sr-only` já dizia "dia
  bom para esporte ao ar livre" e o `<p>` visível não tinha `aria-hidden`, ao
  contrário dos irmãos — o leitor ouvia a frase e depois "boa" solto. O detalhe
  já fazia certo; a célula não

- **O `radiogroup` prometia teclado que não existia.** Cinco `role="radio"` sem
  `onKeyDown`: cada opção era uma parada de `Tab` e as setas não faziam nada.
  O defeito era **herdado do `FiltroDeJanela`**, e por isso a correção foi um
  `GrupoDeRadio` compartilhado com o padrão WAI-ARIA completo — tabindex
  rotativo, setas que andam e selecionam, `Home`/`End`, volta ao circular. As
  duas páginas ganharam junto

- **A pílula do seletor era cópia byte a byte do `FiltroDeJanela`**, incluindo
  o estado selecionado — duas cópias divergindo fariam a escolha ativa parecer
  diferente em duas páginas que fazem a mesma coisa. Absorvido pelo mesmo
  `GrupoDeRadio`

- **A cascata de quatro ternários virou `superficieDaCelula()`**, com a razão
  (a ordem de emissão do CSS, e por que hoje vence a aptidão) na função em vez
  de num comentário sobre uma expressão

- **`julgamentoDe` estava duplicado** entre a célula e a página, em formas
  diferentes do mesmo `find`. Foi para o `aptidao.ts`, que é o dono do
  conceito; `COR_DO_TEXTO` e `COR_SECUNDARIA`, que nasceram idênticas, viraram
  `COR_DO_NIVEL`

- **`ATIVIDADES` alegava ser "a ordem em que o seletor as mostra"**, o que
  deixou de ser verdade quando o seletor passou a montar as opções pelos
  rótulos do backend. Deixou de ser exportada e o comentário passou a dizer o
  que ela realmente é: o validador do parâmetro da URL

### O que a verificação em navegador cobriu

Tudo acima foi medido com a página rodando contra o backend real, nos dois
temas: contraste calculado no DOM, árvore de acessibilidade lida (os dezesseis
`listitem` sobrevivem ao `display: contents`, e os dias são anunciados com data,
previsão e aptidão), navegação por setas percorrida opção a opção, `Enter` e
`Escape` no detalhe com o foco voltando à célula exata, e os dois estados de
semana sem dia bom forçados por interceptação. A página Tendência foi
reverificada por causa do componente compartilhado.
