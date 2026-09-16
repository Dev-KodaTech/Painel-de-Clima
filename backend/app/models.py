"""Modelos Pydantic que espelham o payload 1:1.

Servem de contrato e geram o schema OpenAPI.
"""

from typing import Literal

from pydantic import BaseModel, Field

#: Fixo no payload, e nao escrito no frontend: assim a interface nunca tem
#: unidade em codigo. A escolha de unidade e do backend.
UNIDADES_PADRAO = {
    "temperature": "°C",
    "precipitation": "mm",
    "wind_speed": "km/h",
    "distance": "km",
}

#: As unidades do historico. Repete as tres do painel e acrescenta duas.
#:
#: `uv` e string vazia de proposito: o indice UV **nao tem unidade**, e um
#: rotulo ali faria a interface exibir "7 UV". Vazio e o fato, e a interface
#: concatena sem caso especial.
UNIDADES_DO_HISTORICO = {
    "temperature": "°C",
    "precipitation": "mm",
    "wind_speed": "km/h",
    "humidity": "%",
    "uv": "",
}

#: Exigido por CC-BY 4.0 pela Open-Meteo e pelo GeoNames. String pronta, para
#: que o frontend nao monte texto de licenca.
ATRIBUICAO = "Dados: Open-Meteo.com (CC BY 4.0) · Cidades: GeoNames (CC BY 4.0)"


class Cidade(BaseModel):
    """Uma cidade candidata: resultado de geocodificacao ainda nao escolhido.

    `admin1` e `population` podem faltar — a Open-Meteo omite ambos para
    lugares pequenos —, e sao o que permite distinguir candidatas homonimas.
    """

    id: int
    name: str
    country: str
    country_code: str
    admin1: str | None = None
    latitude: float
    longitude: float
    population: int | None = None
    timezone: str


class CidadesResponse(BaseModel):
    results: list[Cidade]


class CidadeEscolhida(BaseModel):
    """A cidade que o usuario escolheu entre as candidatas.

    Distinta de `Cidade`: aqui nao ha `id`, `population` nem `timezone`, que
    servem para *escolher* entre candidatas e nao dizem nada depois da
    escolha. O fuso do painel vem da previsao, nao daqui.
    """

    name: str
    country: str
    country_code: str
    admin1: str | None = None
    latitude: float
    longitude: float


class Location(BaseModel):
    """A cidade exibida, com o fuso que rege todos os horarios do payload."""

    name: str
    country: str
    country_code: str
    admin1: str | None = None
    latitude: float
    longitude: float
    timezone: str
    utc_offset_seconds: int


class Current(BaseModel):
    """Condicoes atuais.

    `high` e `low` vem do bloco **diario** da API externa, nao do atual: a
    Open-Meteo nao os fornece em `current`, embora o design os mostre no card
    de hoje.
    """

    observed_at: str = Field(
        description="Horario local de parede, sem sufixo de fuso, como veio da API."
    )
    temperature: float
    apparent_temperature: float
    weather_code: int
    description: str
    icon: str
    is_day: bool
    high: float
    low: float


class HourlyPoint(BaseModel):
    """Um ponto do grafico de tendencia: a temperatura de uma hora."""

    time: str = Field(
        description="Horario local de parede, sem sufixo de fuso (`2026-09-14T15:00`)."
    )
    temperature: float


class DailyPoint(BaseModel):
    """Um dia da previsao da semana.

    Um unico bloco `daily` alimenta dois paineis — previsao da semana e
    precipitacao —, porque o design mostra os mesmos sete dias em ambos.
    """

    date: str = Field(description="Data local da cidade (`2026-09-14`), sem horario.")
    weather_code: int
    description: str
    icon: str
    high: float
    low: float
    precipitation_mm: float


class Sun(BaseModel):
    """Nascer e por do sol do dia corrente, no fuso da cidade."""

    sunrise: str
    sunset: str


class CondicaoPrevista(BaseModel):
    """Uma condicao severa **derivada da previsao**, nao um alerta oficial.

    A Open-Meteo nao tem alertas meteorologicos, e a distincao importa: alerta
    e a categoria de informacao em que pessoas tomam decisao de seguranca. O
    payload nao esconde a origem — a interface rotula cada card como derivado.

    O card mostra categoria, data e o valor da metrica que disparou, e nao a
    temperatura que o design de referencia exibe: maxima e minima nada dizem
    sobre vento ou tempestade.
    """

    # Literal, e nao `str`: as tres categorias sao fechadas, e o schema
    # OpenAPI passa a carregar o enum que o frontend ja declara como uniao.
    kind: Literal["storm", "wind", "rain"]
    date: str = Field(description="Data local da cidade do dia representado.")
    label: str
    icon: str
    detail: str = Field(
        description="O valor que disparou, ja em texto: `Rajadas de 86 km/h`."
    )
    also_days: int = Field(
        description=(
            "Quantos outros dias da semana disparam a mesma categoria. Existe "
            "porque ha **um card por categoria**: sem esta contagem, os demais "
            "dias sumiriam sem deixar rastro."
        )
    )


