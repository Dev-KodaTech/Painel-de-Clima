/**
 * Nascer e por do sol de hoje.
 *
 * Os horarios sao de parede da cidade consultada: "19:23" significa 19:23 la,
 * nao aqui. Por isso vem recortados do texto, nunca convertidos.
 */

import type { Sun } from "../api/types";
import { horaDoDia } from "../formato";
import { Painel } from "./Painel";
import { WeatherIcon } from "./WeatherIcon";

type Props = {
  sun: Sun;
};

/**
 * Os dois horarios do painel, com rotulo e icone fixos.
 *
 * Estes nomes de icone sao escolhidos aqui, e nao vindos do payload como os de
 * `current.icon` — uma excecao deliberada. A regra "todo dado vem do backend"
 * existe pela tabela WMO: e ela que traduz um *dado* (o codigo do tempo) em
 * icone, e que o frontend nao deve conhecer. Nascer e por do sol nao sao
 * condicao meteorologica: sao duas linhas fixas de um painel fixo, e mandar o
 * backend repetir "sunrise" a cada resposta seria cerimonia sem leitor.
 */
const HORARIOS = [
  { chave: "sunrise", rotulo: "Nascer do sol", icone: "sunrise" },
  { chave: "sunset", rotulo: "Por do sol", icone: "sunset" },
] as const;

export function CardSol({ sun }: Props) {
  return (
    <Painel titulo="Hoje">
      <dl className="flex flex-col gap-2.5">
        {HORARIOS.map(({ chave, rotulo, icone }) => (
          <div
            key={chave}
            className="flex items-center gap-3 rounded-inner p-2.5 shadow-card"
          >
            <WeatherIcon
              icon={icone}
              description={rotulo}
              className="size-8 shrink-0"
            />
            <div>
              <dt className="text-[10px] text-ink-2">{rotulo}</dt>
              <dd className="text-base font-semibold text-brand-text">
                {horaDoDia(sun[chave])}
              </dd>
            </div>
          </div>
        ))}
      </dl>
    </Painel>
  );
}
