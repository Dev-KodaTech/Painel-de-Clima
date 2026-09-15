/**
 * O indice UV do dia corrente, hora a hora.
 *
 * **O unico painel da pagina que nao obedece a janela temporal**, e a excecao e
 * regra de produto, nao limitacao tecnica: a reanalise do passado nao mede UV —
 * o arquivo aceita o campo e devolve nulo para todos os dias. Por isso o UV
 * nunca entra na comparacao com o ano anterior e nunca cobre 30 dias ou 6
 * meses.
 *
 * A nota do payload diz isso na tela. Sem ela, um grafico de um dia numa pagina
 * de seis meses parece defeito.
 */

import { Area, AreaChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import type { UnitsDoHistorico, Uv } from "../../api/types";
import { faixaDeUv, horaComoNumero, horaCurta, medida } from "../../formato";
import { Painel } from "../Painel";
import { Numero } from "./Numero";
import { AreaDoGrafico } from "./AreaDoGrafico";
import { COR, EIXO, formatador, MARGEM, TOOLTIP } from "./grafico";
import { ResumoEmTexto } from "./ResumoEmTexto";

type Props = {
  uv: Uv;
  units: UnitsDoHistorico;
};

export function IndiceUv({ uv, units }: Props) {
  // O pico do dia: e a hora que a pessoa quer saber, e o numero grande do
  // painel deve ser ele, nao a media de 24 horas em que metade e noite.
  const pico = uv.horas.reduce<(typeof uv.horas)[number] | null>(
    (maior, hora) => (maior === null || hora.uv > maior.uv ? hora : maior),
    null,
  );

  const pontos = uv.horas.map((hora) => ({
    // Rotulo ja formatado por nos: nenhum timestamp passa por `new Date()`,
    // porque ele e horario de parede da cidade.
    rotulo: horaCurta(horaComoNumero(hora.time)),
    uv: hora.uv,
  }));

  return (
    <Painel titulo="Indice UV">
      {uv.horas.length === 0 ? (
        <p className="text-[13px] text-ink-2">
          Sem previsao de indice UV para esta cidade.
        </p>
      ) : (
        <>
          <div className="mb-4 flex flex-wrap gap-6">
            <Numero
              rotulo="Pico de hoje"
              valor={
                pico === null
                  ? null
                  : // A faixa junto do numero: 3 e 8 sao ambos "algum sol" para
                    // quem le, e "moderado" e "muito alto" para quem sabe.
                    `${medida(pico.uv, units.uv, 1)} · ${faixaDeUv(pico.uv)}`
              }
            />
            {pico && (
              <Numero
                rotulo="As"
                valor={horaCurta(horaComoNumero(pico.time))}
              />
            )}
            <Numero
              rotulo="Maxima dos 7 dias"
              valor={
                uv.maximo_da_semana === null
                  ? null
                  : `${medida(uv.maximo_da_semana, units.uv, 1)} · ${faixaDeUv(uv.maximo_da_semana)}`
              }
            />
          </div>

          <AreaDoGrafico altura={160}>
            <AreaChart data={pontos} margin={MARGEM}>
              <defs>
                <linearGradient id="area-uv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COR.anterior} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={COR.anterior} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={COR.grade} vertical={false} />
              {/* Uma marca a cada tres horas: 24 nao cabem na largura. */}
              <XAxis dataKey="rotulo" interval={2} {...EIXO} />
              <YAxis {...EIXO} width={32} allowDecimals={false} />
              <Tooltip
                {...TOOLTIP}
                formatter={formatador(
                  (valor) => `${medida(valor, units.uv, 1)} · ${faixaDeUv(valor)}`,
                  "Indice UV",
                )}
              />
              <Area
                type="monotone"
                dataKey="uv"
                stroke={COR.anterior}
                strokeWidth={2}
                fill="url(#area-uv)"
              />
            </AreaChart>
          </AreaDoGrafico>

          <ResumoEmTexto>
            {pico
              ? `Indice UV do dia, com pico de ${medida(pico.uv, units.uv, 1)} — ${faixaDeUv(pico.uv)} — as ${horaCurta(horaComoNumero(pico.time))}.`
              : "Indice UV do dia."}
          </ResumoEmTexto>
        </>
      )}

      {/* A nota fica **sempre**, inclusive no estado vazio: e ela que explica
          por que este painel nao acompanha a janela escolhida. */}
      <p className="mt-3 text-[11px] text-ink-3">{uv.nota}</p>
    </Painel>
  );
}
