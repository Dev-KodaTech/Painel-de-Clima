"""Modelos Pydantic que espelham o payload 1:1.

Servem de contrato e geram o schema OpenAPI. Esta fatia cobre `location`,
`current`, `hourly`, `daily`, `sun`, `alerts`, `units` e `attribution`; o
bloco `nearby` entra no ticket seguinte.
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


class Alerta(BaseModel):
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


class Units(BaseModel):
    temperature: str
    precipitation: str
    wind_speed: str
    distance: str


class WeatherResponse(BaseModel):
    """O painel. Um objeto por painel da interface.

    Nesta fatia falta `nearby`, que entra com o painel de cidades proximas.
    """

    location: Location
    current: Current
    hourly: list[HourlyPoint]
    daily: list[DailyPoint]
    sun: Sun
    alerts: list[Alerta] = Field(
        description=(
            "Condicoes severas previstas, no maximo duas. Lista vazia e o "
            "caminho normal, nao erro: duas das seis cidades da amostra caem "
            "nele, e o painel mostra o estado vazio em vez de sumir."
        )
    )
    units: Units
    attribution: str
