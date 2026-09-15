# 31: `/api/trends` com a janela atual

**What to build:** o backend passa a servir o histórico climatológico de uma
cidade para uma janela temporal escolhida. Dada uma coordenada e uma janela de 7
dias, 30 dias ou 6 meses, a resposta traz um ponto por dia do período — máxima,
mínima, chuva em mm, umidade média, velocidade máxima do vento e direção
dominante em graus —, o intervalo de datas que o período cobre, as unidades e a
atribuição.

Verificável por `curl` e pelos testes de costura: nenhuma tela muda ainda.

**Blocked by:** None (can start immediately)

**Status:** done

Origem: [spec da página Tendência](30-pagina-tendencia.md).

## Contexto

O backend conhece hoje **um** host da Open-Meteo, o de previsão. Este ticket
acrescenta o segundo — `archive-api.open-meteo.com`, a reanálise ERA5 —, que é
de onde vem todo o passado. Os dois são Open-Meteo e CC-BY 4.0, então a string
de atribuição já existente continua válida e não muda.

O arquivo **cobre até o dia corrente** (medido: consulta em 2026-09-15 devolveu
dado para 2026-09-15). Não há vão entre o fim do arquivo e o início da previsão,
e a janela atual sai inteira do arquivo — sem costura entre as duas APIs.

Sem comparação com o ano anterior (ticket 32), sem resumo (ticket 33) e sem
índice UV (ticket 35).

- [ ] `GET /api/trends` aceita `latitude`, `longitude` e `janela`, e devolve
      `periodo`, `serie`, `units` e `attribution`
- [ ] `janela` é um conjunto fechado — `7d`, `30d`, `6m` — validado como
      `Literal` na borda, do mesmo jeito que `Alerta.kind` já é. Valor fora do
      conjunto é `422` pelo validador, sem código nosso: entrada livre viraria
      aritmética de data arbitrária, e `6000d` é um pedido de dezesseis anos à
      API externa
- [ ] `periodo` carrega as datas de início e fim já resolvidas, para que a
      interface não recalcule datas nem descubra sozinha que "30 dias" termina
      ontem
- [ ] Cada ponto de `serie` traz data, máxima, mínima, chuva em mm, umidade
      média, vento máximo e direção dominante em graus
- [ ] `units` ganha `humidity` (`%`); o índice UV não tem unidade e entra no
      ticket 35. Como no painel, a unidade viaja no payload para que a interface
      nunca a tenha escrita em código
- [ ] O cliente da API externa continua sendo o **único** lugar que conhece o
      formato da Open-Meteo, agora com dois hosts
- [ ] A resposta é cacheada por coordenada arredondada **e janela**: duas
      janelas da mesma cidade são consultas diferentes e não podem compartilhar
      chave
- [ ] Série incompleta devolve os dias que existem, não erro
- [ ] API externa fora do ar vira `503` com mensagem legível, como nos dois
      endpoints existentes
- [ ] Testes de costura HTTP com `TestClient` + `respx`, irmãos de
      `test_weather.py`, com fixtures gravadas do serviço real: as três janelas
      produzem os intervalos corretos, janela inválida é `422`, série curta
      devolve o que existe, indisponibilidade vira `503`, e o payload traz um
      bloco por parte da página
- [ ] `test_contract.py` ganha um caso para o arquivo, no mesmo estilo dos
      existentes: verifica presença de campo, nunca valor


## Comments

Entregue junto das demais fatias, numa implementação só da spec [30](30-pagina-tendencia.md) — ver os comentários de lá, inclusive os achados da revisão.
