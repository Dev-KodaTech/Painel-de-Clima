"""O cache visto de fora: quantas chamadas externas duas consultas produzem.

Esta e a costura que o ticket pede — nenhum teste aqui espia o interior do
cache. O que se observa e o contador de requisicoes do `respx`, que e
exatamente a cota que o cache existe para poupar.

O relogio e injetado para a expiracao; nao ha `sleep` algum.
"""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services import open_meteo
from app.services.cache import Cache
from app.services.open_meteo import FORECAST_URL
from tests.fixtures import FORECAST_BERLIM

client = TestClient(app)

BERLIM = {
    "latitude": 52.52437,
    "longitude": 13.41053,
    "name": "Berlin",
    "country": "Germany",
    "country_code": "DE",
    "admin1": "Land Berlin",
}

#: A mesma cidade com a precisao que outra candidata traria. Arredondadas a
#: duas casas (~1,1 km), as duas sao a mesma chave.
BERLIM_QUASE_IGUAL = {**BERLIM, "latitude": 52.5244, "longitude": 13.4105}


class _Relogio:
    """Relogio injetado, avancado a mao."""

    def __init__(self) -> None:
        self.instante = 0.0

    def __call__(self) -> float:
        return self.instante

    def avancar(self, segundos: float) -> None:
        self.instante += segundos


@pytest.fixture
def relogio(monkeypatch):
    """Substitui o cache do processo por um com relogio sob controle.

    O cache e estado de processo compartilhado: sem a troca, uma entrada
    deixada por um teste serviria o seguinte, e a ordem de execucao mudaria o
    resultado.
    """
    relogio = _Relogio()
    monkeypatch.setattr(open_meteo, "cache", Cache(ttl_segundos=600, agora=relogio))
    return relogio


@respx.mock
def test_duas_consultas_iguais_produzem_uma_chamada_externa(relogio):
    """O caso que justifica o cache: a segunda consulta nao gasta cota."""
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    assert client.get("/api/weather", params=BERLIM).status_code == 200
    assert client.get("/api/weather", params=BERLIM).status_code == 200

    assert rota.call_count == 1


@respx.mock
def test_apos_o_ttl_a_consulta_volta_a_bater_na_api(relogio):
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    client.get("/api/weather", params=BERLIM)
    relogio.avancar(601)
    client.get("/api/weather", params=BERLIM)

    assert rota.call_count == 2


@respx.mock
def test_coordenadas_proximas_compartilham_a_entrada(relogio):
    """A mesma cidade vinda de duas candidatas nao vira duas chamadas."""
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    client.get("/api/weather", params=BERLIM)
    client.get("/api/weather", params=BERLIM_QUASE_IGUAL)

    assert rota.call_count == 1


@respx.mock
def test_cidades_distintas_nao_compartilham_a_entrada(relogio):
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    client.get("/api/weather", params=BERLIM)
    client.get(
        "/api/weather",
        params={**BERLIM, "latitude": 48.85341, "longitude": 2.3488, "name": "Paris"},
    )

    assert rota.call_count == 2


@respx.mock
def test_a_consulta_servida_do_cache_devolve_o_mesmo_painel(relogio):
    """Servir do cache nao pode mudar o que o usuario ve."""
    respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    primeira = client.get("/api/weather", params=BERLIM).json()
    segunda = client.get("/api/weather", params=BERLIM).json()

    assert primeira == segunda


@respx.mock
def test_falha_da_api_nao_fica_cacheada(relogio):
    """Uma indisponibilidade passageira nao pode prender o painel por 10 min."""
    rota = respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("sem rede"))

    assert client.get("/api/weather", params=BERLIM).status_code == 503

    rota.mock(return_value=httpx.Response(200, json=FORECAST_BERLIM))

    assert client.get("/api/weather", params=BERLIM).status_code == 200
