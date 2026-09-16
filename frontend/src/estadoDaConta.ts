/**
 * O estado da conta, e como uma pagina o le.
 *
 * Gemeo de `estadoDoPainel.ts`, e pelas mesmas duas razoes: um arquivo que
 * exporta componente e hook ao mesmo tempo quebra o fast refresh do Vite, e o
 * tipo e o contrato entre a rota de layout e as paginas, nao detalhe de um
 * deles.
 *
 * O que **nao** mora aqui e cookie nenhum. A sessao vive num cookie
 * `HttpOnly` que script algum le — nem este (ADR 0005). O que o frontend sabe
 * da sessao e o que `/api/quem-sou` respondeu: um e-mail, ou nada.
 */

import { useOutletContext } from "react-router";
import type { Conta } from "./api/types";
import type { Estado as EstadoDoPainel } from "./estadoDoPainel";

/**
 * A conta e sempre um destes tres estados.
 *
 * `consultando` existe pelo mesmo motivo que `decidindo` existe no painel: sem
 * ele, o primeiro quadro de toda visita seria "Entrar" no cabecalho — inclusive
 * para quem tem sessao valida —, trocado por "sair" um instante depois. Quem
 * recarrega a pagina veria a propria conta piscar de ausente para presente.
 *
 * Nao ha estado de erro. Se `/api/quem-sou` falhar, o app segue como visitante:
 * e o estado em que as outras seis paginas funcionam inteiras, e uma faixa
 * vermelha no topo por causa de uma consulta que so decide se o cabecalho
 * mostra um e-mail seria alarme desproporcional ao que se perdeu.
 */
export type EstadoDaConta =
  | { tipo: "consultando" }
  | { tipo: "visitante" }
  | { tipo: "entrada"; conta: Conta };

/**
 * O contexto do outlet: painel e conta, juntos.
 *
 * Um objeto so para os dois, e nao dois contextos, porque `useOutletContext`
 * devolve **um** valor por rota de layout — e ha uma. As paginas leem so o que
 * usam: `usePainel()` continua servindo quem nao sabe que existe conta.
 */
export type ContextoDoOutlet = {
  estado: EstadoDoPainel;
  conta: EstadoDaConta;
  /**
   * Guarda a conta recem-aberta, para o app nao reconsultar quem sou.
   *
   * Nao ha `aoSair` aqui, e a assimetria e proposital: quem sai e a barra
   * lateral, que recebe a funcao por prop do `Shell`. Nenhuma pagina sai, e
   * publicar no contexto uma funcao que ninguem chama seria oferecer uma porta
   * que existe so por simetria com a que se usa.
   */
  aoEntrar: (conta: Conta) => void;
};

/** A conta corrente, para a pagina ou componente que a consome. */
export function useConta(): ContextoDoOutlet {
  return useOutletContext<ContextoDoOutlet>();
}
