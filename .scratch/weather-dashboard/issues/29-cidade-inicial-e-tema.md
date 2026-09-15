# 29: Cidade inicial automática e tema escuro

**What to build:** o painel abre já preenchido quando dá para saber qual cidade
mostrar, e o toggle sol/lua do cabeçalho passa a funcionar.

**Blocked by:** —

**Status:** ready-for-agent

Reverte duas decisões da spec, por motivos diferentes.

**Modo escuro** estava no *Out of Scope* porque "dobraria o trabalho de estilo
dos nove painéis". Isso era estimativa feita antes de existir código. Medido no
código atual: 25× `text-ink-2`, 17× `text-ink-3`, 12× `shadow-card`, 10×
`bg-card`, e os SVGs dos gráficos já usam `var(--color-brand)` e
`var(--color-line)`. Há 5 `text-white` no projeto, 4 deles sobre `bg-brand`,
onde continuam brancos nos dois temas. O Tailwind v4 emite
`.bg-card { background-color: var(--color-card) }` — a utilitária aponta para a
variável, não para um hex. **Redefinir as variáveis vira o tema inteiro sem
tocar em componente nenhum.**

**Persistência** ganha uma exceção estreita: última cidade e escolha de tema.
Favoritos e histórico continuam fora.

A regra de **não pedir localização no carregamento** não é revertida — ela
continua valendo por inteiro.

## Cidade inicial

Vocabulário novo em `CONTEXT.md`: **cidade inicial** (o slot) e **cidade
detectada** (a resolvida a partir da coordenada). O navegador devolve
*coordenada*, nunca cidade — quem resolve é `cidade_na_coordenada`, no backend.

- [x] No carregamento, `navigator.permissions.query({ name: "geolocation" })`.
      **Só com `state === "granted"`** chamar `getCurrentPosition`. Nunca
      disparar um pop-up novo: o pedido automático no primeiro acesso é negado
      por reflexo e o browser lembra a negação
- [x] Precedência: **cidade detectada → última cidade → estado vazio**.
      Conceder a permissão *é* a pessoa pedindo que usemos a localização dela
- [x] Toda falha cai para o degrau seguinte **em silêncio**: timeout, coordenada
      a mais de 50 km de qualquer cidade (o backend devolve lista vazia), ou
      browser sem Permissions API. Negar não é falha e não merece mensagem
- [x] A cidade inicial entra na URL com `replace` — o ADR 0002 continua valendo,
      e sem `replace` entrar no app já deixaria você a um Voltar de sair dele
- [x] Última cidade em `localStorage`, guardando **qualquer** cidade que o
      painel carregou, sem distinguir origem. Leitura validada: armazenamento
      pode conter formato velho
- [x] Quinto estado `decidindo`: nada na tela até o app saber se vai carregar.
      Sem ele, "Busque uma cidade" pisca antes do painel automático aparecer
- [x] A detecção roda **uma vez por carregamento**, e não a cada render

## Tema

- [x] `:root[data-tema="escuro"]` redefinindo as variáveis do `@theme`.
      Nenhum componente muda
- [x] Toggle de dois estados. Inicial pelo `prefers-color-scheme`; o primeiro
      clique passa a mandar para sempre. Escolha em `localStorage`
- [x] `data-tema` carimbado por **script inline no `index.html`**, antes do
      primeiro paint. Com `useEffect`, quem usa escuro vê a página branca por
      100–300 ms em toda visita
- [x] No escuro o cartão fica mais claro que o fundo **e** ganha borda sutil. A
      sombra deixa de ser o que separa — sombra é invisível sobre escuro. Via
      `--shadow-card: 0 0 0 1px <linha>, ...`, que aproveita o `shadow-card` já
      presente em todo cartão
- [x] A pílula sol/lua **sai do bloco `aria-hidden`** e vira `<button>` de
      verdade, com rótulo dizendo a ação. Envelope, sino, avatar e o ícone de
      saída continuam inertes

## Também

- [x] A engrenagem da barra lateral virou uma estrela quase idêntica ao sol do
      cabeçalho. Redesenhar: aro grosso com dentes encostados e furo no meio —
      o que distingue de um sol é o raio destacado do centro

## A vigiar

`overcast-day.svg` usa cinzas `#6b7280`–`#9ca3af`. Sobre cartão escuro o
contraste fica baixo. Os demais Meteocons têm nuvens quase brancas
(`#deeafb`–`#f3f7fe`) e sol âmbar, que sobrevivem aos dois temas.
