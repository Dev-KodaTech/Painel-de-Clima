/**
 * O vento da janela: a velocidade ao longo do periodo e a direcao dominante.
 *
 * A direcao vem em ponto cardeal, porque "noroeste" se le e "312°" se calcula.
 * A media que a produz e vetorial e roda no backend: a media aritmetica de 350°
 * e 10° daria 180°, o rumo exatamente oposto.
 *
 * Aqui o vento e **medicao, nao aviso**. Nenhum rotulo de severidade acompanha
 * este grafico: a condicao prevista de vento forte e outra coisa, mora na sua
 * pagina e vem com o rotulo que diz que foi derivada da previsao.
 */

import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";
import type {
  DiaDoHistorico,
  ResumoDoHistorico,
  UnitsDoHistorico,
} from "../../api/types";
import { medida, rumoPorExtenso } from "../../formato";
import { Numero } from "./Numero";
import { PainelDeMetrica } from "./PainelDeMetrica";
import {
  COR,
  EIXO,
  EIXO_DE_DATAS,
  formatador,
  MARGEM,
  porDia,
  TOOLTIP,
} from "./grafico";

type Props = {
  serie: DiaDoHistorico[];
  resumo: ResumoDoHistorico;
  units: UnitsDoHistorico;
};

export function Vento({ serie, resumo, units }: Props) {
  const pontos = porDia(serie, (dia) => dia.wind_speed);
  const rumo = resumo.rumo_dominante;

  const emKmh = (valor: number) => medida(valor, units.wind_speed, 1);

  return (
    <PainelDeMetrica
      titulo="Vento"
      numeros={
        <>
          <Numero
            rotulo="Maxima da janela"
            valor={
              resumo.vento_maximo === null ? null : emKmh(resumo.vento_maximo)
            }
          />
          {/* A palavra para quem le e a sigla para quem reconhece. O **grau**
              nao vira tile: ele existe para o grafico, e "241°" como metrica de
              destaque e o numero que a sigla foi posta ali para dispensar. */}
          <Numero
            rotulo="Direcao dominante"
            valor={rumo === null ? null : `${rumoPorExtenso(rumo)} (${rumo})`}
          />
        </>
      }
      resumoEmTexto={
        resumo.vento_maximo === null
          ? "Sem dado de vento para esta janela."
          : `Vento maximo de ${emKmh(resumo.vento_maximo)}${
              rumo ? `, com direcao dominante de ${rumoPorExtenso(rumo)}` : ""
            }.`
      }
    >
      <LineChart data={pontos} margin={MARGEM}>
        <CartesianGrid stroke={COR.grade} vertical={false} />
        <XAxis dataKey="rotulo" {...EIXO_DE_DATAS} />
        <YAxis {...EIXO} width={62} unit={` ${units.wind_speed}`} />
        <Tooltip {...TOOLTIP} formatter={formatador(emKmh, "Vento")} />
        <Line
          type="monotone"
          dataKey="valor"
          stroke={COR.atual}
          strokeWidth={2}
          dot={false}
          connectNulls
        />
      </LineChart>
    </PainelDeMetrica>
  );
}
