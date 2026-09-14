"""Modelos Pydantic que espelham o payload 1:1.

Servem de contrato e geram o schema OpenAPI. Esta fatia cobre `location`,
`current`, `hourly`, `daily`, `sun`, `units` e `attribution`; os blocos
`alerts` e `nearby` entram nos tickets seguintes.
"""

from pydantic import BaseModel, Field

#: Fixo no payload, e nao escrito no frontend: assim a interface nunca tem
#: unidade em codigo. A escolha de unidade e do backend.
UNIDADES_PADRAO = {
    "temperature": "°C",
    "precipitation": "mm",
    "wind_speed": "km/h",
    "distance": "km",
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


class Units(BaseModel):
    temperature: str
    precipitation: str
    wind_speed: str
    distance: str


class WeatherResponse(BaseModel):
    """O painel. Um objeto por painel da interface.

    Nesta fatia faltam `alerts` e `nearby`, que entram com os paineis de
    condicoes previstas e cidades proximas.
    """

    location: Location
    current: Current
    hourly: list[HourlyPoint]
    daily: list[DailyPoint]
    sun: Sun
    units: Units
    attribution: str
