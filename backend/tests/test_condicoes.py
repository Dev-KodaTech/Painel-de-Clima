"""Costura HTTP das condicoes severas derivadas da previsao.

As seis cidades sao as mesmas sobre as quais os limiares foram calibrados, e
cada uma cobre um caso que a regra tem de acertar. O que se verifica e o que
sai do endpoint — nunca como a derivacao chegou la.
"""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services.open_meteo import FORECAST_URL
from tests.fixtures import (
    DAILY_CAIRO,
    DAILY_INNSBRUCK,
    DAILY_MIAMI,
    DAILY_REYKJAVIK,
    DAILY_SINGAPURA,
    DAILY_WELLINGTON,
    FORECAST_BERLIM,
    forecast_com_daily,
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


def _alertas(daily: dict | None = None) -> list[dict]:
    """O bloco `condicoes` do painel para uma semana de clima."""
    payload = forecast_com_daily(daily) if daily else FORECAST_BERLIM
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))
    return client.get("/api/weather", params=BERLIM).json()["condicoes"]


@respx.mock
def test_wellington_produz_um_card_de_vento_e_nao_cinco():
    """A regressao que motivou o dedup.

    Wellington tem rajada >= 60 km/h em cinco dos sete dias. Sem dedup por
    categoria, o painel receberia cinco cards identicos — numa cidade
    litoranea, vento forte e o clima normal, e repeti-lo cinco vezes e ruido.
    """
    alertas = _alertas(DAILY_WELLINGTON)

    assert [alerta["kind"] for alerta in alertas] == ["wind"]
    vento = alertas[0]
    # O pior dia, nao o primeiro a cruzar o limiar.
    assert vento["date"] == "2026-09-16"
    assert "86" in vento["detail"]
    # Quatro outros dias cruzaram o limiar e viraram uma linha, nao cards.
    assert vento["also_days"] == 4


@respx.mock
@pytest.mark.parametrize(
    ("cidade", "daily"),
    [("Cairo", DAILY_CAIRO), ("Singapura", DAILY_SINGAPURA)],
)
def test_semana_tranquila_produz_lista_vazia(cidade, daily):
    """O estado vazio e caminho normal: duas das seis cidades caem nele."""
    assert _alertas(daily) == []


@respx.mock
def test_miami_produz_dois_cards_distintos():
    """Chuva de 104,4 mm no primeiro dia e tempestade no sexto."""
    alertas = _alertas(DAILY_MIAMI)

    assert [alerta["kind"] for alerta in alertas] == ["rain", "storm"]
    assert alertas[0]["date"] == "2026-09-14"
    assert alertas[1]["date"] == "2026-09-19"


@respx.mock
def test_innsbruck_produz_so_a_tempestade():
    """Vento e chuva ficam abaixo do limiar: a categoria aparece sozinha."""
    alertas = _alertas(DAILY_INNSBRUCK)

    assert [alerta["kind"] for alerta in alertas] == ["storm"]
    assert alertas[0]["date"] == "2026-09-16"


@respx.mock
def test_reykjavik_produz_vento_e_chuva_do_mesmo_dia():
    alertas = _alertas(DAILY_REYKJAVIK)

    assert {alerta["kind"] for alerta in alertas} == {"wind", "rain"}
    assert all(alerta["date"] == "2026-09-16" for alerta in alertas)


@respx.mock
def test_alertas_saem_ordenados_por_data():
    """Miami tem chuva no dia 0 e tempestade no dia 5, nesta ordem."""
    alertas = _alertas(DAILY_MIAMI)

    assert [alerta["date"] for alerta in alertas] == sorted(
        alerta["date"] for alerta in alertas
    )


@respx.mock
def test_no_maximo_dois_cards_sao_exibidos():
    """Semana em que as tres categorias disparam, em dias distintos."""
    tres_categorias = {
        **DAILY_WELLINGTON,
        "weather_code": [95, 3, 51, 81, 51, 51, 51],
        "precipitation_sum": [0.0, 42.0, 0.4, 14.5, 0.3, 0.4, 0.2],
    }

    alertas = _alertas(tres_categorias)

    assert len(alertas) == 2
    # Os dois mais proximos: tempestade no dia 0, chuva no dia 1. O vento, cujo
    # pior dia e o terceiro, fica de fora.
    assert [alerta["kind"] for alerta in alertas] == ["storm", "rain"]


@respx.mock
@pytest.mark.parametrize(
    ("rajada", "esperado"),
    [(59.9, []), (60.0, ["wind"])],
)
def test_fronteira_do_limiar_de_vento(rajada, esperado):
    """60,0 km/h dispara; 59,9 nao. O limiar e >=, e nao aproximado."""
    semana = {
        **DAILY_CAIRO,
        "wind_gusts_10m_max": [rajada, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
    }

    assert [alerta["kind"] for alerta in _alertas(semana)] == esperado


@respx.mock
@pytest.mark.parametrize(
    ("chuva", "esperado"),
    [(19.9, []), (20.0, ["rain"])],
)
def test_fronteira_do_limiar_de_chuva(chuva, esperado):
    """20,0 mm dispara; 19,9 nao."""
    semana = {**DAILY_CAIRO, "precipitation_sum": [chuva, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}

    assert [alerta["kind"] for alerta in _alertas(semana)] == esperado


@respx.mock
def test_card_traz_rotulo_icone_e_valor_da_metrica():
    """Categoria, data e o valor que disparou — nao a temperatura do dia.

    O design de referencia poe uma temperatura grande no card de alerta, que
    nada diz sobre vento ou tempestade. O desvio e deliberado.
    """
    vento = _alertas(DAILY_WELLINGTON)[0]

    assert vento == {
        "kind": "wind",
        "date": "2026-09-16",
        "label": "Vento forte",
        "icon": "wind",
        "detail": "Rajadas de 86 km/h",
        "also_days": 4,
    }


@respx.mock
def test_tempestade_nao_traz_valor_de_metrica():
    """A tempestade vem de um codigo, nao de um numero: nao ha o que medir."""
    tempestade = _alertas(DAILY_INNSBRUCK)[0]

    assert tempestade["label"] == "Tempestade"
    assert tempestade["detail"] == "Tempestade com raios prevista"
    assert tempestade["also_days"] == 0
