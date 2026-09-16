/**
 * O card de condicoes do painel: alerta oficial e condicao prevista.
 *
 * O painel **nao se chama "alertas"** — cada card de condicao prevista diz
 * que e derivado da previsao, e cada card de alerta diz que e do INMET (ADR
 * 0001, reafirmado pelo ADR 0007). Alerta oficial tem precedencia sobre
 * condicao prevista nos dois slots: quando ha alerta, ele entra primeiro. O
 * teto de dois cards e a altura fixa `h-faixa3` sao do layout, e nao mudam
 * aqui — so a ordem dos slots muda com a precedencia.
 *
 * O card de condicao prevista muda de conteudo em relacao ao design de
 * referencia, que mostra uma temperatura grande ao lado do aviso: maxima e
 * minima nada dizem sobre vento ou tempestade. No lugar vao categoria, data e
 * o valor que disparou.
 */

import type { AlertaOficial, CondicaoPrevista, PainelSlot } from "../api/types";
import { diaDoCard } from "../formato";
import { Painel } from "./Painel";
import { WeatherIcon } from "./WeatherIcon";

type Props = {
  condicoes: PainelSlot[];
};

/**
 * Se o slot e um alerta oficial.
 *
 * Testa a **presenca** de `severidade`, um campo que so o alerta tem, e nao a
 * ausencia de `kind`: a checagem negativa classificaria como alerta qualquer
 * coisa que nao fosse condicao prevista, e um terceiro tipo de slot — ou um
 * `kind` que o alerta viesse a ganhar por outro motivo — cairia no ramo
 * errado sem erro de compilacao.
 */
function ehAlertaOficial(slot: PainelSlot): slot is AlertaOficial {
  return "severidade" in slot;
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

export function CondicoesPrevistas({ condicoes }: Props) {
  return (
    <Painel titulo="Condicoes previstas">
      {condicoes.length === 0 ? (
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
          {condicoes.map((slot) =>
            ehAlertaOficial(slot) ? (
              <CardDeAlerta key={slot.id} alerta={slot} />
            ) : (
              <CardDeCondicaoPrevista key={slot.kind} condicao={slot} />
            ),
          )}

          {/* O painel diz uma vez o que os cards de condicao prevista dizem
              em resumo: que nada ali e aviso oficial de defesa civil. Um
              card de alerta, se houver, ja declara a propria fonte. */}
          <li className="text-[10px] text-ink-3">
            Condicoes previstas nao sao alertas oficiais.
          </li>
        </ul>
      )}
    </Painel>
  );
}

function CardDeAlerta({ alerta }: { alerta: AlertaOficial }) {
  return (
    <li className="flex items-center gap-3 rounded-inner bg-brand-soft p-2.5">
      <span
        aria-hidden="true"
        className="size-9 shrink-0 rounded-full border border-line"
        style={{ backgroundColor: alerta.cor }}
      />
      <div className="min-w-0">
        <p className="text-[13px] font-semibold">
          {alerta.tipo} <span className="font-normal text-ink-2">{alerta.severidade}</span>
        </p>
        <p className="text-[11px] text-ink-2">{alerta.riscos}</p>
        <p className="text-[10px] text-ink-3">Alerta do INMET</p>
      </div>
    </li>
  );
}

function CardDeCondicaoPrevista({ condicao }: { condicao: CondicaoPrevista }) {
  return (
    <li className="flex items-center gap-3 rounded-inner bg-brand-soft p-2.5">
      <WeatherIcon
        icon={condicao.icon}
        description={condicao.label}
        className="size-9 shrink-0"
      />
      <div className="min-w-0">
        <p className="text-[13px] font-semibold">
          {condicao.label}{" "}
          <span className="font-normal text-ink-2">
            {outrosDias(condicao.also_days)}
          </span>
        </p>
        <p className="text-[11px] text-ink-2">
          {diaDoCard(condicao.date)} · {condicao.detail}
        </p>
        {/* Em cada card, nao so no rodape do painel: um card lido sozinho —
            e e assim que se le um aviso — precisa carregar a sua propria
            procedencia. */}
        <p className="text-[10px] text-ink-3">Derivado da previsao</p>
      </div>
    </li>
  );
}
