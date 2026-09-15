/**
 * A caixa de um grafico: altura fixa e largura do container.
 *
 * `ResponsiveContainer` dentro da coluna de conteudo, que ja e `min-w-0` no
 * `Shell` — sem isso a coluna cresce ate caber o maior filho e estoura.
 */

import type { ReactNode } from "react";
import { ResponsiveContainer } from "recharts";

export function AreaDoGrafico({
  children,
  altura = 220,
}: {
  children: ReactNode;
  altura?: number;
}) {
  return (
    <div className="w-full" style={{ height: altura }}>
      <ResponsiveContainer width="100%" height="100%">
        {children as never}
      </ResponsiveContainer>
    </div>
  );
}
