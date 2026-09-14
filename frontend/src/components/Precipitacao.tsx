/**
 * A chuva prevista para cada um dos sete dias, em barras comparaveis.
 *
 * Le o mesmo bloco `daily` da previsao da semana — o design mostra os mesmos
 * sete dias nos dois paineis, e um segundo bloco no payload so os deixaria
 * livres para divergir.
 *
 * As barras sao normalizadas pelo dia mais chuvoso da propria semana, nao por
 * uma escala fixa de milimetros: o painel responde "qual dia levar
 * guarda-chuva", e uma escala absoluta deixaria a semana inteira de Singapura
 * rente ao chao enquanto Miami estoura o topo.
 */

import type { DailyPoint, Units } from "../api/types";
import { diaDaSemanaCurto, precipitacao } from "../formato";
import { Painel } from "./Painel";

type Props = {
  daily: DailyPoint[];
  units: Units;
};

/** A barra do dia mais chuvoso ocupa a area inteira; as demais, uma fracao. */
const ESCALA_PERCENTUAL = 100;

/**
 * A altura minima de uma barra com chuva, em porcentagem.
 *
 * Sem ela, 0,4 mm ao lado de 104 mm arredonda para nada visivel e o dia parece
 * seco. Um tracinho diz "choveu pouco", que e verdade; ausencia diria "nao
 * choveu", que nao e.
 */
const ALTURA_MINIMA = 3;

/**
 * A altura da barra de um dia, de 0 a 100.
 *
 * Uma semana inteiramente seca tem maximo zero, e dividir por ele daria `NaN`
 * em toda barra — o caso e comum (Cairo: sete dias sem chuva), nao exotico.
 */
function altura(milimetros: number, maximo: number): number {
  if (milimetros <= 0 || maximo <= 0) return 0;
  return Math.max((milimetros / maximo) * ESCALA_PERCENTUAL, ALTURA_MINIMA);
}

export function Precipitacao({ daily, units }: Props) {
  const maximo = Math.max(...daily.map((dia) => dia.precipitation_mm));

  return (
    <Painel titulo="Precipitacao prevista">
      <ol className="flex h-faixa3 items-end justify-between gap-2">
        {daily.map((dia, indice) => (
          <li key={dia.date} className="flex h-full flex-1 flex-col justify-end gap-1.5">
            <p className="text-center text-[10px] text-ink-2">
              {precipitacao(dia.precipitation_mm, units.precipitation)}
            </p>

            {/* A coluna e transparente: so a barra tem cor. Uma trilha de
                fundo preenchida competiria com as barras baixas — sete caixas
                cheias e uma barra azul leem-se pior que sete barras. */}
            <div className="flex h-full items-end">
              <div
                className="w-full rounded-t-md bg-brand"
                style={{ height: `${altura(dia.precipitation_mm, maximo)}%` }}
              />
            </div>

            {/* A linha de base do grafico, que sustenta o dia sem chuva. */}
            <div className="h-px bg-line" />

            <p className="text-center text-[11px] text-ink-2">
              {indice === 0 ? "Hoje" : diaDaSemanaCurto(dia.date)}
            </p>
          </li>
        ))}
      </ol>
    </Painel>
  );
}
