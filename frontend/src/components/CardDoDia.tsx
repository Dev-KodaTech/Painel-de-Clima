/**
 * O card de hoje: temperatura atual em destaque, com descricao, icone,
 * sensacao termica e os extremos do dia.
 *
 * Todas as unidades vem do payload (`units`), nunca escritas aqui: a escolha
 * de unidade e do backend.
 */

import type { Current, Location, Units } from "../api/types";
import { dataPorExtenso, horaDoDia, procedencia, temperatura } from "../formato";
import { WeatherIcon } from "./WeatherIcon";

type Props = {
  location: Location;
  current: Current;
  units: Units;
};

export function CardDoDia({ location, current, units }: Props) {
  return (
    <section className="rounded-card bg-card p-[18px] shadow-card">
      <header className="flex items-baseline justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">{location.name}</h2>
          <p className="mt-0.5 text-[11px] text-ink-2">
            {procedencia(location.admin1, location.country)}
          </p>
        </div>
        {/* Data e hora da cidade consultada, nao do usuario. */}
        <p className="shrink-0 text-right text-[11px] text-ink-3">
          {dataPorExtenso(current.observed_at)}
          <span className="ml-1.5">{horaDoDia(current.observed_at)}</span>
        </p>
      </header>

      <div className="mt-5 flex items-center gap-4">
        <WeatherIcon
          icon={current.icon}
          description={current.description}
          className="size-20 shrink-0"
        />
        <div>
          <p className="text-[56px] leading-none font-semibold tracking-[-0.02em] text-accent">
            {temperatura(current.temperature, units.temperature)}
          </p>
          <p className="mt-1.5 text-[13px]">{current.description}</p>
        </div>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-y-2 border-t border-line pt-4 text-[13px]">
        <dt className="text-[11px] tracking-wide text-ink-3 uppercase">Sensacao</dt>
        <dd className="text-right">
          {temperatura(current.apparent_temperature, units.temperature)}
        </dd>

        <dt className="text-[11px] tracking-wide text-ink-3 uppercase">Max / min</dt>
        <dd className="text-right">
          {temperatura(current.high, units.temperature)}
          <span className="mx-1 text-ink-3">/</span>
          <span className="text-ink-2">
            {temperatura(current.low, units.temperature)}
          </span>
        </dd>
      </dl>
    </section>
  );
}
