# 28: Barra lateral, seis páginas e os ícones do cabeçalho

**What to build:** a barra lateral esquerda do design vira navegação de verdade
— seis páginas roteáveis —, e o cabeçalho ganha os elementos que faltavam.

**Blocked by:** —

**Status:** resolved

Reverte uma decisão da spec. O *Out of Scope* dizia: *"A barra lateral tem sete
ícones no design, mas existe uma página só; permanecem decorativos."* Passam a
existir seis páginas, e os ícones passam a navegar. A spec foi emendada junto
com este ticket.

Nenhuma das seis páginas é inventada: cada uma corresponde a um painel que já
existe e que hoje é exibido truncado dentro de um cartão do grid.

| Rota | Página | Dado |
|---|---|---|
| `/` | Visão geral | o grid de nove painéis |
| `/tendencia` | Tendência | `hourly` + precipitação em tela cheia |
| `/vizinhas` | Cidades vizinhas | `nearby` completo |
| `/condicoes` | Condições previstas | `alerts` sem o limite de dois cards |
| `/semana` | Sete dias | `daily` expandido |
| `/ajustes` | Ajustes | nada ainda |

**Este ticket entrega as páginas vazias.** Só a Visão geral tem conteúdo — o
grid que já existe, movido para lá. As outras cinco levam título e uma frase
nomeando o que vai entrar. Preencher cada uma é ticket próprio.

## A construir

- [x] `react-router` 8.x, modo declarativo. `BrowserRouter` em `main.tsx`
- [x] `Shell` como rota de layout: segura sidebar, cabeçalho, busca e a
      requisição do painel, e renderiza `<Outlet />`
- [x] A cidade escolhida mora em `useSearchParams`, não em `useState` — ver
      [ADR 0002](../../../docs/adr/0002-cidade-na-url.md). Os parâmetros são
      `lat`, `lon`, `name`, `cc`, `country`, `admin1`: `/api/weather` exige
      `country_code` e usa os outros para montar o `location`
- [x] Shell de grid `64px 1fr` dentro do container de 1180px que já existe.
      Sidebar como cartão flutuante, `sticky`, altura da viewport — sem isso as
      cinco páginas vazias exibem uma barra atrofiada
- [x] Marca no topo da sidebar linkando para `/`, sem destaque de ativo
- [x] Seis ícones de navegação com `aria-label` + `title`: sem rótulo visível
      eles são mudos para teclado e leitor de tela
- [x] Ícone de saída no rodapé da sidebar como decoração inerte
- [x] Cabeçalho: data por extenso, toggle sol/lua, envelope, sino e avatar
- [x] Busca nas cinco páginas de clima, **ausente em Ajustes**, com altura fixa
      do cabeçalho para o conteúdo não pular
- [x] Rota `*`: página de erro mínima com link de volta
- [x] As cinco páginas vazias: título + uma frase do que vai entrar

## O que fica decorativo, e por quê

Toggle sol/lua, envelope, sino, avatar e o ícone de saída não têm
funcionalidade por trás — modo escuro está fora de escopo e não há cadastro
ainda. Vão como decoração inerte (`aria-hidden`), **nunca como `<button>`**: um
botão que aceita o clique e não responde promete o que não cumpre. O avatar usa
silhueta neutra, sem nome inventado.

O ícone de saída segura o lugar no rodapé da sidebar: deixá-lo de fora obrigaria
a redesenhar a base da barra quando o cadastro chegar, em vez de trocar um
`div` por um `button`.

## O que não muda

- Os nove painéis da Visão geral: mesmos componentes, mesmo grid de três faixas
- O contrato da API: nenhum endpoint novo, nenhum parâmetro novo
- Modo escuro continua fora de escopo. O toggle é enfeite, não interruptor
  — **revertido pelo [ticket 29](29-cidade-inicial-e-tema.md)**, que entrou no
  mesmo commit e tornou o toggle um `<button>` de verdade. As duas menções ao
  toggle como decoração inerte acima valem para o desenho original deste
  ticket, não para o código de hoje.

## Comments

Entregue no commit `308d78b`, que escreveu e implementou este ticket de uma vez
— por isso o `Status:` e as marcacoes so foram corrigidos agora. Os onze itens
da lista estao no codigo; a revisao de dois eixos rodou depois, sobre
`7698517...HEAD`, e esta abaixo.

Notas do que a implementacao decidiu e o ticket nao previa:

