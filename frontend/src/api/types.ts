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

/**
 * O que `/api/weather` precisa saber de uma cidade — menos que uma `Cidade`.
 *
 * Existe porque a cidade escolhida viaja pela URL, e a URL nao carrega
 * `id`, `population` nem `timezone`: nenhum deles vai na requisicao do painel.
 * Uma `Cidade` inteira continua servindo, por ser mais larga que isto.
 */
export type CidadeDoPainel = Pick<
  Cidade,
  "latitude" | "longitude" | "name" | "country" | "country_code" | "admin1"
>;

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
  /** Inteiro: a distancia e estimada sobre a esfera e vem arredondada ao km. */
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
  /** Ate cinco, da mais perto para a mais longe. Pode ter menos numa cidade
   * cujas vizinhas acabam antes — Honolulu tem quatro. */
  nearby: Nearby[];
  units: Units;
  attribution: string;
};

/**
 * A janela temporal que a pagina Tendencia analisa.
 *
 * Uniao fechada, nao `string`: o backend a valida como `Literal` e rejeita
 * qualquer outra coisa com 422. Aqui o mesmo conjunto impede que uma janela
 * inventada chegue a compilar.
 */
export type Janela = "7d" | "30d" | "6m";

/** As datas das duas janelas, prontas para exibir — a interface nao as recalcula. */
export type Periodo = {
  janela: Janela;
  /** `2026-08-17`: primeiro dia da janela atual. */
  inicio: string;
  fim: string;
  inicio_anterior: string;
  fim_anterior: string;
};

/**
 * Um dia do historico climatologico: **medicao**, nao previsao.
 *
 * Todo campo fora de `date` e opcional porque o arquivo tem buracos nas
 * bordas: um dia sem uma variavel entra na serie com o campo nulo, em vez de
 * sumir e levar os outros quatro valores junto.
 */
export type DiaDoHistorico = {
  /** Data local da cidade (`2026-09-14`). */
  date: string;
  high: number | null;
  low: number | null;
  precipitation_mm: number | null;
  /** Umidade relativa media do dia, em %. */
  humidity: number | null;
  wind_speed: number | null;
  /** Direcao dominante em graus; `rumo_dominante` do resumo a traduz. */
  wind_direction: number | null;
};

export type PontoDeUv = {
  /** Horario de parede da cidade (`2026-09-15T13:00`), como todo timestamp. */
  time: string;
  uv: number;
};

/**
 * O indice UV — **so do futuro**, e por isso um bloco irmao de `serie`.
 *
 * A reanalise do passado nao mede UV. A consequencia e regra de produto: o UV
 * nunca entra na comparacao com o ano anterior e nunca cobre 30 dias ou 6
 * meses. `nota` traz o texto que diz isso na tela.
 */
export type Uv = {
  /** O dia corrente, hora a hora. Vazio quando a previsao nao o traz. */
  horas: PontoDeUv[];
  maximo_da_semana: number | null;
  nota: string;
};

/**
 * Os numeros prontos da janela, calculados no backend.
 *
 * Nulos, e nao zeros, quando falta o dado: uma media de lista vazia seria `0`,
 * que se le como "fez zero grau".
 */
export type ResumoDoHistorico = {
  chuva_total_mm: number | null;
  chuva_total_anterior_mm: number | null;
  /** Dias em que choveu: 60 mm em tres dias e 60 mm em vinte sao diferentes. */
  dias_com_chuva: number;
  umidade_minima: number | null;
  umidade_media: number | null;
  umidade_maxima: number | null;
  vento_maximo: number | null;
  direcao_dominante: number | null;
  /** A mesma direcao em ponto cardeal (`NO`), ja pronta para ler. */
  rumo_dominante: string | null;
  temperatura_media: number | null;
  temperatura_media_anterior: number | null;
  /** Positivo = a janela atual esta mais quente que o mesmo periodo de 2025. */
  diferenca_media: number | null;
};

/** As unidades do historico. `uv` e vazia: o indice nao tem unidade. */
export type UnitsDoHistorico = {
  temperature: string;
  precipitation: string;
  wind_speed: string;
  humidity: string;
  uv: string;
};

/** O historico climatologico de uma cidade. Um bloco por parte da pagina. */
export type TrendsResponse = {
  periodo: Periodo;
  serie: DiaDoHistorico[];
  /** Vazia quando o arquivo nao cobre o ano anterior — normal, nao erro. */
  comparacao: DiaDoHistorico[];
  uv: Uv;
  resumo: ResumoDoHistorico;
  units: UnitsDoHistorico;
  attribution: string;
};
