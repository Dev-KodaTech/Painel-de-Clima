"""Costura HTTP de `/api/weather`: os blocos do painel e as armadilhas de fuso."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services.open_meteo import FORECAST_URL
from tests.fixtures import (
    DIAS_DA_PREVISAO,
    FORECAST_BERLIM,
    TEMPERATURAS_DIA_CORRENTE,
)

client = TestClient(app)

BERLIM = {
    "latitude": 52.52437,
    "longitude": 13.41053,
    "name": "Berlin",
    "country": "Germany",
    "country_code": "DE",
    "admin1": "Land Berlin",
}


def _mock_forecast(payload=None):
    return respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=payload or FORECAST_BERLIM)
    )


@respx.mock
def test_painel_traz_os_blocos_desta_fatia():
    _mock_forecast()

    corpo = client.get("/api/weather", params=BERLIM).json()

    assert set(corpo) == {
        "location",
        "current",
        "hourly",
        "daily",
        "sun",
        "units",
        "attribution",
    }
    assert corpo["units"] == {
        "temperature": "°C",
        "precipitation": "mm",
        "wind_speed": "km/h",
        "distance": "km",
    }
    assert corpo["attribution"]


@respx.mock
def test_location_confirma_a_cidade_pedida():
    _mock_forecast()

    location = client.get("/api/weather", params=BERLIM).json()["location"]

    assert location["name"] == "Berlin"
    assert location["country"] == "Germany"
    assert location["admin1"] == "Land Berlin"


@respx.mock
def test_current_traduz_o_codigo_wmo_em_texto_e_icone():
    """O frontend nunca ve o inteiro cru: a tabela WMO mora no backend."""
    _mock_forecast()

    current = client.get("/api/weather", params=BERLIM).json()["current"]

    assert current["weather_code"] == 3
    assert current["description"] == "Nublado"
    assert current["icon"] == "overcast"


@respx.mock
def test_current_usa_o_icone_noturno_quando_is_day_e_zero():
    """`is_day` vem como inteiro e escolhe a variante do icone."""
    noturno = {
        **FORECAST_BERLIM,
        "current": {**FORECAST_BERLIM["current"], "weather_code": 0, "is_day": 0},
    }
    _mock_forecast(noturno)

    current = client.get("/api/weather", params=BERLIM).json()["current"]

    assert current["is_day"] is False
    assert current["icon"] == "clear-night"


@respx.mock
def test_high_e_low_vem_do_bloco_diario():
    """A API externa nao fornece maxima e minima em `current`."""
    _mock_forecast()

    current = client.get("/api/weather", params=BERLIM).json()["current"]

    assert current["high"] == 17.2
    assert current["low"] == 13.7
    # A temperatura de agora e outra coisa, e nao se confunde com os extremos.
    assert current["temperature"] == 16.5
    assert current["apparent_temperature"] == 16.9


@respx.mock
def test_fuso_sobrevive_ao_trajeto_sem_deslocamento():
    """Timestamp sem sufixo e horario de parede da cidade, nao UTC.

    Interpreta-lo como UTC deslocaria o horario em duas horas em Berlim.
    """
    _mock_forecast()

    corpo = client.get("/api/weather", params=BERLIM).json()

    assert corpo["current"]["observed_at"] == "2026-09-14T03:00"
    assert corpo["location"]["timezone"] == "Europe/Berlin"
    assert corpo["location"]["utc_offset_seconds"] == 7200


@respx.mock
def test_codigo_wmo_desconhecido_degrada_sem_derrubar_o_painel():
    desconhecido = {
        **FORECAST_BERLIM,
        "current": {**FORECAST_BERLIM["current"], "weather_code": 42},
    }
    _mock_forecast(desconhecido)

    response = client.get("/api/weather", params=BERLIM)

    assert response.status_code == 200
    assert response.json()["current"]["description"] == "Condicao desconhecida"


@respx.mock
def test_api_externa_fora_do_ar_vira_mensagem_compreensivel():
    respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("sem rede"))

    response = client.get("/api/weather", params=BERLIM)

    assert response.status_code == 503
    assert "indisponivel" in response.json()["detail"]


def test_coordenada_invalida_e_rejeitada():
    assert client.get("/api/weather", params={**BERLIM, "latitude": 91}).status_code == 422


@pytest.mark.parametrize("ausente", ["name", "country", "country_code"])
def test_identidade_incompleta_e_rejeitada(ausente):
    """`location` existe para o usuario confirmar a cidade que pediu.

    Com pais em branco ela nao confirmaria nada, entao o endpoint recusa em
    vez de devolver um painel rotulado pela metade.
    """
    params = {campo: valor for campo, valor in BERLIM.items() if campo != ausente}

    assert client.get("/api/weather", params=params).status_code == 422


@respx.mock
def test_hourly_traz_as_24_horas_do_dia_corrente():
    """Nao uma janela rolante a partir de agora: o dia inteiro, 00:00 a 23:00.

    A API externa devolve 168 pontos para sete dias de previsao. Recortar a
    partir de "agora" faria o grafico comecar em lugar diferente a cada hora do
    dia; recortar do dia corrente casa com o design, que mostra 0h a 23h.
    """
    _mock_forecast()

    hourly = client.get("/api/weather", params=BERLIM).json()["hourly"]

    assert len(hourly) == 24
    assert hourly[0]["time"] == "2026-09-14T00:00"
    assert hourly[-1]["time"] == "2026-09-14T23:00"
    assert [ponto["temperature"] for ponto in hourly] == TEMPERATURAS_DIA_CORRENTE


@respx.mock
def test_hourly_recorta_o_dia_corrente_mesmo_quando_agora_e_o_fim_do_dia():
    """As 23:00 o grafico continua sendo o dia inteiro, quase todo passado."""
    fim_do_dia = {
        **FORECAST_BERLIM,
        "current": {**FORECAST_BERLIM["current"], "time": "2026-09-14T23:00"},
    }
    _mock_forecast(fim_do_dia)

    hourly = client.get("/api/weather", params=BERLIM).json()["hourly"]

    assert len(hourly) == 24
    assert hourly[0]["time"] == "2026-09-14T00:00"


@respx.mock
def test_daily_traz_sete_dias_com_icone_e_extremos():
    _mock_forecast()

    daily = client.get("/api/weather", params=BERLIM).json()["daily"]

    assert len(daily) == 7
    assert daily[0] == {
        "date": "2026-09-14",
        "weather_code": 3,
        "description": "Nublado",
        "icon": "overcast",
        "high": 17.2,
        "low": 13.7,
        "precipitation_mm": 0.0,
    }
    assert [dia["date"] for dia in daily] == DIAS_DA_PREVISAO


@respx.mock
def test_daily_usa_sempre_o_icone_diurno():
    """O card de um dia inteiro nao tem noite: `is_day` nao se aplica.

    O terceiro dia e tempestade (95) e o sexto chuva fraca (61); ambos tem
    icone unico, mas o primeiro dia (nublado) prova a escolha diurna porque a
    leitura atual e noturna (`is_day: 0`) e o dia nao a herda.
    """
    _mock_forecast()

    corpo = client.get("/api/weather", params=BERLIM).json()

    assert corpo["current"]["is_day"] is False
    assert corpo["daily"][2]["icon"] == "thunderstorms"
    assert corpo["daily"][5]["icon"] == "rain"


@respx.mock
def test_sun_traz_nascer_e_por_do_sol_do_dia_corrente():
    """Do primeiro dia do bloco diario, nao de um dia qualquer da semana."""
    _mock_forecast()

    sun = client.get("/api/weather", params=BERLIM).json()["sun"]

    assert sun == {"sunrise": "2026-09-14T06:38", "sunset": "2026-09-14T19:23"}


@respx.mock
def test_horarios_do_sol_sobrevivem_ao_trajeto_sem_deslocamento():
    """Berlim esta a UTC+2: reinterpretar como UTC adiantaria o por do sol.

    A armadilha vale para todo timestamp do payload, nao so para `observed_at`.
    """
    _mock_forecast()

    corpo = client.get("/api/weather", params=BERLIM).json()

    assert corpo["sun"]["sunset"].endswith("19:23")
    assert "Z" not in corpo["sun"]["sunset"]
    assert "+" not in corpo["sun"]["sunset"]
    assert corpo["hourly"][6]["time"] == "2026-09-14T06:00"