class Nearby(BaseModel):
    """Uma cidade vizinha, selecionada por aneis sobre o dataset local.

    `distance_km` e **obrigatorio**, nao enfeite: para uma cidade isolada,
    "Auckland — 4.094 km" e honesto, e o mesmo item sem a distancia seria
    enganoso — sugeriria uma vizinhanca que nao existe.
    """

    name: str
    country_code: str
    # Exatas como o dataset as traz, sem o arredondamento que `distance_km`
    # sofre: a distancia e um numero lido, e a coordenada e consumida por um
    # mapa. Arredonda-la poria o marcador longe do ponto que mediu a distancia.
    latitude: float
    longitude: float
    # Inteiro, e nao `float`: a distancia e estimada sobre a esfera e exibida
    # arredondada ao km. Declara-la fracionaria prometeria uma precisao que o
    # valor nao tem e que ninguem le.
    distance_km: int = Field(
        description="Distancia em linha reta ate a cidade consultada, em km."
    )
    temperature: float
    weather_code: int
    description: str
    icon: str


class Units(BaseModel):
    temperature: str
    precipitation: str
    wind_speed: str
    distance: str


class WeatherResponse(BaseModel):
    """O painel. Um objeto por painel da interface."""

    location: Location
    current: Current
    hourly: list[HourlyPoint]
    daily: list[DailyPoint]
    sun: Sun
    condicoes: list[CondicaoPrevista] = Field(
        description=(
            "Condicoes severas previstas. No maximo duas aqui — o teto e do "
            "layout deste painel, nao do dado. Lista vazia e o caminho "
            "normal, nao erro: duas das seis cidades da amostra caem nele, e "
            "o painel mostra o estado vazio em vez de sumir."
        )
    )
    nearby: list[Nearby] = Field(
        description=(
            "Ate cinco cidades vizinhas, da mais perto para a mais longe. "
            "Numa cidade isolada elas sao distantes, e a distancia obrigatoria "
            "de cada item e o que torna a comparacao honesta; quando a lista "
            "so poderia ser completada por uma cidade solta — Honolulu e o "
            "continente —, ela termina antes."
        )
    )
    units: Units
    attribution: str


class CondicoesResponse(BaseModel):
    """A pagina Condicoes: um item por dia que dispara, sem dedup nem teto.

    O oposto do bloco `condicoes` do painel. La o teto e o dedup existem para
    caber em dois cards de altura fixa; aqui nao ha layout a proteger, entao a
    semana de Wellington chega como cinco itens de vento, um por dia.
    """

    condicoes: list[CondicaoPrevista] = Field(
        description=(
            "Um item por dia que dispara uma categoria, em ordem cronologica. "
            "Um dia que dispara duas categorias produz dois itens. Lista "
            "vazia e o caminho normal numa semana calma, nao erro."
        )
    )
    attribution: str


#: As tres janelas temporais que a pagina Tendencia analisa. Conjunto fechado,
#: e nao um numero de dias livre: `janela` entra por parametro de URL, e um
#: valor livre viraria aritmetica de data com entrada arbitraria — "6000d" e
#: uma requisicao de dezesseis anos a API externa.
Janela = Literal["7d", "30d", "6m"]


class Periodo(BaseModel):
    """As datas das duas janelas que a pagina compara.

    Existe para que a interface **nao recalcule datas**: "30 dias" termina
    ontem ou hoje conforme o arquivo, e refazer essa conta no frontend seria um
    segundo lugar para ela estar errada.
    """

    janela: Janela
    inicio: str = Field(description="Primeiro dia da janela atual (`2026-08-17`).")
    fim: str = Field(description="Ultimo dia da janela atual.")
    inicio_anterior: str = Field(
        description="Primeiro dia da mesma janela no ano anterior."
    )
    fim_anterior: str


