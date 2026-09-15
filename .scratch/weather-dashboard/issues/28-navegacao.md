# 28: Barra lateral, seis páginas e os ícones do cabeçalho

**What to build:** a barra lateral esquerda do design vira navegação de verdade
— seis páginas roteáveis —, e o cabeçalho ganha os elementos que faltavam.

**Blocked by:** —

**Status:** ready-for-agent

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

- [ ] `react-router` 8.x, modo declarativo. `BrowserRouter` em `main.tsx`
- [ ] `Shell` como rota de layout: segura sidebar, cabeçalho, busca e a
      requisição do painel, e renderiza `<Outlet />`
- [ ] A cidade escolhida mora em `useSearchParams`, não em `useState` — ver
      [ADR 0002](../../../docs/adr/0002-cidade-na-url.md). Os parâmetros são
      `lat`, `lon`, `name`, `cc`, `country`, `admin1`: `/api/weather` exige
      `country_code` e usa os outros para montar o `location`
- [ ] Shell de grid `64px 1fr` dentro do container de 1180px que já existe.
      Sidebar como cartão flutuante, `sticky`, altura da viewport — sem isso as
      cinco páginas vazias exibem uma barra atrofiada
- [ ] Marca no topo da sidebar linkando para `/`, sem destaque de ativo
- [ ] Seis ícones de navegação com `aria-label` + `title`: sem rótulo visível
      eles são mudos para teclado e leitor de tela
- [ ] Ícone de saída no rodapé da sidebar como decoração inerte
- [ ] Cabeçalho: data por extenso, toggle sol/lua, envelope, sino e avatar
- [ ] Busca nas cinco páginas de clima, **ausente em Ajustes**, com altura fixa
      do cabeçalho para o conteúdo não pular
- [ ] Rota `*`: página de erro mínima com link de volta
- [ ] As cinco páginas vazias: título + uma frase do que vai entrar

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
