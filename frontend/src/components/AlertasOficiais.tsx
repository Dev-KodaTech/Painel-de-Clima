/**
 * Os alertas oficiais do INMET que cobrem a cidade escolhida.
 *
 * Secao **estruturalmente separada** das condicoes previstas (ADR 0007): o
 * card declara a fonte oficial com a mesma insistencia que o card de condicao
 * prevista declara "derivado da previsao" — a fronteira e o que impede as duas
 * categorias de se confundirem quando lidas soltas, fora da pagina.
 *
 * Os **tres estados nunca colapsam**: sem alerta ativo, fora de cobertura e
 * falha na consulta parecem a mesma "lista vazia" vistos de fora, mas
 * afirmam fatos diferentes — ver `StatusDosAlertas` em `api/types.ts` e o
 * verbete *Alerta* do `CONTEXT.md`.
 */

import type { AlertaOficial, StatusDosAlertas } from "../api/types";
import { Painel } from "./Painel";

type Props = {
  alertas: AlertaOficial[];
  status: StatusDosAlertas;
};

const TELEFONE_DEFESA_CIVIL = "199";
const TELEFONE_BOMBEIROS = "193";

/**
 * O texto sobre a faixa de severidade e **sempre escuro**, nas tres cores.
 *
 * As cores do INMET sao todas saturadas e claras, e o branco reprova em
 * todas: medido em WCAG contra `#FFFFFF`, o amarelo `#FFFE00` da 1,08:1, o
 * laranja `#FF8C00` da 2,33:1 e o vermelho `#FF0000` da 4,00:1 — nenhuma
 * alcanca o minimo de 4,5:1. O preto passa nas tres: 19,4:1, 9,0:1 e 5,25:1.
 *
 * O preto e fixo, e nao o token `--color-ink`: a cor de fundo vem do INMET e
 * e a mesma nos dois temas, entao um texto que seguisse o tema viraria quase
 * branco no escuro sobre um fundo que continuou amarelo. Esta faixa e a
 * unica superficie do app que nao pertence ao tema.
 */
const TEXTO_SOBRE_SEVERIDADE = "#000000";

export function AlertasOficiais({ alertas, status }: Props) {
  return (
    <Painel titulo="Alertas oficiais" className="border-2 border-accent/40">
      {status === "fora_de_cobertura" && <ForaDeCobertura />}
      {status === "indisponivel" && <ConsultaIndisponivel />}
      {status === "ok" && alertas.length === 0 && <SemAlertasAtivos />}
      {status === "ok" && alertas.length > 0 && <ListaDeAlertas alertas={alertas} />}
    </Painel>
  );
}

function ForaDeCobertura() {
  return (
    <p className="py-4 text-[13px] text-ink-2">
      O INMET so cobre o Brasil. Fora do pais, nao ha como saber se ha alerta
      ativo para esta regiao.
    </p>
  );
}

function ConsultaIndisponivel() {
  return (
    <p role="alert" className="py-4 text-[13px] text-ink-2">
      Nao foi possivel consultar o INMET agora. A ausencia de alerta aqui nao
      significa que a regiao esta livre de aviso — tente novamente em
      instantes.
    </p>
  );
}

function SemAlertasAtivos() {
  return (
    <p className="py-4 text-[13px] text-ink-2">
      Nenhum alerta oficial ativo para esta regiao.
    </p>
  );
}

function ListaDeAlertas({ alertas }: { alertas: AlertaOficial[] }) {
  return (
    <div className="flex flex-col gap-3">
      <ul className="flex flex-col gap-3">
        {alertas.map((alerta) => (
          <CardDeAlerta key={alerta.id} alerta={alerta} />
        ))}
      </ul>
      <p className="text-[11px] text-ink-3">
        Em risco: Defesa Civil {TELEFONE_DEFESA_CIVIL} · Bombeiros{" "}
        {TELEFONE_BOMBEIROS}
      </p>
    </div>
  );
}

function CardDeAlerta({ alerta }: { alerta: AlertaOficial }) {
  return (
    <li className="overflow-hidden rounded-inner border border-line">
      <div
        className="flex items-center justify-between gap-2 px-3 py-2"
        style={{ backgroundColor: alerta.cor, color: TEXTO_SOBRE_SEVERIDADE }}
      >
        <span className="text-[13px] font-semibold">{alerta.tipo}</span>
        {/* A severidade e texto, nunca so a cor do fundo — quem le sem
            perceber cor precisa do mesmo dado. */}
        <span className="text-[11px] font-medium">{alerta.severidade}</span>
      </div>

      <div className="flex flex-col gap-2 bg-brand-soft p-3">
        <p className="text-[11px] text-ink-2">
          Valido de {alerta.inicio} ate {alerta.fim}
        </p>
        <p className="text-[13px]">{alerta.riscos}</p>

        <details className="text-[12px]">
          <summary className="cursor-pointer select-none font-medium text-brand-text">
            Recomendacoes de seguranca
          </summary>
          <p className="mt-1.5 text-ink-2">{alerta.instrucoes}</p>
        </details>

        <p className="text-[10px] text-ink-3">Alerta do INMET</p>
      </div>
    </li>
  );
}