class DiaDoHistorico(BaseModel):
    """Um dia do historico climatologico: medicao, nao previsao.

    Nao ha `weather_code` nem icone aqui: a reanalise nao os fornece, e o que a
    pagina exibe sao series numericas, nao cards de condicao.

    Todo campo fora de `date` e opcional porque o arquivo e **incompleto nas
    bordas**: um dia sem medicao vem como `null`, e descartar o dia inteiro por
    causa de uma variavel faltando esconderia os outros quatro valores dele.
    """

    date: str = Field(description="Data local da cidade (`2026-09-14`).")
    high: float | None = None
    low: float | None = None
    precipitation_mm: float | None = None
    humidity: float | None = Field(
        default=None, description="Umidade relativa media do dia, em %."
    )
    wind_speed: float | None = Field(
        default=None, description="Velocidade maxima do vento do dia."
    )
    wind_direction: float | None = Field(
        default=None, description="Direcao dominante do vento, em graus."
    )


class PontoDeUv(BaseModel):
    """O indice UV de uma hora."""

    time: str = Field(description="Horario de parede da cidade (`2026-09-15T13:00`).")
    uv: float


class Uv(BaseModel):
    """O indice UV — **so do futuro**, e por isso um bloco irmao de `serie`.

    A reanalise ERA5 nao tem UV: o arquivo aceita `uv_index_max` e devolve
    `null` para todos os dias, com unidade `"undefined"`. Medido contra o
    servico real.

    A consequencia e regra de produto, nao detalhe: o UV **nunca** participa da
    comparacao com o ano anterior e **nunca** cobre 30 dias ou 6 meses. Um
    campo dentro de `serie` seria `null` em 173 dos 180 pontos e todo consumidor
    teria de saber disso; a forma do payload e que deve carregar o fato.
    """

    horas: list[PontoDeUv] = Field(
        description="O dia corrente, hora a hora. Vazio quando a previsao nao o traz."
    )
    maximo_da_semana: float | None = Field(
        default=None, description="O maior indice dos sete dias previstos."
    )
    nota: str = Field(
        description="Por que o UV nao acompanha a janela, ja em texto para exibir."
    )


class ResumoDoHistorico(BaseModel):
    """Os numeros prontos da janela, calculados no backend.

    Media, acumulado e contagem sobre ate 180 pontos sao a mesma operacao para
    qualquer cliente; mante-las aqui evita que a pagina reimplemente estatistica
    — e que duas paginas a reimplementem de dois jeitos.

    Os campos sao opcionais porque uma janela sem dado algum nao tem media: uma
    media de lista vazia seria `0`, que se le como "fez zero grau".
    """

    chuva_total_mm: float | None = None
    chuva_total_anterior_mm: float | None = None
    dias_com_chuva: int = Field(
        description=(
            "Dias da janela em que choveu. Existe porque 60 mm em tres dias e "
            "60 mm em vinte dias sao periodos diferentes."
        )
    )
    umidade_minima: float | None = None
    umidade_media: float | None = None
    umidade_maxima: float | None = None
    vento_maximo: float | None = None
    direcao_dominante: float | None = Field(
        default=None, description="Direcao dominante do vento na janela, em graus."
    )
    rumo_dominante: str | None = Field(
        default=None,
        description=(
            "A mesma direcao em ponto cardeal (`NO`), porque 'noroeste' se le e "
            "'312°' se calcula."
        ),
    )
    temperatura_media: float | None = None
    temperatura_media_anterior: float | None = None
    diferenca_media: float | None = Field(
        default=None,
        description=(
            "Quanto a janela atual esta acima (positivo) ou abaixo do mesmo "
            "periodo do ano anterior. `null` quando falta um dos dois."
        ),
    )


class UnitsDoHistorico(BaseModel):
    """Como no painel, para que a interface nunca tenha unidade em codigo.

    Ganha `humidity` e `uv` em relacao as do painel; `uv` e string vazia porque
    o indice **nao tem unidade** — e um indice, e escrever "UV" ali faria a
    interface exibir "7 UV".
    """

    temperature: str
    precipitation: str
    wind_speed: str
    humidity: str
    uv: str


class TrendsResponse(BaseModel):
    """O historico climatologico de uma cidade. Um bloco por parte da pagina."""

    periodo: Periodo
    serie: list[DiaDoHistorico] = Field(
        description="Um ponto por dia da janela atual."
    )
    comparacao: list[DiaDoHistorico] = Field(
        description=(
            "A mesma forma, para o mesmo periodo do ano anterior. Lista vazia "
            "quando o arquivo nao cobre o periodo — caminho normal, nao erro: a "
            "pagina esconde a segunda serie e diz por que."
        )
    )
    uv: Uv
    resumo: ResumoDoHistorico
    units: UnitsDoHistorico
    attribution: str
