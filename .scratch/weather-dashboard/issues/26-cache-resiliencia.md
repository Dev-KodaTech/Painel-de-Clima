# 26: Cache e resiliência

**What to build:** o painel se comporta bem quando as coisas demoram ou falham: mostra que está carregando, explica de forma compreensível quando o serviço externo está fora do ar, e não refaz trabalho desnecessário. A origem dos dados fica visível na página.

**Blocked by:** 23, 25

**Status:** resolved

Passada final cobrindo todos os caminhos de dados de uma vez — por isso depende dos dois ramos (23 e 25) terem convergido.

Referência: [spec](../spec.md), "Módulos do backend" e "Further Notes".

- [x] Cache em memória, TTL de 10 min, chave por **coordenada arredondada**
- [x] Estado de carregamento visível durante as requisições
- [x] API externa fora do ar: mensagem compreensível, não stack trace
- [x] Cidade não encontrada: mensagem clara orientando a corrigir o texto
- [x] Rodapé de atribuição renderizado a partir do campo `attribution` do payload, nunca texto fixo no frontend
- [x] Teste: duas requisições iguais produzem **uma** chamada externa; após o TTL, duas. Relógio injetado, sem `sleep`
- [x] Teste: coordenadas próximas arredondam para a mesma chave de cache
- [x] Teste: falha da API externa vira erro tratado
- [x] **Um** teste de contrato marcado `contract`, **fora** da suíte padrão, batendo na API real e verificando apenas presença de campos — nunca valores

## Comments

Implementado. Notas do que a implementacao verificou ou mudou:

- **So as chamadas por coordenada sao cacheadas.** A busca por texto fica de
  fora de proposito: dispara a cada tecla, a chave seria o texto cru — "Ber",
  "Berl", "Berli" sao tres entradas para a mesma cidade — e o conjunto de
  chaves possiveis nao tem limite. E tambem a chamada barata, que nao arrasta
  previsao junto.
- **A chave arredonda a duas casas (~1,1 km).** Abaixo da celula de grade que a
  propria API usa, que ja devolve a coordenada arredondada em vez da pedida.
  Sem isso, `52.52437` e `52.5244` — a mesma Berlim vinda de duas candidatas
  com precisao diferente — seriam entradas distintas, e o cache erraria no caso
  que existe para servir.
- **O cache cobre as duas chamadas externas, nao so a cara.** A das vizinhas e
  cacheada pelo conjunto inteiro de coordenadas, sob prefixo proprio: a
  requisicao e uma so para todas, e a resposta so faz sentido inteira. Como a
  selecao de vizinhas e deterministica sobre um dataset fixo, a chave do
  conjunto repete tal qual na segunda consulta.
- **Falha da API nao e cacheada.** Guardar um erro por dez minutos prenderia o
  painel numa indisponibilidade passageira; o valor so e gravado depois de a
  busca retornar.
- **Sem trava entre requisicoes concorrentes pela mesma chave.** Duas consultas
  simultaneas a uma cidade fria fazem duas chamadas em vez de uma. Um lock por
  chave traria coordenacao e risco de deadlock para economizar uma requisicao
  de uma cota de 10.000 diarias.
- Os demais itens da lista ja estavam satisfeitos pelos tickets 21-25 (estado
  de carregamento, mensagens de erro, rodape a partir de `attribution`) e pelo
  12 (teste de contrato). Foram conferidos, nao reimplementados.

### Achados da revisao

Aplicados:

- **O cache guardava a corrotina, nao o resultado.** A primeira versao tinha um
  `obter` sincrono alem do assincrono, e o call site caiu no sincrono: o valor
  gravado era a corrotina de `_get`, e a segunda consulta morria com "cannot
  reuse already awaited coroutine". O sincrono nao tinha chamador na producao —
  existia so para os testes usarem, exercitando um caminho que a aplicacao
  nunca roda. Removido; sobrou um `obter` assincrono, que e o que a producao
  usa. A revisao apontou o metodo morto; o bug apareceu ao remove-lo.
- **O teste de cache nao exercitava a chamada das vizinhas.** Sem `lifespan` o
  dataset fica vazio, `nearby` sai vazio e a segunda chamada externa nunca
  acontece — as duas batem na mesma URL, entao `call_count == 1` parecia provar
  mais do que provava. Ha agora teste com o dataset carregado que conta as duas
  rotas separadamente (distinguidas por `forecast_days`), e foi ele que pegou o
  bug da corrotina.
- **O estado de processo mudou de lugar.** A instancia compartilhada morava em
  `services/open_meteo.py`, contra a regra que `dataset.py` enuncia: estado de
  processo mora fora dos servicos. Foi para `app/cache_do_processo.py`, o que
  tambem deu ao teste **um** ponto de troca em vez de dois — antes o conftest
  limpava uma instancia enquanto o teste de TTL substituia outra.
- `_Relogio` estava duplicado nos dois arquivos de teste; virou `Relogio` no
  `conftest.py`.

Descartado:

- A revisao notou que ha **cinco** testes de contrato onde o ticket pede "um".
  Ficam como estao: sao de antes deste ticket (12), estao fora da suite padrao,
  verificam presenca e nunca valor, e a intencao da spec — nao fazer a suite
  depender da rede — esta honrada. "Um" ali le-se como um arquivo, uma
  preocupacao.
- A revisao sugeriu tipar o `prefixo` de `chave_de_coordenada`, hoje uma string
  crua com dois valores possiveis. Procede como observacao, mas sao dois call
  sites no mesmo modulo; um tipo para eles seria cerimonia maior que o risco.
