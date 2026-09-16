"""Costura HTTP de `/api/condicoes`: um item por dia que dispara.

O oposto do dedup que `test_condicoes.py` verifica. Os limiares e a
calibracao sao os mesmos — importados de `condicoes.py`, nao reescritos — e o
que muda e so o corte: aqui nao ha `also_days` nem `MAXIMO_DE_CARDS`.
"""

import httpx
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services.open_meteo import FORECAST_URL
from tests.fixtures import (
    DAILY_CAIRO,
    DAILY_MIAMI,
    DAILY_REYKJAVIK,
    DAILY_WELLINGTON,
    forecast_com_daily,
)

client = TestClient(app)

BERLIM = {"latitude": 52.52437, "longitude": 13.41053}


def _condicoes(daily: dict) -> list[dict]:
    payload = forecast_com_daily(daily)
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))
    return client.get("/api/condicoes", params=BERLIM).json()["condicoes"]


@respx.mock
def test_wellington_produz_cinco_itens_de_vento_um_por_dia():
    """A regressao inversa da do painel: aqui os cinco dias contam, nao um."""
    condicoes = _condicoes(DAILY_WELLINGTON)

    assert [item["kind"] for item in condicoes] == ["wind"] * 5
    assert [item["date"] for item in condicoes] == [
        "2026-09-15",
        "2026-09-16",
        "2026-09-17",
        "2026-09-19",
        "2026-09-20",
    ]


@respx.mock
def test_um_dia_que_dispara_duas_categorias_produz_dois_itens():
    """Reykjavik tem vento e chuva no mesmo dia — dois itens, mesma data."""
    condicoes = _condicoes(DAILY_REYKJAVIK)

    mesma_data = [item for item in condicoes if item["date"] == "2026-09-16"]
    assert {item["kind"] for item in mesma_data} == {"wind", "rain"}


@respx.mock
def test_dias_de_categorias_diferentes_nao_tem_teto():
    """Miami dispara chuva num dia e tempestade noutro: os dois aparecem,
    sem o corte de `MAXIMO_DE_CARDS` que o painel aplica."""
    condicoes = _condicoes(DAILY_MIAMI)

    assert [item["kind"] for item in condicoes] == ["rain", "storm"]
    assert [item["date"] for item in condicoes] == sorted(
        item["date"] for item in condicoes
    )


@respx.mock
def test_semana_tranquila_produz_lista_vazia():
    assert _condicoes(DAILY_CAIRO) == []


@respx.mock
def test_itens_saem_em_ordem_cronologica():
    condicoes = _condicoes(DAILY_WELLINGTON)

    assert [item["date"] for item in condicoes] == sorted(
        item["date"] for item in condicoes
    )


@respx.mock
def test_cada_item_traz_dia_categoria_e_o_valor_que_disparou():
    vento = _condicoes(DAILY_WELLINGTON)[0]

    assert vento["kind"] == "wind"
    assert vento["date"] == "2026-09-15"
    assert vento["label"] == "Vento forte"
    assert "km/h" in vento["detail"]


@respx.mock
def test_o_payload_traz_a_atribuicao():
    payload = forecast_com_daily(DAILY_CAIRO)
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))

    assert client.get("/api/condicoes", params=BERLIM).json()["attribution"]


@respx.mock
def test_reaproveita_o_cache_de_weather_sem_chamada_extra():
    """`/api/weather` popula o cache; `/api/condicoes` na mesma coordenada nao
    deveria bater na API externa de novo."""
    payload = forecast_com_daily(DAILY_WELLINGTON)
    rota = respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))

    client.get(
        "/api/weather",
        params={
            **BERLIM,
            "name": "Berlin",
            "country": "Germany",
            "country_code": "DE",
        },
    )
    chamadas_apos_weather = rota.call_count

    client.get("/api/condicoes", params=BERLIM)

    assert rota.call_count == chamadas_apos_weather


@respx.mock
def test_coordenada_fora_do_globo_e_422():
    assert client.get("/api/condicoes", params={"latitude": 91, "longitude": 0}).status_code == 422


@respx.mock
def test_api_externa_fora_do_ar_vira_503_com_mensagem_legivel():
    respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("sem rede"))

    resposta = client.get("/api/condicoes", params=BERLIM)

    assert resposta.status_code == 503
    assert resposta.json()["detail"]
