/**
 * Rota desconhecida.
 *
 * Existe em vez de um redirecionamento silencioso para a raiz. Agora que a
 * cidade viaja na URL, os links sao compartilhaveis — e um link quebrado que
 * aterrissa na Visao geral faz quem o abriu achar que chegou no lugar certo.
 *
 * O link de volta preserva os parametros: a cidade sobrevive ao engano.
 */

import { Link, useLocation } from "react-router";

export function NaoEncontrada() {
  const { pathname, search } = useLocation();

  return (
    <section className="py-6">
      <h2 className="text-lg font-semibold">Pagina nao encontrada</h2>
      <p className="mt-2 max-w-prose text-[13px] text-ink-2">
        Nao existe nada em <code className="text-ink">{pathname}</code>. Confira
        o endereco ou volte para a{" "}
        <Link
          to={{ pathname: "/", search }}
          className="text-brand-text underline underline-offset-2"
        >
          visao geral
        </Link>
        .
      </p>
    </section>
  );
}
