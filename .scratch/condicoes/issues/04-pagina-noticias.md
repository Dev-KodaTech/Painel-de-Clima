# 04: Página Notícias por RSS agregado

Status: concluida

**What to build:** a oitava página — notícias de clima e meio ambiente, agregadas
de três feeds RSS públicos no backend.

Por que RSS e não uma API de notícias, com os números da verificação:
[ADR 0009](../../../docs/adr/0009-noticias-por-rss-nao-por-api.md). Resumo: dos
cinco níveis gratuitos avaliados, quatro proíbem produção ou uso comercial, e o
quinto não tem filtro regional fora do plano corporativo.

**Blocked by:** None (independente das fatias 01-03)

## Backend

- [x] Agregador de RSS em módulo próprio, único lugar que conhece o formato dos
      feeds
- [x] Três feeds: Agência Brasil meio-ambiente
      (`https://agenciabrasil.ebc.com.br/rss/meio-ambiente/feed.xml`),
      Observatório do Clima (`https://www.oc.eco.br/feed/`) e Revista Pesquisa
      FAPESP (`https://revistapesquisa.fapesp.br/feed/`)
- [x] `GET /api/noticias` devolve os itens agregados em ordem cronológica
      decrescente, cada um com título, veículo, data, link e resumo
- [x] **Um feed indisponível não derruba a resposta**: o agregador ignora o que
      falhou e devolve o resto
- [x] Todos os feeds fora do ar é estado distinto de "nenhuma notícia", e a
      interface os distingue
- [x] Cache — as notícias mudam em escala de horas
- [x] Sem filtro regional: as notícias são nacionais e apresentadas como tais
- [x] A atribuição do endpoint nomeia os veículos

## Frontend

- [x] Página nova em `navegacao.tsx`, com ícone e a frase descrevendo o que
      entrega
- [x] Registrada em `CONSTRUIDAS` no `App.tsx`
- [x] Lista com título, veículo, data e link para o site do veículo
- [x] O veículo é sempre visível: a licença pede crédito, e numa lista que mistura
      agência pública, ONG e revista científica quem publicou é parte da
      informação
- [x] A página não depende da cidade escolhida — é a única que não depende, e não
      deve pedir que se busque uma
- [x] Links abrem no site do veículo
- [x] Estados de carregamento e de falha
- [x] Os comentários que dizem "as seis paginas" passam a dizer oito — a contagem
      já estava defasada antes desta feature (`navegacao.tsx` lista sete), e está
      em `estadoDoPainel.ts`, `estadoDaConta.ts`, `navegacao.tsx` (duas vezes),
      `BarraLateral.tsx` e `Tendencia.tsx`

## Testes

- [x] Fixtures golden dos três feeds, com `respx`
- [x] Caso de um feed falhando e os outros dois respondendo
- [x] Caso de todos falhando
- [x] Feed com XML malformado não derruba o agregador
- [x] Teste de contrato marcado `contract` para os três feeds

## O que mudou em relação ao planejado

### Dois achados dos feeds reais

**O Observatório do Clima exige um `User-Agent` de formato específico.** O
CloudFront à frente do `oc.eco.br` responde **403** ao padrão do httpx, ao do
curl e até ao nome próprio da aplicação sem prefixo — o que passa é
`Mozilla/5.0 (compatible; Nome/Versão)`. Foi medido contra o serviço real, está
em `USER_AGENT` com a medição ao lado, e o ADR 0009 ganhou a seção "Sem chave,
mas não sem cabeçalho": a leitura natural do ADR original era "basta pedir o
feed", e não bastava. Sem isso, um dos três veículos nunca apareceria — e o
sintoma seria uma lista permanentemente curta, não um erro.

**O `description` dos três veículos é HTML, em três formatos diferentes.** A
Agência Brasil o manda duas vezes escapado, atrás de um logotipo e de um `<p>`
de centralização, com o texto útil dentro de um `<strong>` a ~400 caracteres do
início; os outros dois mandam CDATA com o rodapé do WordPress ("O post … apareceu
primeiro em …") colado no fim de toda matéria. A ordem das operações de limpeza
está em `_resumo`, e as fixtures golden preservam as três armadilhas. Junto: o
`guid` da Agência Brasil **não é URL**, o que torna tentador — e errado — usá-lo
como reserva do `<link>`.

### A contagem de páginas

A ficha diz que `navegacao.tsx` "lista sete". **Listava seis**: Locais salvos
nunca entrou. Com Notícias são sete entradas, e o `CONTEXT.md` conta oito porque
inclui Locais salvos, que ainda não existe. Os comentários passaram a dizer oito
— que é o app do glossário —, e o cabeçalho de `navegacao.tsx` registra a
diferença para quem for conferir. Em `estadoDaConta.ts` o número é **sete**, não
oito, porque a frase ali é "as outras páginas funcionam sem conta" e Locais
salvos é justamente a que não funciona.

### Decisões não pedidas pela ficha

- **TTL próprio de meia hora** (`TTL_DAS_NOTICIAS_SEGUNDOS`), e uma terceira
  família em `cache_do_processo`. A ficha pede cache "em escala de horas"; o
  cache existente é o de dez minutos da previsão, calibrado noutro ciclo.
  Meia hora é o teto da matéria urgente — uma enchente em curso.
- **`MAXIMO_DE_ITENS = 30`**: os feeds trazem 10, 10 e 30 itens, e sem teto a
  FAPESP dominaria metade da lista. O corte é depois da ordenação.
- **A atribuição é vazia quando nenhum veículo responde**, e mora na página, não
  no rodapé do `Shell` — aquele só aparece com painel pronto, isto é, com cidade
  escolhida, e esta é a página que não exige nenhuma. Sem isso o crédito que a
  licença pede não seria exibido.

## Verificação

Rodado contra os feeds reais: `uv run pytest -m contract -k noticias` passa
(3 casos — um por veículo, mais o agregado). A página foi aberta num browser e
conferida nos quatro estados (carregada, degradação parcial, sem notícias, tudo
fora do ar) e nos dois temas.

Suíte: **390 passed**. A falha de
`test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela` é pré-existente e não
relacionada — já registrada nas fichas 01 a 03, e reconfirmada com `git stash`
contra o código anterior a esta fatia. Frontend typecheca, linta e builda limpo.

### Revisão

Duas revisões (padrões e spec) apontaram, e foi corrigido: "feed" e "fonte" como
sinônimos proibidos pelo `CONTEXT.md` em texto de interface; um comentário novo
que dizia "seis paginas" — a string que a ficha pedia para eliminar; a atribuição
genérica que creditava quem não forneceu nada; `StatusDasNoticias` duplicado
entre serviço e modelo; helpers de teste copiados nos dois arquivos; e o TTL
acima, que era o defeito de fundo — os comentários diziam "horas" e o código
usava dez minutos.
