/**
 * As condicoes severas previstas para a semana.
 *
 * O painel **nao se chama "alertas"**, e cada card diz que e derivado da
 * previsao. O desvio do design de referencia e deliberado: alerta
 * meteorologico e a categoria de informacao em que pessoas tomam decisao de
 * seguranca, e o que esta aqui e uma regra nossa sobre a previsao, nao um
 * aviso de defesa civil. Custa uma linha de texto.
 *
 * O card tambem muda de conteudo em relacao ao design, que mostra uma
 * temperatura grande ao lado do aviso: maxima e minima nada dizem sobre vento
 * ou tempestade. No lugar vao categoria, data e o valor que disparou.
 */

import type { Alerta } from "../api/types";
import { dataCurta, diaDaSemanaCurto } from "../formato";
import { Painel } from "./Painel";
import { WeatherIcon } from "./WeatherIcon";

type Props = {
  alerts: Alerta[];
};

/** "Sex, 16 set" — o dia que o card representa, sem ambiguidade na semana. */
function quando(date: string): string {
  return `${diaDaSemanaCurto(date)}, ${dataCurta(date)}`;
}

/**
 * "(+4 dias)" — os outros dias da mesma categoria, que nao viraram cards.
 *
 * Sem esta linha o dedup mentiria por omissao: Wellington tem cinco dias de
 * vento forte e exibe um card, e quem olhasse veria um dia de vento numa semana
 * que tem cinco.
 */
function outrosDias(quantidade: number): string | null {
  if (quantidade <= 0) return null;
  return quantidade === 1 ? "(+1 dia)" : `(+${quantidade} dias)`;
}

/**
 * A altura fixa da lista, igual em qualquer estado.
 *
 * O grid tem nove paineis, e este e o unico cujo conteudo pode ser nada. Sem
 * altura propria, uma semana tranquila encolheria o card e desalinharia a
 * faixa inteira — e o estado vazio e o caso comum, nao a excecao.
 *
 * O valor e o token `--spacing-faixa3`, compartilhado com o painel de
 * precipitacao ao lado: os dois precisam concordar, e um numero repetido nos
 * dois arquivos concordaria so ate alguem editar um deles.
 */
const ALTURA = "h-faixa3";

export function CondicoesPrevistas({ alerts }: Props) {
  return (
    <Painel titulo="Condicoes previstas">
      {alerts.length === 0 ? (
        <div className={`flex ${ALTURA} flex-col items-center justify-center gap-1`}>
          <WeatherIcon
            icon="clear-day"
            description="Nenhuma condicao severa"
            className="size-10"
          />
          <p className="text-[13px] font-medium">Sem condicoes severas</p>
          <p className="text-[11px] text-ink-3">nos proximos 7 dias</p>
        </div>
      ) : (
        <ul className={`flex ${ALTURA} flex-col gap-2.5`}>
          {alerts.map((alerta) => (
            <li
              key={alerta.kind}
              className="flex items-center gap-3 rounded-inner bg-brand-soft p-2.5"
            >
              <WeatherIcon
                icon={alerta.icon}
                description={alerta.label}
                className="size-9 shrink-0"
              />
              <div className="min-w-0">
                <p className="text-[13px] font-semibold">
                  {alerta.label}{" "}
                  <span className="font-normal text-ink-2">
                    {outrosDias(alerta.also_days)}
                  </span>
                </p>
                <p className="text-[11px] text-ink-2">
                  {quando(alerta.date)} · {alerta.detail}
                </p>
                {/* Em cada card, nao so no rodape do painel: um card lido
                    sozinho — e e assim que se le um aviso — precisa carregar a
                    sua propria procedencia. */}
                <p className="text-[10px] text-ink-3">Derivado da previsao</p>
              </div>
            </li>
          ))}

          {/* O painel diz uma vez o que os cards dizem em resumo: que nada
              aqui e aviso oficial de defesa civil. */}
          <li className="text-[10px] text-ink-3">Nao sao alertas oficiais.</li>
        </ul>
      )}
    </Painel>
  );
}
