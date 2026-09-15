# 35: Métricas avançadas e índice UV

**What to build:** a página Tendência ganha o segundo bloco: chuva acumulada,
variação da umidade do ar, vento com a direção dominante, e o índice UV ao longo
do dia. Fecha a página e o vocabulário do domínio.

**Blocked by:** 34

**Status:** done

Origem: [spec da página Tendência](30-pagina-tendencia.md).

## O índice UV não existe no passado

Medido contra o serviço real: `uv_index_max` é **aceito** pela API de arquivo e
devolve `null` para todos os dias, com unidade `"undefined"` e status `200` — não
é erro. A reanálise ERA5 não tem UV. Na API de previsão o mesmo campo devolve
valores normais.

Isso não é detalhe de implementação, é regra de produto: **o índice UV nunca
participa da comparação com o ano anterior, e nunca cobre 30 dias ou 6 meses.**
Ele vem da API de **previsão**, cobre a janela que ela oferece, e a interface diz
por quê.

Por isso `uv` é um bloco irmão de `serie` no payload, e não uma coluna dela: um
campo dentro de `serie` seria `null` em 173 dos 180 pontos, e todo consumidor
teria de saber disso. A forma do payload é que deve carregar o fato.

Um consumidor desatento plota uma linha reta no zero e ninguém nota — é a
armadilha central deste ticket.

- [ ] Gráfico da chuva distribuída ao longo da janela, que distingue "choveu todo
      dia um pouco" de "choveu tudo num dia só"
- [ ] Chuva acumulada em mm exibida ao lado da do ano anterior, para dizer se o
      período foi mais seco que o normal
- [ ] Gráfico da variação da umidade, com mínima e máxima exibidas: a amplitude
      importa, não só a média
- [ ] Gráfico da velocidade do vento ao longo da janela
- [ ] Direção dominante exibida em ponto cardeal, não só em graus
- [ ] `/api/trends` ganha o bloco `uv`, vindo da **API de previsão**, irmão de
      `serie` e nunca uma coluna dela
- [ ] O índice UV é classificado em faixas — baixo, moderado, alto, muito alto,
      extremo —, porque o número sozinho não diz o que significa
- [ ] A interface diz que o UV cobre só os próximos dias, em vez de exibir um
      gráfico vazio sem explicação
- [ ] Toda métrica exibe a sua unidade, lida do payload
- [ ] Teste de costura: `uv_index_max` vindo `null` em todos os dias do arquivo
      **não** vira uma série de nulos no payload
- [ ] `test_contract.py` ganha o caso do UV nulo no arquivo: se um dia a
      Open-Meteo passar a servir UV histórico, queremos saber, porque a regra de
      produto muda junto
- [ ] `CONTEXT.md` ganha **histórico climatológico** (a série de dias passados,
      sempre apresentada em comparação com o ano anterior — distinta de
      *previsão*, que é modelo do futuro) e **janela temporal** (o período que a
      pessoa escolhe, distinto dos *sete dias* fixos da previsão)
- [ ] O glossário registra que **Tendência** nomeia a página de análise, e que o
      *painel* homônimo da Visão geral — a curva horária de um dia — continua
      sendo outra coisa. Sem esse registro, "tendência" repete o problema que o
      glossário desfez com "painel"
- [ ] A descrição da página em `navegacao.tsx` é emendada: ela hoje promete "a
      tendência horária de temperatura e a precipitação em tela cheia", que
      deixa de ser o que a página é


## Comments

Entregue junto das demais fatias, numa implementação só da spec [30](30-pagina-tendencia.md) — ver os comentários de lá, inclusive os achados da revisão.
