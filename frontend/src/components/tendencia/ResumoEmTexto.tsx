/**
 * O resumo em texto de um grafico, para quem usa leitor de tela.
 *
 * Uma serie de 180 pontos nao se le ponto a ponto, e um `<svg>` sem alternativa
 * e um buraco na pagina. A frase diz o que a curva mostra — extremos, media,
 * tendencia —, que e o que quem enxerga extrai dela de relance.
 *
 * `sr-only` e nao `aria-label` no grafico: o Recharts monta uma arvore de SVG
 * propria, e um rotulo nela competiria com os elementos que ele mesmo gera.
 */

import type { ReactNode } from "react";

export function ResumoEmTexto({ children }: { children: ReactNode }) {
  return <p className="sr-only">{children}</p>;
}
