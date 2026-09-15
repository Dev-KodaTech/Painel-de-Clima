# O histórico climatológico é buscado na página, não no layout

O [ADR 0002](0002-cidade-na-url.md) pôs a requisição do painel na rota de
layout e **rejeitou explicitamente** cada página buscar o seu ao montar, por
refazer a requisição a cada troca de página. A página Tendência é a exceção a
essa decisão: ela busca o próprio histórico, no seu efeito, com o seu estado de
carregamento e de erro.

A inversão é deliberada e o motivo é o mesmo do ADR 0002, aplicado ao contrário.
Lá, o que se queria evitar era uma requisição que toda troca de página refaz.
Aqui, o layout buscando o histórico faria **as seis páginas** pagarem por ele:
o payload do painel tem ~3,5 KB e o histórico de 6 meses com duas séries dobra
isso, para dado que cinco das seis páginas nunca leem. A Visão geral esperaria
duas chamadas ao arquivo antes de pintar.

Daí também o endpoint ser próprio (`/api/trends`) e não um bloco a mais no
`/api/weather`.

## A regra, para a sétima página

Quem acrescentar a próxima página vai encontrar dois precedentes contraditórios
e precisa saber qual seguir:

> **Dado que várias páginas leem vai no layout; dado que só uma página lê vai
> nela.**

Está escrito aqui porque o código sozinho não conta isso — ele mostra os dois
padrões lado a lado, sem dizer o que separa um do outro.

## Consequences

Sair da Tendência e voltar **refaz a requisição**. É o custo que o ADR 0002
recusou a pagar, e aqui ele é aceito porque incide sobre uma página só.

Quem absorve é o cache do backend, não estado guardado no cliente: a volta é
instantânea porque a segunda consulta não gasta cota da API externa, com duas
famílias de TTL — 10 minutos para a janela atual, 24 h para a do ano anterior,
que não muda mais.

O layout deixa de ser o único lugar que busca. Essa é a fragilidade real da
decisão, e é ela que a regra acima existe para conter.
