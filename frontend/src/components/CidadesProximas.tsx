/**
 * A temperatura das cidades vizinhas, para comparar com a regiao em volta.
 *
 * **Substitui o mapa ilustrado de regioes do design de referencia.** O mapa
 * pressupoe um pais fixo, o que e incompativel com buscar qualquer cidade do
 * mundo: nao ha ilustracao que sirva para Berlim e para Papeete. A tabela ja
 * existe no design, no canto inferior direito; perde-se a ilustracao e ganha-se
 * uma cidade qualquer.
 *
 * A distancia e coluna, nao enfeite: numa cidade isolada as vizinhas estao a
 * milhares de quilometros, e e a distancia que diz o quanto a comparacao vale.
 *
 * A sigla do pais acompanha a distancia porque a selecao ignora fronteiras: de
 * Basileia saem Mulhouse (FR), Freiburg (DE) e Berna (CH), e sem a sigla as
 * tres se leriam como suicas. Proximidade importa mais que nacionalidade, mas
 * a nacionalidade ainda e o que explica um nome estrangeiro na lista.
 */

import type { Nearby, Units } from "../api/types";
import { distancia, temperatura } from "../formato";
import { Painel } from "./Painel";
import { WeatherIcon } from "./WeatherIcon";

type Props = {
  nearby: Nearby[];
  units: Units;
};

export function CidadesProximas({ nearby, units }: Props) {
  return (
    <Painel titulo="Cidades proximas">
      {nearby.length === 0 ? (
        <p className="text-[11px] text-ink-3">
          Sem cidades proximas para comparar.
        </p>
      ) : (
        <ul className="flex flex-col">
          {nearby.map((cidade) => (
            <li
              key={`${cidade.name}-${cidade.distance_km}`}
              // Divisoria entre linhas, nao em volta delas: a ultima nao
              // recebe borda, para a tabela nao terminar num traco solto.
              className="flex items-center gap-2.5 border-b border-line py-2 last:border-0 last:pb-0"
            >
              <WeatherIcon
                icon={cidade.icon}
                description={cidade.description}
                className="size-7 shrink-0"
              />

              <div className="min-w-0 flex-1">
                {/* `truncate` porque nomes longos existem — "Villingen-
                    Schwenningen" — e a coluna e estreita: cortar e melhor que
                    empurrar a temperatura para fora do card. */}
                <p className="truncate text-[13px] font-medium">{cidade.name}</p>
                <p className="text-[10px] text-ink-3">
                  {distancia(cidade.distance_km, units.distance)} ·{" "}
                  {cidade.country_code}
                </p>
              </div>

              <p className="text-[13px] font-semibold tabular-nums">
                {temperatura(cidade.temperature, units.temperature)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Painel>
  );
}
