/**
 * Tipos que espelham o payload do backend.
 *
 * Sao o contrato do lado do frontend: um campo errado quebra na compilacao e
 * nao em producao. Devem acompanhar `backend/app/models.py` 1:1 — os nomes
 * sao deliberadamente identicos aos do JSON.
 */

/** Uma cidade candidata: resultado de geocodificacao ainda nao escolhido. */
export type Cidade = {
  id: number;
  name: string;
  country: string;
  country_code: string;
  /** Ausente em lugares pequenos; e o que distingue candidatas homonimas. */
  admin1: string | null;
  latitude: number;
  longitude: number;
  population: number | null;
  timezone: string;
};

export type CidadesResponse = {
  results: Cidade[];
};

export type Location = {
  name: string;
  country: string;
  country_code: string;
  admin1: string | null;
  latitude: number;
  longitude: number;
  timezone: string;
  utc_offset_seconds: number;
};

export type Current = {
  /**
   * Horario local de parede da cidade, sem sufixo de fuso
   * (`2026-09-14T03:00`). Tratar como UTC desloca o horario em horas.
   */
  observed_at: string;
  temperature: number;
  apparent_temperature: number;
  weather_code: number;
  /** Texto ja traduzido pelo backend: o frontend nao conhece a tabela WMO. */
  description: string;
  /** Nome de arquivo no conjunto Meteocons, tambem resolvido no backend. */
  icon: string;
  is_day: boolean;
  /** Do bloco diario: a API externa nao fornece extremos em `current`. */
  high: number;
  low: number;
};

export type Units = {
  temperature: string;
  precipitation: string;
  wind_speed: string;
  distance: string;
};

export type WeatherResponse = {
  location: Location;
  current: Current;
  units: Units;
  attribution: string;
};
