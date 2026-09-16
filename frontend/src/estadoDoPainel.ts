/**
 * O estado do painel, e como uma pagina o le.
 *
 * Mora fora do `Shell` porque um arquivo que exporta componente e hook ao
 * mesmo tempo quebra o fast refresh do Vite — e porque o tipo e o contrato
 * entre o layout e as seis paginas, nao detalhe de um deles.
 */

import { useOutletContext } from "react-router";
import type { WeatherResponse } from "./api/types";

/**
 * O painel e sempre um destes cinco estados, nunca uma combinacao deles.
 * Um unico estado impede o par invalido "carregando com erro" que tres
 * booleanos independentes permitiriam.
 */
export type Estado =
  /**
   * O app ainda nao sabe se vai abrir com uma cidade.
   *
   * Nao e o mesmo que vazio, e a diferenca e visivel: sem este estado o
   * primeiro quadro seria "Busque uma cidade", logo substituido pelo painel
   * aparecendo sozinho. Quando nao ha permissao nem cidade lembrada ele dura
   * um quadro e ninguem o ve.
   */
  | { tipo: "decidindo" }
  | { tipo: "vazio" }
  | { tipo: "carregando" }
  | { tipo: "pronto"; painel: WeatherResponse }
  | { tipo: "erro"; mensagem: string };

export type ContextoDoPainel = { estado: Estado };

/**
 * O painel corrente, para a pagina que o consome.
 *
 * O contexto do outlet cresceu — ele carrega a conta tambem, ver
 * `estadoDaConta.ts` —, e este hook continua devolvendo so o painel. E de
 * proposito: as cinco paginas que nao sabem que existe conta nao passam a
 * saber, e o tipo estreito e o que impede uma delas de ler `conta` sem
 * querer.
 */
export function usePainel(): ContextoDoPainel {
  return useOutletContext<ContextoDoPainel>();
}