- **A lista de paginas virou dado** (`src/navegacao.tsx`). A barra lateral
  desenha os icones a partir dela e o `App` declara as rotas a partir dela.
  Cinco arquivos de pagina vazia quase identicos seriam cinco lugares para a
  navegacao e as rotas discordarem.
- **Cada link preserva os parametros de busca.** Sem isso trocar de pagina
  descartaria a cidade — que e justamente o que mora na URL — e a pagina de
  destino abriria vazia.
- **`end` no `NavLink` da raiz**: `/` e prefixo de todos os outros caminhos, e
  sem ele o icone de grade ficaria permanentemente ativo.
- **A chave do efeito e `parametros.toString()`**, e nao o objeto da cidade:
  uma cidade reconstruida a cada render nunca seria igual a anterior e o efeito
  entraria em laco. E e o texto que da a propriedade que o ticket pede — trocar
  de pagina mantendo a cidade nao o altera, e nenhuma requisicao e refeita.
- **Os quatro estados do painel sao tratados na Visao geral, nao no `Shell`.**
  Se o Shell os tratasse, renderizaria "busque uma cidade" no lugar da pagina, e
  as cinco paginas vazias nunca chegariam a mostrar o que sao.
- **`min-w-0` na coluna de conteudo**: sem isso ela cresce ate caber o seu maior
  filho — o grafico da tendencia — e estoura o container de 1180 px.

### Achados da revisao

Aplicado:

- **README desatualizado no mesmo diff que o criou.** Dizia que o toggle
  sol/lua era decoracao inerte e que "nao ha modo escuro", quatro linhas acima
  da secao "Cidade inicial e tema", que descreve o tema escuro funcionando. O
  toggle saiu da lista de cromo inerte. De quebra, o link de exemplo trazia
  quatro dos seis parametros, logo abaixo da frase que explica por que sao
  seis; agora traz os seis.

Registrado, nao aplicado:

- **`painel` voltou a nomear a resposta da API.** O `CONTEXT.md` escrito nesta
  mesma serie de commits diz: "Ficou sendo so o cartao. A resposta da API nao
  tem termo de dominio — e `WeatherResponse` no codigo e nada mais." Mas
  `estadoDoPainel.ts`, `ContextoDoPainel`, `usePainel()`, `CidadeDoPainel` e
  `estado.painel` nomeiam com ela exatamente a resposta inteira. Achado
  legitimo. Nao corrigido aqui porque `buscarPainel` e `ErroDoPainel` ja
  usavam o termo assim antes deste ticket: uma renomeacao parcial deixaria o
  vocabulario pior do que esta. E ticket de vocabulario proprio, como o 27 foi
  para *vizinha*.
- **A busca aparece na pagina de erro.** `mostrarBusca` e um teste negativo
  (`pathname !== CAMINHO_SEM_BUSCA`), e a rota `*` mora dentro do `Shell`. A
  pagina de erro nao e uma das cinco paginas de clima, entao estritamente nao
  deveria te-la — mas buscar uma cidade dali e saida util de um link quebrado,
  e o ticket nao diz nada sobre o cabecalho da rota `*`.
- **`Shell` e o unico nome de componente em ingles** entre `Cabecalho`,
  `BarraLateral` e `PaginaVazia`, e nao consta do glossario.
- **`Shell.tsx` muda por varios motivos** — rota, requisicao, deteccao inicial,
  armazenamento, derivacao de estado e layout — e reconcilia tres unioes
  marcadas (`Inicial`, `Resultado`, `Estado`) num ternario aninhado de cinco
  ramos. Candidato a divisao quando a proxima pagina de verdade chegar.

Descartado:

- **"`country` e `admin1` deveriam ser obrigatorios na URL, como diz o ADR
  0002."** Levantado pelos dois eixos, e errado nos dois. O backend declara
  `country: str = ""` **de proposito**: a chave `country` some da resposta do
  geocoding para territorios e regioes especiais — Papeete, Noumea, Hong Kong,
  Macau, Saint-Denis —, e exigi-la devolvia `422`, deixando essas cidades sem
  painel algum (ver ticket 24). Tornar o parametro obrigatorio em
  `cidadeNaUrl.ts` reintroduziria exatamente essa regressao. A frase do ADR e
  justificativa de por que os seis parametros viajam juntos, nao exigencia de
  que os seis estejam sempre presentes.
