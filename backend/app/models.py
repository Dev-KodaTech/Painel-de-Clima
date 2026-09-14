"""Modelos Pydantic que espelham o payload 1:1.

Servem de contrato e geram o schema OpenAPI. Esta fatia cobre `location`,
`current`, `units` e `attribution`; os blocos `hourly`, `daily`, `sun`,
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


class Units(BaseModel):
    temperature: str
    precipitation: str
    wind_speed: str
    distance: str


class WeatherResponse(BaseModel):
    """O painel. Um objeto por painel da interface.

    Nesta fatia so `location`, `current`, `units` e `attribution`; os demais
    blocos entram conforme os paineis forem construidos.
    """

    location: Location
    current: Current
    units: Units
    attribution: str
