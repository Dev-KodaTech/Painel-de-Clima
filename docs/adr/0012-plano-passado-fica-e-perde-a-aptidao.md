# Plano de dia passado fica na lista, esmaecido e sem aptidão

Um plano cujo dia já passou **continua na faixa**. Vai para um grupo próprio no
fim da lista, visualmente esmaecido, e **sem aptidão nenhuma ao lado**.

Era o último risco aberto da spec do Calendário ("plano de dia passado não tem
política definida"), e a story 28 já dizia a metade que não se negocia: *um
plano de ontem não pode sumir sem aviso*.

## Por que não some

A pessoa criou aquele plano. Fazê-lo desaparecer à meia-noite é o app apagando
algo de alguém sem que ninguém peça — e sem deixar rastro de que apagou. Quem
abrisse a página no dia seguinte não veria uma lista menor: veria uma lista
**correta**, sem nenhum sinal de que faltava coisa. Esse é o modo de falha pior,
porque não se percebe.

É a mesma regra que o `LocalSalvo` já segue por outro caminho: o que tem dono só
sai da lista quando o dono manda. Apagar continua sendo uma ação, com
confirmação, e não um efeito do relógio.

## Por que esmaecido e agrupado, e não misturado

Um plano de ontem e um plano de quinta não pedem a mesma coisa de quem lê. O de
quinta é uma decisão pendente — dá para olhar a aptidão e adiar. O de ontem é
registro: não há o que decidir sobre ele.

Deixá-los misturados na mesma ordem cronológica faria a faixa abrir sempre pelo
passado, e o que a pessoa veio ver — os próximos dias — ficaria abaixo de uma
pilha que só cresce. O agrupamento é o que mantém a faixa útil numa conta velha.

O esmaecimento **não é o único sinal**, e isso é deliberado: o grupo tem um
título próprio ("Já passaram"), que é o canal que sobrevive ao daltonismo e ao
leitor de tela. A opacidade reforça para quem varre a faixa com os olhos; ela
não carrega a distinção sozinha. É a mesma regra que a aptidão já segue na
grade — cor reforça, palavra informa.

## Por que sem aptidão, e esta é a parte que custou a decidir

A tentação é mostrar a aptidão que aquele dia teve. Ela é forte porque parece
mais informativa: "você lavou roupa num dia ruim" é uma frase com conteúdo.

Não dá, e o motivo é de dado e não de gosto. **A previsão daquele dia já não
existe.** A grade começa hoje e vai ao dia 16; ontem não está nela, e o
`/api/horizonte` não o devolve. Exibir aptidão ali exigiria uma das duas coisas
que o app recusa em outro lugar:

- **guardar a aptidão junto do plano** — proibido pelo verbete *Plano* e pela
  mesma razão que o `LocalSalvo` não guarda clima: clima guardado envelhece, e
  alguém veria a previsão de anteontem sem saber que é de anteontem;
- **buscar o passado** — seria o `archive-api`, que é reanálise e não previsão.
  Julgar um dia passado com medição e apresentá-lo com o mesmo rótulo de um
  julgamento feito sobre previsão apagaria a fronteira entre medido e previsto,
  que é exatamente a distinção que o verbete *Histórico climatológico* mantém.

Então a faixa não tem o que dizer sobre o tempo de ontem, e **diz isso** em vez
de deixar um espaço vazio onde a aptidão estaria nos outros itens. Um branco
naquele lugar se leria como falha de carregamento — o mesmo defeito que a nota
da fronteira do dia 8 existe para evitar na grade.

## Consequences

**A faixa cresce sem teto.** Uma conta de um ano tem um ano de planos passados,
e todos ficam. Não há paginação nesta fatia, e é uma dívida assumida
conscientemente: a alternativa era apagar, que é o que este registro recusa. O
gatilho para revisitar é nomeável — quando a faixa ficar longa o bastante para
atrapalhar, a resposta é recolher o grupo do passado ou paginá-lo, **nunca**
descartá-lo.

**Apagar continua sendo a única saída da lista**, e por isso ela precisa estar
sempre disponível no item passado — não só nos futuros. Um plano que não some
sozinho e também não pode ser apagado seria permanente por acidente.

**O "hoje" que decide o que é passado vem da cidade, não do browser.** É o
primeiro dia da grade, que o backend monta no fuso da cidade consultada. Lido do
relógio local, quem está em São Paulo consultando Tóquio veria um plano mudar de
grupo por causa de um fuso que não é o da página. A comparação é de string
`AAAA-MM-DD`, pela regra do `formato.ts`: nesse formato a ordem lexicográfica é
a cronológica, e `new Date("2026-09-22")` seria meia-noite **UTC** — dia 21 às
21h em São Paulo, que é o erro que esta escolha evita.

**Enquanto a grade não carregou, não há "hoje"**, e nenhum plano é classificado
como passado. É o estado correto: sem saber que dia é na cidade, agrupar seria
chutar. A faixa aparece inteira e o grupo do passado se forma quando a grade
chega.
