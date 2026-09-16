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
export type CondicaoPrevista = {
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
  /**
   * Exatas, sem o arredondamento de `distance_km`: sao as que a selecao usou
   * para medir a distancia, e o que permite marcar a cidade num mapa.
   */
  latitude: number;
  longitude: number;
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

/**
 * Um alerta do INMET que cobre a cidade escolhida.
 *
 * O que uma `CondicaoPrevista` nao pode ter: severidade oficial, janela de
 * validade declarada por quem emitiu, e recomendacoes de seguranca. Sem
 * `kind` — e o que distingue este tipo de `CondicaoPrevista` num slot do
 * painel sem precisar de um campo discriminador a mais.
 */
export type AlertaOficial = {
  id: string;
  tipo: string;
  severidade: string;
  /** 1 a 8, crescente com a gravidade. A interface anuncia `severidade` como
   * texto sempre — isto so ordena quando ha mais de um alerta ativo. */
  id_severidade: number;
  /** A cor oficial do INMET, em hexadecimal (`#FFFE00` para Perigo Potencial). */
  cor: string;
  inicio: string;
  fim: string;
  riscos: string;
  /** As recomendacoes de seguranca — atras de um expandir, recolhidas por padrao. */
  instrucoes: string;
};

/**
 * Um dos dois slots do card de condicoes do painel.
 *
 * Uniao, e nao um campo `tipo` extra: os dois formatos ja divergem o
 * suficiente (severidade oficial de um lado, `also_days` do outro) para que
 * a presenca de `kind` seja o discriminador. Ver `AlertaOficial`.
 */
export type PainelSlot = AlertaOficial | CondicaoPrevista;

/**
 * Os tres estados da secao de alertas oficiais, nunca colapsados entre si.
 *
 * `"ok"` e "consultamos o INMET" — a lista pode estar vazia (sem alerta
 * ativo) ou nao. `"fora_de_cobertura"` e "fora do Brasil, nao consultamos":
 * a ausencia de alerta aqui nao afirma seguranca nenhuma. `"indisponivel"` e
 * "consultamos e falhou": o mesmo cuidado, por um motivo diferente. Ver o
 * verbete *Alerta* do `CONTEXT.md`.
 */
export type StatusDosAlertas = "ok" | "fora_de_cobertura" | "indisponivel";

/**
 * A pagina Condicoes: alertas oficiais do INMET e condicoes previstas.
 *
 * Duas secoes, nao uma lista (ADR 0007). `condicoes` e o oposto do bloco
 * homonimo do painel — a mesma forma de `CondicaoPrevista` (`also_days`
 * sempre `0` aqui, porque cada dia ja e o seu proprio item).
 */
export type CondicoesResponse = {
  /** Os avisos do INMET que cobrem a cidade escolhida. Vazia tanto com `ok`
   * sem alerta ativo quanto com `fora_de_cobertura` ou `indisponivel` — o
   * que ela significa depende de `status_dos_alertas`, nunca da lista sozinha. */
  alertas: AlertaOficial[];
  status_dos_alertas: StatusDosAlertas;
  /** Um item por dia que dispara, em ordem cronologica. Vazia numa semana calma. */
  condicoes: CondicaoPrevista[];
  attribution: string;
};

/**
 * Uma materia de clima ou meio ambiente, vinda de feed publico.
 *
 * **O unico conteudo do app que nao e sobre a cidade escolhida.** Nao e dado
 * meteorologico: ninguem a calculou, ela nao descreve cidade nenhuma e nada no
 * app depende dela (ver o verbete *Noticia* do `CONTEXT.md`). Dai nao haver
 * coordenada nem unidade em campo algum daqui.
 */
export type Noticia = {
  titulo: string;
  /**
   * Quem publicou. **Sempre exibido**, nunca opcional: a licenca pede credito,
   * e numa lista que mistura agencia publica, ONG e revista cientifica quem
   * publicou e parte da informacao (ADR 0009).
   */
  veiculo: string;
  /** A materia no site do veiculo. */
  link: string;
  /**
   * Quando o veiculo publicou, em ISO **com fuso** — diferente de todo o resto
   * do payload, cujos horarios sao de parede e sem sufixo. Aqui ha fuso porque
   * os feeds divergem (`-0300` e `+0000`) e porque a data nao pertence a
   * cidade nenhuma.
   */
  publicada_em: string;
  /** A chamada da materia, ja como texto corrido. Vazia quando o feed nao traz. */
  resumo: string;
};

/**
 * Os dois estados da pagina Noticias, **nunca colapsados** entre si.
 *
 * `"ok"` cobre inclusive a lista vazia: tres feeds que responderam sem materia
 * sao um dia calmo. `"indisponivel"` e so quando **nenhum** veiculo respondeu —
 * ali a lista vazia nao diz "nao ha noticia", diz "nao ha como saber". O mesmo
 * cuidado de `StatusDosAlertas`, pelo mesmo motivo (ADR 0009).
 */
export type StatusDasNoticias = "ok" | "indisponivel";

/**
 * A pagina Noticias: as materias dos tres veiculos, ja agregadas.
 *
 * **Sem `location` e sem `units`** — e a unica resposta do backend que nao e
 * sobre uma cidade. As noticias sao nacionais e nao ha filtro regional
 * (ADR 0009).
 */
export type NoticiasResponse = {
  /** Em ordem cronologica decrescente, misturando os veiculos. */
  noticias: Noticia[];
  status: StatusDasNoticias;
  /**
   * Os veiculos que nao responderam; vazio no caminho normal. Nomeados, e nao
   * contados: e o que explica a quem le por que a lista esta curta.
   */
  veiculos_fora_do_ar: string[];
  attribution: string;
};

export type WeatherResponse = {
  location: Location;
  current: Current;
  /** As 24 horas do dia corrente, 00:00 a 23:00 — nao uma janela rolante. */
  hourly: HourlyPoint[];
  /** Sete dias, comecando hoje. */
  daily: DailyPoint[];
  sun: Sun;
  /** No maximo duas aqui — o teto e do layout deste painel, nao do dado.
   * Alerta oficial tem precedencia sobre condicao prevista nos dois slots
   * (ADR 0007): quando ha alerta, ele entra primeiro. Lista vazia e o
   * caminho normal, nao erro. */
  condicoes: PainelSlot[];
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

/**
 * A conta como a API a devolve: o e-mail, e nada mais.
 *
 * Espelha `ContaSaida` do backend. Nao ha `id` — os locais salvos vem da
 * sessao, nunca de um identificador que o cliente informe — e nao ha senha
 * nem hash em resposta alguma.
 */
export type Conta = {
  email: string;
};

/**
 * Quem esta pedindo, ou `null`.
 *
 * O envelope com um campo espelha `QuemSouResponse`: "nao ha sessao" e um
 * **valor** que se le, e nao um status que o cliente precise tratar como
 * falha. Visitante sem conta e o estado normal de quem nunca entrou.
 */
export type QuemSouResponse = {
  conta: Conta | null;
};
