/**
 * Uma pagina que ainda nao foi construida.
 *
 * Titulo e uma frase do que vai entrar ali. Sem cartao branco: a ausencia da
 * moldura e o que faz "ainda nao construida" ser visivel de longe, e nada
 * precisa ser desmontado quando a pagina de verdade chegar.
 *
 * Renderizar so o titulo seria pior — uma pagina vazia de proposito ficaria
 * indistinguivel de uma rota quebrada. Um esqueleto cinza seria pior ainda:
 * conteudo falso que alguem confunde com carregamento.
 *
 * Nao le o painel: enquanto a pagina nao usa dado nenhum, a frase e verdadeira
 * com ou sem cidade escolhida.
 */

import type { Pagina } from "../navegacao";

export function PaginaVazia({ pagina }: { pagina: Pagina }) {
  return (
    <section className="py-6">
      <h2 className="text-lg font-semibold">{pagina.titulo}</h2>
      <p className="mt-2 max-w-prose text-[13px] text-ink-2">{pagina.oQueVem}</p>
    </section>
  );
}
