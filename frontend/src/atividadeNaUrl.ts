/**
 * A atividade escolhida na pagina Calendario, lida e escrita nos parametros da
 * URL.
 *
 * ## A decisao: vai para a URL
 *
 * O precedente do app estava **dividido**, e a issue 06 pediu a decisao junto
 * da razao. A janela temporal da Tendencia viaja na URL (`janelaNaUrl.ts`); a
 * ordenacao da tabela de vizinhas **nao** viaja, porque "a ordem de uma tabela
 * de cinco linhas nao e algo que alguem compartilhe" (ADR 0006).
 *
 * A atividade fica do lado da janela, por dois criterios que o ADR 0006 usou
 * para mandar a ordenacao para o outro lado:
 *
 * 1. **Governa a pagina inteira.** Escolher "lavar roupa" repinta as sete
 *    celulas do horizonte curto — nao e uma preferencia de exibicao de um
 *    componente, e o que a pagina afirma.
 * 2. **E compartilhavel de verdade.** "Manda o link do calendario mostrando
 *    quando da para lavar roupa" e uma frase que alguem diz. "Manda o link da
 *    tabela ordenada por temperatura" nao e — e essa foi exatamente a distincao
 *    que o ADR 0006 registrou.
 *
 * Recarregar tambem nao perde a escolha, e trocar de cidade a preserva de graca:
 * a busca substitui os parametros da cidade e este fica, que e o comportamento
 * certo — quem compara duas cidades para lavar roupa quer continuar comparando
 * para lavar roupa.
 *
 * Nao vai para o `localStorage`, pela mesma regra de `janelaNaUrl.ts`: a URL ja
 * atende compartilhar e recarregar, e o armazenamento local continua restrito a
 * ultima cidade e ao tema.
 */

import type { Atividade } from "./api/types";

/** O parametro. Curto porque divide a URL com os seis da cidade. */
const PARAMETRO = "atividade";

/**
 * As quatro atividades, **so para validar o que vem na URL**.
 *
 * Nao exportada e nao renderizada por ninguem: ao contrario de `JANELAS`, que
 * desenha os botoes do `FiltroDeJanela`, o seletor de atividade monta as suas
 * opcoes a partir dos `rotulo` que o backend manda — quais sao e em que ordem
 * aparecem sao de la. Aqui a lista existe por um motivo so: `Atividade` e um
 * tipo, e tipo nao valida string em tempo de execucao. Um `?atividade=xyz`
 * digitado a mao precisa de algo concreto contra o que ser comparado.
 *
 * **Sem rotulo, de proposito.** Escrever "Lavar roupa" aqui criaria o segundo
 * mapa de `Atividade` para texto que o campo `rotulo` do backend existe para
 * evitar.
 *
 * O preco e que acrescentar a quinta atividade exige tocar aqui **e** no tipo.
 * E o mesmo preco que qualquer union do `types.ts` paga para ser validavel, e o
 * modo de falha e brando: uma atividade ausente desta lista nao some da
 * interface — ela so nao sobrevive a um recarregamento da pagina.
 */
const ATIVIDADES: Atividade[] = [
  "lavar_roupa",
  "esporte",
  "viagem",
  "plantio",
];

/**
 * A atividade dos parametros, ou `null` quando nenhuma foi escolhida.
 *
 * **`null` e um estado de verdade, e nao a ausencia de um padrao.** A pagina
 * abre sem atividade nenhuma, mostrando so previsao — e como a fatia 04 a
 * deixou, e e o estado inicial que a issue pede. Eleger uma das quatro como
 * padrao faria a grade abrir pintada por um criterio que ninguem escolheu, e
 * "lavar roupa" apareceria como se fosse a pergunta natural de quem abre um
 * calendario.
 *
 * Um valor invalido na URL cai no mesmo `null`, pela razao de `janelaNaUrl.ts`:
 * e indistinguivel de link truncado ou editado a mao, e melhor mostrar a grade
 * sem pintura que uma pagina de erro por causa de um parametro.
 */
export function atividadeDosParametros(
  parametros: URLSearchParams,
): Atividade | null {
  const bruta = parametros.get(PARAMETRO);
  return ATIVIDADES.some((atividade) => atividade === bruta)
    ? (bruta as Atividade)
    : null;
}

/**
 * Os parametros com a atividade trocada, preservando os da cidade.
 *
 * `null` **remove** o parametro em vez de escrever um valor vazio: uma URL sem
 * ele ja significa "sem atividade escolhida", e `?atividade=` seria um segundo
 * jeito de dizer a mesma coisa — o mesmo motivo pelo qual `comJanela` omite a
 * janela padrao.
 */
export function comAtividade(
  parametros: URLSearchParams,
  atividade: Atividade | null,
): URLSearchParams {
  const proximos = new URLSearchParams(parametros);
  if (atividade === null) proximos.delete(PARAMETRO);
  else proximos.set(PARAMETRO, atividade);
  return proximos;
}
