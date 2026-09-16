# 02: `/api/condicoes` por dia, e a página

Status: ready-for-agent

**What to build:** o endpoint que devolve **um item por dia que dispara**, e a
página Condições com a seção de condições previstas. A seção de alertas oficiais
é a fatia 03; esta entrega a página funcionando com uma seção só.

Hoje `derivar()` colapsa todos os dias de uma categoria num card mais
`also_days: int`. O painel da Visão geral quer esse colapso — dois cards, altura
fixa. A página quer o contrário: a semana de Wellington são cinco dias de vento,
com data e rajada de cada um, não "(+4 dias)".

Os limiares e as regras são os mesmos. O que muda é só o colapso: `also_days`
sempre foi a admissão de que o dado por dia existe e está sendo descartado.

**Blocked by:** 01

- [ ] `GET /api/condicoes?latitude&longitude` devolve um item por dia que dispara,
      em ordem cronológica
- [ ] Um dia que dispara duas categorias produz dois itens
- [ ] Sem teto de quantidade e sem dedup por categoria — o `MAXIMO_DE_CARDS`
      continua valendo só para o painel
- [ ] Os limiares são os mesmos de `condicoes.py`, importados e não reescritos:
      um segundo conjunto de constantes faria o mesmo dia ser severo numa página e
      calmo na outra
- [ ] O endpoint reaproveita o cache de 10 minutos da previsão, sem chamada extra
      à API externa quando `/api/weather` já populou a entrada
- [ ] A página é buscada nela mesma, não no `Shell`, pela regra do
      [ADR 0003](../../../docs/adr/0003-historico-e-buscado-na-pagina.md)
- [ ] A página trata os cinco estados do painel por conta própria, como
      `VisaoGeral` e `CidadesVizinhas` fazem
- [ ] Cada item mostra dia, categoria e o valor que disparou
- [ ] Cada item traz o rótulo de proveniência "derivado da previsão" — obrigatório
      pelo ADR 0001 e reafirmado pelo ADR 0007, não removível por layout
- [ ] Semana sem nenhuma condição mostra mensagem clara, não lista vazia
- [ ] A página entra em `CONSTRUIDAS` no `App.tsx`
- [ ] O título da página e a frase em `navegacao.tsx` passam a descrever o que a
      página entrega — a frase atual promete o que a fatia 01 mostrou não existir,
      e a regra do [ADR 0006](../../../docs/adr/0006-vizinhas-e-comparacao-nao-lista-longa.md)
      exige que ela mude junto
- [ ] A página passa a se chamar **Condições**, não "Condições previstas"
