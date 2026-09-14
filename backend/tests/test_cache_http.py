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

from app import cache_do_processo
from app.main import app
from app.services.cache import Cache
from app.services.open_meteo import FORECAST_URL
from tests.conftest import Relogio
from tests.fixtures import FORECAST_BERLIM, atual_de_varias

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


@pytest.fixture
def relogio():
    """Substitui o cache do processo por um com relogio sob controle.

    O cache e estado de processo compartilhado: sem a troca, uma entrada
    deixada por um teste serviria o seguinte, e a ordem de execucao mudaria o
    resultado.
    """
    relogio = Relogio()
    original = cache_do_processo.atual()
    cache_do_processo.substituir(Cache(ttl_segundos=600, agora=relogio))
    yield relogio
    cache_do_processo.substituir(original)


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


@pytest.fixture
def app_com_dataset():
    """O app com o `lifespan` executado, e portanto com o dataset carregado.

    Sem ele a lista de cidades fica vazia, o bloco `nearby` sai vazio e a
    **segunda** chamada externa nunca acontece — os testes acima contam so a da
    previsao, ainda que as duas batam na mesma URL.
    """
    with TestClient(app) as cliente:
        yield cliente


def _mockar_as_duas_chamadas():
    """As duas chamadas batem na mesma URL e se distinguem pelos parametros.

    A da previsao pede sete dias; a das vizinhas pede um. Contar as duas
    separadamente e o que torna visivel que o cache cobre **as duas**, e nao
    so a cara.
    """
    previsao = respx.get(FORECAST_URL, params__contains={"forecast_days": "7"}).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )
    vizinhas = respx.get(FORECAST_URL, params__contains={"forecast_days": "1"}).mock(
        return_value=httpx.Response(200, json=atual_de_varias(TEMPERATURAS_VIZINHAS))
    )
    return previsao, vizinhas


#: Uma por vizinha de Berlim, todas distintas.
TEMPERATURAS_VIZINHAS = [11.1, 12.2, 13.3, 14.4, 15.5]


@respx.mock
def test_o_cache_cobre_tambem_a_chamada_das_vizinhas(relogio, app_com_dataset):
    """Ambas as chamadas externas sao poupadas, nao apenas a da previsao."""
    previsao, vizinhas = _mockar_as_duas_chamadas()

    primeiro = app_com_dataset.get("/api/weather", params=BERLIM).json()
    segundo = app_com_dataset.get("/api/weather", params=BERLIM).json()

    # A primeira consulta faz as duas; a segunda, nenhuma.
    assert previsao.call_count == 1
    assert vizinhas.call_count == 1
    # E a tabela servida do cache continua preenchida e igual.
    assert len(segundo["nearby"]) == 5
    assert primeiro["nearby"] == segundo["nearby"]


@respx.mock
def test_apos_o_ttl_as_duas_chamadas_sao_refeitas(relogio, app_com_dataset):
    previsao, vizinhas = _mockar_as_duas_chamadas()

    app_com_dataset.get("/api/weather", params=BERLIM)
    relogio.avancar(601)
    app_com_dataset.get("/api/weather", params=BERLIM)

    assert previsao.call_count == 2
    assert vizinhas.call_count == 2
