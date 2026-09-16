/**
 * A janela temporal da pagina Tendencia, lida e escrita nos parametros da URL.
 *
 * Mora na URL pela mesma razao que a cidade (`docs/adr/0002-cidade-na-url.md`):
 * assim "Berlim, ultimos 6 meses" e um link que abre exatamente isso, e
 * recarregar nao perde a escolha. Trocar de cidade tambem a preserva de graca —
 * a busca substitui os parametros da cidade e este fica.
 *
 * Nao vai para o `localStorage`: a URL ja atende compartilhar e recarregar, e o
 * armazenamento continua restrito a ultima cidade e ao tema.
 *
 * A restricao **segue valendo** depois dos locais salvos, e nao foi
 * abandonada por eles: um local salvo pertence a uma conta e vive no banco,
 * que e o que o faz acompanhar a pessoa entre navegadores — justamente o que
 * o `localStorage` nao faria. Ver ADR 0004.
 */

import type { Janela } from "./api/types";

/** O parametro. Curto porque divide a URL com os seis da cidade. */
const PARAMETRO = "janela";

/** A janela com que a pagina abre. Sete dias: o recorte que o painel ja usa. */
export const JANELA_PADRAO: Janela = "7d";

/**
 * As tres janelas e os seus rotulos, na ordem em que o filtro as mostra.
 *
 * Uma lista so, como `PAGINAS`: o filtro desenha os botoes a partir dela e a
 * validacao abaixo a usa como conjunto de valores aceitos.
 */
export const JANELAS: { valor: Janela; rotulo: string }[] = [
  { valor: "7d", rotulo: "7 dias" },
  { valor: "30d", rotulo: "30 dias" },
  { valor: "6m", rotulo: "6 meses" },
];

/**
 * A janela dos parametros, ou a padrao.
 *
 * Um valor invalido na URL cai na padrao em vez de virar erro: e indistinguivel
 * de link truncado ou editado a mao, e o backend recusaria a requisicao com 422
 * — melhor mostrar sete dias que uma pagina de erro por causa de um parametro.
 */
export function janelaDosParametros(parametros: URLSearchParams): Janela {
  const bruta = parametros.get(PARAMETRO);
  return JANELAS.some((janela) => janela.valor === bruta)
    ? (bruta as Janela)
    : JANELA_PADRAO;
}

/**
 * Os parametros com a janela trocada, preservando os da cidade.
 *
 * A janela padrao **sai** da URL em vez de ser escrita: uma URL sem o parametro
 * ja significa sete dias, e escreve-lo faria dois links diferentes abrirem a
 * mesma pagina.
 */
export function comJanela(
  parametros: URLSearchParams,
  janela: Janela,
): URLSearchParams {
  const proximos = new URLSearchParams(parametros);
  if (janela === JANELA_PADRAO) proximos.delete(PARAMETRO);
  else proximos.set(PARAMETRO, janela);
  return proximos;
}
