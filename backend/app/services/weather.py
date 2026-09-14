"""Monta o payload do painel a partir das respostas da API externa."""

import httpx

from app.models import (
    ATRIBUICAO,
    UNIDADES_PADRAO,
    Cidade,
    CidadeEscolhida,
    Current,
    Location,
    Units,
    WeatherResponse,
)
from app.services import open_meteo
from app.services.wmo import traduzir


def para_cidade(bruto: dict) -> Cidade:
    """Converte uma candidata do geocoding no modelo.

    `admin1` e `population` faltam para lugares pequenos; o modelo os aceita
    como nulos e a interface omite o que nao veio.
    """
    return Cidade(
        id=bruto["id"],
        name=bruto["name"],
        country=bruto.get("country", ""),
        country_code=bruto.get("country_code", ""),
        admin1=bruto.get("admin1"),
        latitude=bruto["latitude"],
        longitude=bruto["longitude"],
        population=bruto.get("population"),
        timezone=bruto.get("timezone", "UTC"),
    )


async def buscar_candidatas(client: httpx.AsyncClient, q: str) -> list[Cidade]:
    brutas = await open_meteo.buscar_cidades(client, q)
    return [para_cidade(bruta) for bruta in brutas]


async def montar_painel(
    client: httpx.AsyncClient, cidade: CidadeEscolhida
) -> WeatherResponse:
    """Busca a previsao e monta o painel para uma cidade ja escolhida.

    A coordenada vem da propria cidade: passa-la em separado abriria a
    possibilidade de buscar o tempo de um lugar e rotula-lo com o nome de
    outro.
    """
    previsao = await open_meteo.buscar_previsao(
        client, cidade.latitude, cidade.longitude
    )
    return _montar(previsao, cidade)


def _montar(previsao: dict, cidade: CidadeEscolhida) -> WeatherResponse:
    current = previsao["current"]
    daily = previsao["daily"]

    # `is_day` vem como inteiro (0/1), nao booleano.
    is_day = bool(current["is_day"])
    description, icon = traduzir(current["weather_code"], is_day)

    return WeatherResponse(
        location=Location(
            name=cidade.name,
            country=cidade.country,
            country_code=cidade.country_code,
            admin1=cidade.admin1,
            # A coordenada da resposta, nao a pedida: a API externa arredonda
            # para a celula da grade que de fato usou.
            latitude=previsao["latitude"],
            longitude=previsao["longitude"],
            timezone=previsao["timezone"],
            utc_offset_seconds=previsao["utc_offset_seconds"],
        ),
        current=Current(
            # Viaja exatamente como veio: horario de parede da cidade, sem
            # sufixo de fuso. Reinterpreta-lo como UTC deslocaria tudo.
            observed_at=current["time"],
            temperature=current["temperature_2m"],
            apparent_temperature=current["apparent_temperature"],
            weather_code=current["weather_code"],
            description=description,
            icon=icon,
            is_day=is_day,
            # Do bloco diario: a API nao fornece maxima e minima em `current`.
            high=daily["temperature_2m_max"][0],
            low=daily["temperature_2m_min"][0],
        ),
        units=Units(**UNIDADES_PADRAO),
        attribution=ATRIBUICAO,
    )
