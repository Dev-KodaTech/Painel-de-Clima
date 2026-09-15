/**
 * Um numero de resumo: rotulo pequeno em cima, valor grande embaixo.
 *
 * Existe porque a pagina tem dez deles e o alinhamento entre metricas de
 * paineis diferentes depende de todos usarem os mesmos tamanhos.
 *
 * `null` vira um traco, e nao zero: uma janela sem dado nao teve zero de
 * umidade — ela nao teve umidade medida, e "0%" seria uma leitura falsa.
 */

export function Numero({
  rotulo,
  valor,
}: {
  rotulo: string;
  valor: string | null;
}) {
  return (
    <div>
      <p className="text-[11px] text-ink-2">{rotulo}</p>
      <p className="mt-0.5 text-lg font-semibold tabular-nums">
        {valor ?? <span className="text-ink-3">—</span>}
      </p>
    </div>
  );
}
