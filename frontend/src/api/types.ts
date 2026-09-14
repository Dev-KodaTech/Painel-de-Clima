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

/**
 * Uma condicao severa **derivada da previsao**, nao um alerta oficial.
 *
 * A distincao nao e formalidade: alerta meteorologico e a categoria de
 * informacao em que pessoas tomam decisao de seguranca, e a fonte aqui nao e
 * defesa civil. A interface rotula cada card como derivado.
 */
export type Alerta = {
  kind: "storm" | "wind" | "rain";
  /** Data local da cidade do dia representado. */
  date: string;
  label: string;
  icon: string;
  /** O valor que disparou, ja em texto: "Rajadas de 86 km/h". */
  detail: string;
  /**
   * Quantos **outros** dias disparam a mesma categoria. Ha um card por
   * categoria: sem esta contagem, os demais dias sumiriam sem deixar rastro.
   */
  also_days: number;
};

/**
 * Uma cidade vizinha, selecionada por aneis sobre o dataset local do backend.
 *
 * `distance_km` nao e opcional: numa cidade isolada as vizinhas sao distantes,
 * e "Auckland — 4.094 km" e honesto onde "Auckland" sozinha sugeriria uma
 * vizinhanca que nao existe.
 */
export type Nearby = {
  name: string;
  country_code: string;
  distance_km: number;
  temperature: number;
  weather_code: number;
  description: string;
  icon: string;
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
  /** No maximo duas. Lista vazia e o caminho normal, nao erro. */
  alerts: Alerta[];
  /** De quatro a cinco, da mais perto para a mais longe. */
  nearby: Nearby[];
  units: Units;
  attribution: string;
};
