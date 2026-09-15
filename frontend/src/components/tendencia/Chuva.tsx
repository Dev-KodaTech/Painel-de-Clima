/**
 * A chuva da janela: o acumulado em numeros e a distribuicao em barras.
 *
 * Os dois juntos porque um sem o outro engana: 60 mm num mes podem ser "choveu
 * um pouco todo dia" ou "choveu tudo numa tarde", e o acumulado sozinho nao
 * distingue os dois. Dai as barras ao lado e a contagem de dias com chuva.
 */

import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import type {
  DiaDoHistorico,
  ResumoDoHistorico,
  UnitsDoHistorico,
} from "../../api/types";
import { acumulado } from "../../formato";
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
  /** O ano da comparacao, para rotular o acumulado anterior. `null` sem ele. */
  anoAnterior: string | null;
  units: UnitsDoHistorico;
};

export function Chuva({ serie, resumo, anoAnterior, units }: Props) {
  // Zero e nao `null`: um dia sem chuva **teve** zero de chuva, e omiti-lo
  // abriria um buraco no grafico onde houve um dia seco.
  const pontos = porDia(serie, (dia) => dia.precipitation_mm ?? 0);

  const emMm = (valor: number) => acumulado(valor, units.precipitation);

  return (
    <PainelDeMetrica
      titulo="Chuva"
      numeros={
        <>
          <Numero
            rotulo="Acumulado"
            valor={
              resumo.chuva_total_mm === null ? null : emMm(resumo.chuva_total_mm)
            }
          />
          {/* Ao lado do atual, para responder "foi mais seco que o normal?". */}
          {anoAnterior && (
            <Numero
              rotulo={`Em ${anoAnterior}`}
              valor={
                resumo.chuva_total_anterior_mm === null
                  ? null
                  : emMm(resumo.chuva_total_anterior_mm)
              }
            />
          )}
          <Numero
            rotulo="Dias com chuva"
            valor={`${resumo.dias_com_chuva} de ${serie.length}`}
          />
        </>
      }
      resumoEmTexto={
        resumo.chuva_total_mm === null
          ? "Sem dado de chuva para esta janela."
          : `Choveu ${emMm(resumo.chuva_total_mm)} ao longo de ${serie.length} dias, em ${resumo.dias_com_chuva} deles.`
      }
    >
      <BarChart data={pontos} margin={MARGEM}>
        <CartesianGrid stroke={COR.grade} vertical={false} />
        <XAxis dataKey="rotulo" {...EIXO_DE_DATAS} />
        <YAxis {...EIXO} width={56} unit={` ${units.precipitation}`} />
        <Tooltip {...TOOLTIP} formatter={formatador(emMm, "Chuva")} />
        <Bar dataKey="valor" fill={COR.atual} radius={[3, 3, 0, 0]} />
      </BarChart>
    </PainelDeMetrica>
  );
}
