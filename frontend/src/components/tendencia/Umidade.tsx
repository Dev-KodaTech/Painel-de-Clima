/**
 * A variacao da umidade do ar ao longo da janela.
 *
 * Minima e maxima acompanham a media porque a media sozinha esconde a
 * amplitude: 70% de media pode ser um periodo estavel ou um que oscilou entre
 * 40% e 95%, e sao climas diferentes de se viver.
 */

import { Area, AreaChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import type {
  DiaDoHistorico,
  ResumoDoHistorico,
  UnitsDoHistorico,
} from "../../api/types";
import { medida } from "../../formato";
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

export function Umidade({ serie, resumo, units }: Props) {
  // `null` aqui, ao contrario da chuva: um dia sem medicao de umidade nao teve
  // 0% de umidade — a curva deve pular o ponto, nao mergulhar no chao.
  const pontos = porDia(serie, (dia) => dia.humidity);

  const emPorcento = (valor: number) => medida(valor, units.humidity);

  return (
    <PainelDeMetrica
      titulo="Umidade do ar"
      numeros={
        <>
          <Numero
            rotulo="Minima"
            valor={
              resumo.umidade_minima === null
                ? null
                : emPorcento(resumo.umidade_minima)
            }
          />
          <Numero
            rotulo="Media"
            valor={
              resumo.umidade_media === null
                ? null
                : emPorcento(resumo.umidade_media)
            }
          />
          <Numero
            rotulo="Maxima"
            valor={
              resumo.umidade_maxima === null
                ? null
                : emPorcento(resumo.umidade_maxima)
            }
          />
        </>
      }
      resumoEmTexto={
        resumo.umidade_media === null
          ? "Sem dado de umidade para esta janela."
          : `Umidade media de ${emPorcento(resumo.umidade_media)}, variando entre ${emPorcento(resumo.umidade_minima ?? 0)} e ${emPorcento(resumo.umidade_maxima ?? 0)}.`
      }
    >
      <AreaChart data={pontos} margin={MARGEM}>
        <defs>
          <linearGradient id="area-umidade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COR.atual} stopOpacity={0.22} />
            <stop offset="100%" stopColor={COR.atual} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={COR.grade} vertical={false} />
        <XAxis dataKey="rotulo" {...EIXO_DE_DATAS} />
        {/* 0 a 100 fixo: umidade relativa tem escala propria, e deixa-la
            automatica faria uma variacao de 68% a 71% ocupar o painel inteiro
            e parecer dramatica. */}
        <YAxis {...EIXO} width={46} domain={[0, 100]} unit={units.humidity} />
        <Tooltip {...TOOLTIP} formatter={formatador(emPorcento, "Umidade")} />
        <Area
          type="monotone"
          dataKey="valor"
          stroke={COR.atual}
          strokeWidth={2}
          fill="url(#area-umidade)"
          connectNulls
        />
      </AreaChart>
    </PainelDeMetrica>
  );
}
