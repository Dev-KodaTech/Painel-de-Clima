# 32: Comparação com o ano anterior

**What to build:** o histórico passa a vir acompanhado do **mesmo período do ano
anterior**. A resposta de `/api/trends` ganha uma segunda série, na mesma forma
da primeira, cobrindo as mesmas datas de calendário um ano atrás — é ela que
permite responder "este período está fora do normal?".

Quando o arquivo não cobre o período do ano anterior, a segunda série vem vazia
e a atual continua íntegra.

**Blocked by:** 31

**Status:** done

Origem: [spec da página Tendência](30-pagina-tendencia.md).

## Contexto

São **duas chamadas ao arquivo, não uma**: a API aceita um único intervalo por
requisição, e pedir de setembro do ano passado até hoje traria 365 dias para usar
60.

Este ticket também traz a separação do cache em duas famílias. O cache do
processo hoje guarda **uma** instância; passa a guardar duas, com TTLs
diferentes. A mudança é pequena — o `Cache` já recebe o TTL no construtor, e a
mecânica do TTL, já testada, não muda.

- [ ] `/api/trends` devolve `comparacao`, na mesma forma de `serie`, para o
      mesmo período do ano anterior
- [ ] A comparação usa a **mesma data de calendário**, não o mesmo dia da
      semana: setembro se compara com setembro
- [ ] Funciona igual no hemisfério sul — "mesmo período do ano anterior" não
      depende de estação
- [ ] Arquivo sem dado para o ano anterior devolve `comparacao` vazia e a série
      atual íntegra. Não é erro: é o caminho normal para uma cidade cujo arquivo
      começa depois
- [ ] O cache do processo passa a ter duas famílias de chave com TTLs distintos:
      a janela atual mantém os 10 minutos do painel, porque o dia corrente ainda
      muda; a janela do ano anterior ganha TTL longo (24 h), porque **o passado
      não muda** e reconsultá-lo a cada 10 minutos gastaria cota para receber os
      mesmos números
- [ ] Nenhum teste existente do cache precisa mudar de comportamento
- [ ] Testes de costura: a janela do ano anterior cobre as datas corretas para
      as três janelas; arquivo vazio no ano anterior devolve `comparacao` vazia
      sem derrubar a atual
- [ ] `test_cache_http.py` ganha: janelas diferentes da mesma cidade são
      chamadas externas diferentes, e o dado do ano anterior sobrevive ao TTL
      curto — com o relógio injetado do `conftest.py`, nunca esperando de
      verdade


## Comments

Entregue junto das demais fatias, numa implementação só da spec [30](30-pagina-tendencia.md) — ver os comentários de lá, inclusive os achados da revisão.
