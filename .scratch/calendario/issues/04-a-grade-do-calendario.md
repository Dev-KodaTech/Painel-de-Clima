# 04: A grade do calendário

Status: done

**What to build:** a página Calendário de verdade — a grade de dezesseis dias com
a fronteira visível —, substituindo o `PaginaVazia`. Sem aptidão e sem planos:
esta fatia entrega uma página completa e útil sozinha.

**Blocked by:** 02, 03

## A grade

- [x] Componente escrito à mão, CSS Grid e `Intl`. **Sem FullCalendar e sem
      shadcn/ui** — o porquê está na spec, e a decisão não deve ser reaberta numa
      limpeza futura sem ler aquele parágrafo
      — **entregue sem `Intl`.** Escrito à mão e em CSS Grid como pedido, mas os
      nomes de mês e de dia vêm das tabelas que `formato.ts` já mantém
      (`MESES`, `DIAS_CURTOS`), e não de `Intl.DateTimeFormat`. Duas razões: os
      sete rótulos de coluna da grade são exatamente os que `diaDaSemanaCurto`
      devolve — usar `Intl` criaria uma segunda fonte para os mesmos nomes —, e
      `Intl` segue o locale do **navegador**, o que renderizaria "Wed" no lugar
      de "Qua" para quem estiver com o browser em inglês, numa interface que é
      pt-BR inteira. O registro está no cabeçalho de `Grade.tsx`
- [x] Sem biblioteca de data. `Intl.DateTimeFormat` para nomes, e o truque de
      `Date.UTC` sobre componentes já fatiados que `formato.ts:indiceDoDia` usa,
      **pelo mesmo motivo**: o fuso do navegador não pode deslocar o dia
- [x] Atenção — esta é a primeira página do app com **aritmética** de data
      (limite de mês, offset do dia da semana na primeira linha). A regra do
      `formato.ts` continua: timestamp da previsão é hora de parede da cidade,
      fatiado como string, nunca `new Date(string)`
- [x] Dezesseis dias a partir de hoje, alinhados por dia da semana — a grade
      começa na coluna certa, com as células anteriores vazias
- [x] Reaproveitar o que já existe: os ícones de `@bybas/weather-icons` pela
      mesma via de `PrevisaoSemana.tsx`, a moldura de `Painel.tsx`, os tokens do
      `index.css`

## A célula

- [x] Horizonte curto: data, ícone, máxima e mínima
- [x] Horizonte longo: data, máxima, mínima e probabilidade de chuva —
      **sem ícone de céu**
- [x] Hoje é visualmente distinguível
- [x] A distinção entre os dois horizontes é estrutural e legível sem cor —
      leitor de tela e daltônico incluídos
- [x] Cada célula é anunciada com data e previsão, não como célula muda

## A fronteira

- [x] Uma marca visível entre o dia 7 e o dia 8, que a pessoa consiga interpretar
      sem saber o que é ICON ou ECMWF
      — a marca é uma **borda esquerda sólida e mais grossa na primeira célula
      do horizonte longo**, e não uma faixa atravessando a grade. Numa grade de
      sete colunas a fronteira cai no meio de uma linha na maioria das semanas,
      onde uma faixa horizontal não teria por onde passar
- [x] Um texto curto explicando que dali em diante a previsão é menos precisa.
      **Não pode parecer erro de carregamento** — é o risco concreto: uma metade
      da grade com menos informação que a outra lê como falha se nada disser o
      contrário
- [x] A explicação diz que a fonte muda e a confiança cai. Não precisa nomear os
      modelos; precisa não mentir

## Estados

- [x] Sem cidade escolhida: a instrução de buscar, como as outras páginas fazem
- [x] Carregando
- [x] Erro da previsão, declarado — não uma grade vazia que parece "sem tempo"
- [x] Trocar de cidade recarrega a grade
- [x] O rodapé de atribuição, pela função de atribuição

## Registro da rota

- [x] Entrar em `CONSTRUIDAS` em `App.tsx`, deixando de cair no `PaginaVazia`
- [x] Busca própria no componente, com o padrão de chave carimbada que
      `Tendencia.tsx` estabeleceu (`AbortController`, chave comparada no
      resultado). Não inventar um segundo padrão de fetch

## Comments

### Revisão (`/code-review`), e o que ela mudou

Quatro achados viraram correção, e todos foram encontrados **depois** de a
página já renderizar certo — o que é o registro de que rodar a página não
substitui a revisão, e vice-versa.

- **A célula era anunciada vazia.** O anúncio estava num `aria-label` no
  `<li>`, e `listitem` é um dos papéis em que a ARIA 1.2 **proíbe** nome vindo
  do autor. O Chrome computa o nome assim mesmo — a árvore de acessibilidade
  foi lida e o nome estava lá, que é justamente o que fazia o atributo passar
  na verificação —, mas todo o conteúdo visível da célula é `aria-hidden`, e o
  leitor que seguisse a regra anunciaria um item vazio. Virou um `<span>`
  `sr-only`, que é o padrão que `ResumoEmTexto` e a `TabelaComparativa` já usam
  neste repo
- **A nota da fronteira se contradizia com a grade.** Ela dizia "não falta
  dado", e o último dia da janela às vezes chega sem máxima nem mínima (medido
  em Berlim e no Cairo), com a célula imprimindo "sem dado" logo acima. Agora
  diz **"não é falha de carregamento"**, que é o que ela precisa negar e
  continua verdade na célula sem número
- **A atribuição era omitida por estado do painel.** Ela sumia quando o painel
  estava pronto, para não repetir a linha do rodapé do `Shell`. Só que
  `atribuicao()` já tem um ramo que muda o texto (`com_inmet`): no dia em que o
  horizonte creditasse algo que o painel não credita, a página mostraria o
  crédito do painel no lugar do seu. A comparação passou a ser **por valor** —
  se as frases divergirem, as duas aparecem
- **`DIAS_CURTOS` estava duplicado.** Os sete rótulos de coluna da grade eram
  uma cópia local dos que `formato.ts` já mantinha. Passou a ser exportado de
  lá: as colunas da grade **são** os dias que `diaDaSemanaCurto` devolve

Fora isso, a página foi verificada rodando contra o backend real, em São Paulo,
Berlim, Cairo e Wellington: dezesseis células, coluna inicial certa em cada
cidade (quarta em São Paulo, quinta em Berlim), fronteira no dia 8, tema claro
e escuro, e os estados sem cidade / carregando / erro. A aritmética de data foi
conferida em `TZ` de UTC+14 a UTC−11, incluindo ano bissexto e virada de ano.

### Uma pendência que **não** é desta fatia

`tests/test_trends.py::TestUv::test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela`
falha na suíte do backend, e já falhava antes desta fatia — nenhum arquivo de
backend foi tocado aqui. É um teste dependente de data: ele monta o cenário com
`date.today() + 1` e afirma que a ponta da janela difere desse dia, o que deixa
de valer conforme a data em que roda. Vale uma issue própria.
