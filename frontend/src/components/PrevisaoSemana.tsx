/**
 * A previsao dos sete dias: uma coluna por dia, com icone e maxima/minima.
 *
 * O primeiro dia e hoje — o backend monta o bloco comecando no dia corrente —,
 * e e ele que recebe o destaque. Nao ha selecao: o destaque orienta na
 * sequencia, nao indica escolha.
 */

import type { DailyPoint, Units } from "../api/types";
import { dataCurta, diaDaSemanaCurto, temperatura } from "../formato";
import { Painel } from "./Painel";
import { WeatherIcon } from "./WeatherIcon";

type Props = {
  daily: DailyPoint[];
  units: Units;
};

export function PrevisaoSemana({ daily, units }: Props) {
  return (
    <Painel titulo="Previsao da semana">
      <ol className="flex justify-between gap-1.5">
        {daily.map((dia, indice) => {
          const hoje = indice === 0;
          return (
            <li
              key={dia.date}
              className={`flex-1 rounded-inner px-2 py-2.5 text-center ${
                hoje ? "bg-brand text-white" : ""
              }`}
            >
              <p className={`text-[11px] ${hoje ? "text-white/80" : "text-ink-2"}`}>
                {hoje ? "Hoje" : diaDaSemanaCurto(dia.date)}
              </p>
              <p className={`text-[10px] ${hoje ? "text-white/70" : "text-ink-3"}`}>
                {dataCurta(dia.date)}
              </p>

              <WeatherIcon
                icon={dia.icon}
                description={dia.description}
                className="mx-auto my-1.5 size-9"
              />

              <p className="text-[13px] font-semibold">
                {temperatura(dia.high, units.temperature)}
              </p>
              <p className={`text-[11px] ${hoje ? "text-white/80" : "text-ink-2"}`}>
                {temperatura(dia.low, units.temperature)}
              </p>
            </li>
          );
        })}
      </ol>
    </Painel>
  );
}
