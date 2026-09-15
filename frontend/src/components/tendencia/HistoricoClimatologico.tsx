/**
 * O historico climatologico: a temperatura da janela sobreposta a do mesmo
 * periodo do ano anterior.
 *
 * E a comparacao que responde "este periodo esta fora do normal?" — a razao de
 * a pagina existir. As duas series compartilham o eixo horizontal por **posicao
 * na janela**, e nao por data: as datas diferem por um ano, e um eixo temporal
 * real as poria a 365 dias de distancia uma da outra.
 */

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DiaDoHistorico, UnitsDoHistorico } from "../../api/types";
import { ano, dataCurta, diferenca, temperatura } from "../../formato";
import { Painel } from "../Painel";
import { AreaDoGrafico } from "./AreaDoGrafico";
import { COR, EIXO, EIXO_DE_DATAS, MARGEM, TOOLTIP } from "./grafico";
import { ResumoEmTexto } from "./ResumoEmTexto";

type Props = {
  serie: DiaDoHistorico[];
  comparacao: DiaDoHistorico[];
  /** A diferenca media, ja calculada no backend. `null` sem ano anterior. */
  diferencaMedia: number | null;
  units: UnitsDoHistorico;
};

/** A media do dia: a curva compara dias, nao picos. */
function mediaDoDia(dia: DiaDoHistorico | undefined): number | null {
  if (!dia || dia.high === null || dia.low === null) return null;
  return (dia.high + dia.low) / 2;
}

/** `09-14` a partir de `2026-09-14`: a data sem o ano, que e o que casa. */
function mesEDia(data: string): string {
  return data.slice(5, 10);
}

/**
 * As duas series casadas pela **data do calendario**, nao pela posicao.
 *
 * Casar por indice seria mais curto e funciona enquanto as duas listas vem
 * completas e do mesmo tamanho — que e o caso comum. Mas o arquivo pode vir
 * curto ou com um buraco na cabeca (o proprio contrato preve: "serie incompleta
 * devolve os dias que existem"), e ai o i-esimo dia de uma deixa de ser o
 * i-esimo da outra. O desalinhamento seria **invisivel**: as duas curvas
 * continuariam plausiveis, deslocadas pelo tamanho do buraco, e cada tooltip
 * compararia setembro com agosto sem dizer nada.
 *
 * 29 de fevereiro nao existe no ano anterior e simplesmente nao encontra par —
 * a curva do ano passado tem um furo ali, que e a verdade, e `connectNulls` o
 * atravessa.
 */
function casar(serie: DiaDoHistorico[], comparacao: DiaDoHistorico[]) {
  const anterior = new Map(comparacao.map((dia) => [mesEDia(dia.date), dia]));

  return serie.map((dia) => {
    const par = anterior.get(mesEDia(dia.date));
    return {
      rotulo: dataCurta(dia.date),
      atual: mediaDoDia(dia),
      anterior: mediaDoDia(par),
    };
  });
}

export function HistoricoClimatologico({
  serie,
  comparacao,
  diferencaMedia,
  units,
}: Props) {
  if (serie.length === 0) {
    return (
      <Painel titulo="Historico climatologico">
        <p className="text-[13px] text-ink-2">
          O arquivo nao tem dado para esta cidade nesta janela.
        </p>
      </Painel>
    );
  }

  const pontos = casar(serie, comparacao);
  const anoAtual = ano(serie[0].date);
  const anoAnterior = comparacao.length > 0 ? ano(comparacao[0].date) : null;

  return (
    <Painel titulo="Historico climatologico">
      {/* A conclusao antes do grafico: quem so quer o numero nao precisa
          interpretar duas curvas. */}
      {diferencaMedia !== null && anoAnterior ? (
        <p className="mb-3 text-[13px] text-ink-2">
          Este periodo esta{" "}
          <strong className="font-semibold text-ink">
            {diferenca(diferencaMedia, units.temperature)}
          </strong>{" "}
          em relacao ao mesmo periodo de {anoAnterior}.
        </p>
      ) : (
        // A serie nao some sem explicacao: o arquivo simplesmente nao cobre
        // aquele periodo nesta cidade.
        <p className="mb-3 text-[13px] text-ink-2">
          Sem dado do ano anterior para esta cidade e janela — o grafico mostra
          so o periodo atual.
        </p>
      )}

      <AreaDoGrafico>
        <LineChart data={pontos} margin={MARGEM}>
          <CartesianGrid stroke={COR.grade} vertical={false} />
          <XAxis dataKey="rotulo" {...EIXO_DE_DATAS} />
          <YAxis
            {...EIXO}
            width={52}
            tickFormatter={(valor: number) =>
              temperatura(valor, units.temperature)
            }
          />
          <Tooltip
            {...TOOLTIP}
            // O nome da serie e o rotulo aqui — sao duas, e "2025" ou "2026"
            // e justamente o que o tooltip precisa dizer.
            formatter={(valor: unknown, nome: unknown) => [
              typeof valor === "number"
                ? temperatura(valor, units.temperature)
                : "—",
              String(nome),
            ]}
          />
          <Legend
            iconType="plainline"
            wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
          />

          {/* O ano anterior desenhado **primeiro**, e tracejado: fica atras da
              serie atual, que e a que a pessoa veio ver. As duas se distinguem
              por cor e por traco — cor sozinha excluiria quem nao a percebe. */}
          {anoAnterior && (
            <Line
              type="monotone"
              dataKey="anterior"
              name={anoAnterior}
              stroke={COR.anterior}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              // `connectNulls`: um dia sem medicao no meio do arquivo nao deve
              // partir a curva em duas.
              connectNulls
            />
          )}
          <Line
            type="monotone"
            dataKey="atual"
            name={anoAtual}
            stroke={COR.atual}
            strokeWidth={2.4}
            dot={false}
            connectNulls
          />
        </LineChart>
      </AreaDoGrafico>

      <ResumoEmTexto>
        Temperatura media diaria de {dataCurta(serie[0].date)} a{" "}
        {dataCurta(serie[serie.length - 1].date)}.
        {diferencaMedia !== null && anoAnterior
          ? ` O periodo esta ${diferenca(diferencaMedia, units.temperature)} em relacao a ${anoAnterior}.`
          : " Sem dado do ano anterior para comparar."}
      </ResumoEmTexto>
    </Painel>
  );
}
