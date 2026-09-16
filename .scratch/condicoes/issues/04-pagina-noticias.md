# 04: Página Notícias por RSS agregado

Status: ready-for-agent

**What to build:** a oitava página — notícias de clima e meio ambiente, agregadas
de três feeds RSS públicos no backend.

Por que RSS e não uma API de notícias, com os números da verificação:
[ADR 0009](../../../docs/adr/0009-noticias-por-rss-nao-por-api.md). Resumo: dos
cinco níveis gratuitos avaliados, quatro proíbem produção ou uso comercial, e o
quinto não tem filtro regional fora do plano corporativo.

**Blocked by:** None (independente das fatias 01-03)

## Backend

- [ ] Agregador de RSS em módulo próprio, único lugar que conhece o formato dos
      feeds
- [ ] Três feeds: Agência Brasil meio-ambiente
      (`https://agenciabrasil.ebc.com.br/rss/meio-ambiente/feed.xml`),
      Observatório do Clima (`https://www.oc.eco.br/feed/`) e Revista Pesquisa
      FAPESP (`https://revistapesquisa.fapesp.br/feed/`)
- [ ] `GET /api/noticias` devolve os itens agregados em ordem cronológica
      decrescente, cada um com título, veículo, data, link e resumo
- [ ] **Um feed indisponível não derruba a resposta**: o agregador ignora o que
      falhou e devolve o resto
- [ ] Todos os feeds fora do ar é estado distinto de "nenhuma notícia", e a
      interface os distingue
- [ ] Cache — as notícias mudam em escala de horas
- [ ] Sem filtro regional: as notícias são nacionais e apresentadas como tais
- [ ] A atribuição do endpoint nomeia os veículos

## Frontend

- [ ] Página nova em `navegacao.tsx`, com ícone e a frase descrevendo o que
      entrega
- [ ] Registrada em `CONSTRUIDAS` no `App.tsx`
- [ ] Lista com título, veículo, data e link para o site do veículo
- [ ] O veículo é sempre visível: a licença pede crédito, e numa lista que mistura
      agência pública, ONG e revista científica quem publicou é parte da
      informação
- [ ] A página não depende da cidade escolhida — é a única que não depende, e não
      deve pedir que se busque uma
- [ ] Links abrem no site do veículo
- [ ] Estados de carregamento e de falha
- [ ] Os comentários que dizem "as seis paginas" passam a dizer oito — a contagem
      já estava defasada antes desta feature (`navegacao.tsx` lista sete), e está
      em `estadoDoPainel.ts`, `estadoDaConta.ts`, `navegacao.tsx` (duas vezes),
      `BarraLateral.tsx` e `Tendencia.tsx`

## Testes

- [ ] Fixtures golden dos três feeds, com `respx`
- [ ] Caso de um feed falhando e os outros dois respondendo
- [ ] Caso de todos falhando
- [ ] Feed com XML malformado não derruba o agregador
- [ ] Teste de contrato marcado `contract` para os três feeds
