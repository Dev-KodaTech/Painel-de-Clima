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

/** Um ponto do grafico de tendencia. */
export type HourlyPoint = {
  /** Horario de parede da cidade, sem sufixo (`2026-09-14T15:00`). */
  time: string;
  temperature: number;
};

/**
 * Um dia da previsao. Um unico bloco alimenta dois paineis — semana e
 * precipitacao —, porque o design mostra os mesmos sete dias em ambos.
 */
export type DailyPoint = {
  /** Data local da cidade (`2026-09-14`), sem horario. */
  date: string;
  weather_code: number;
  description: string;
  icon: string;
  high: number;
  low: number;
  precipitation_mm: number;
};

export type Sun = {
  /** Horario de parede da cidade: "19:23" significa 19:23 la. */
  sunrise: string;
  sunset: string;
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
  /** As 24 horas do dia corrente, 00:00 a 23:00 — nao uma janela rolante. */
  hourly: HourlyPoint[];
  /** Sete dias, comecando hoje. */
  daily: DailyPoint[];
  sun: Sun;
  units: Units;
  attribution: string;
};
