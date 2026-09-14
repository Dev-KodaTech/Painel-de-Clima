"""Costura HTTP do bloco `nearby`: a tabela de cidades vizinhas.

Estes testes sobem o app **com `lifespan`** (`with TestClient(app)`), o que
carrega o dataset de verdade. Sem isso a lista de cidades fica vazia e o bloco
sai vazio sem erro algum — o painel pareceria certo e a tabela nunca teria
dados.

A selecao em si tem costura propria em `test_vizinhas.py`, sobre a funcao pura.
Aqui o que se verifica e o trajeto: duas chamadas, o casamento posicional entre
cidade e leitura, e a distancia obrigatoria no payload.
"""

import httpx
import pytest
import respx

from app.services.open_meteo import FORECAST_URL
from tests.fixtures import FORECAST_BERLIM, atual_de_varias
from tests.test_weather import BERLIM

#: Uma por vizinha esperada, todas distintas: uma correspondencia trocada
#: aparece como a temperatura errada na linha errada, nao como um empate.
TEMPERATURAS = [11.1, 12.2, 13.3, 14.4, 15.5]


@pytest.fixture
def app_com_dataset():
    """O app com o `lifespan` executado, e portanto com o dataset carregado."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


def _mockar_as_duas_chamadas(temperaturas=None):
    """As duas chamadas batem na **mesma** URL e se distinguem pelos parametros.

    A da previsao pede sete dias (`forecast_days=7`) e um bloco `hourly`; a das
    vizinhas pede um dia e nenhum. E o que permite devolver os dois formatos
    diferentes — objeto e array — para o mesmo endpoint, e e tambem a prova de
    que sao mesmo duas chamadas distintas.

    A rota mais especifica vem primeiro: o respx casa na ordem de registro.
    """
    respx.get(FORECAST_URL, params__contains={"forecast_days": "7"}).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )
    return respx.get(FORECAST_URL, params__contains={"forecast_days": "1"}).mock(
        return_value=httpx.Response(
            200, json=atual_de_varias(temperaturas or TEMPERATURAS)
        )
    )


@respx.mock
def test_nearby_traz_as_vizinhas_com_distancia_e_temperatura(app_com_dataset):
    _mockar_as_duas_chamadas()

    nearby = app_com_dataset.get("/api/weather", params=BERLIM).json()["nearby"]

    assert len(nearby) == 5
    for vizinha in nearby:
        assert vizinha["name"]
        assert vizinha["country_code"]
        # Obrigatoria: sem ela, "Auckland" no painel de Papeete sugeriria uma
        # vizinhanca que nao existe.
        assert vizinha["distance_km"] > 0
        assert vizinha["description"]
        assert vizinha["icon"]


@respx.mock
def test_nearby_de_berlim_sao_cidades_reais_e_nao_bairros(app_com_dataset):
    """O mesmo criterio da costura pura, visto pela ponta do endpoint."""
    _mockar_as_duas_chamadas()

    nearby = app_com_dataset.get("/api/weather", params=BERLIM).json()["nearby"]
    nomes = [vizinha["name"] for vizinha in nearby]

    assert "Potsdam" in nomes
    assert "Kreuzberg" not in nomes
    assert "Berlin" not in nomes


@respx.mock
def test_cada_vizinha_recebe_a_leitura_da_sua_posicao(app_com_dataset):
    """A resposta multi-coordenada nao repete o nome: a ordem e o vinculo.

    Trocar a ordem exibiria a temperatura de uma cidade sob o nome de outra —
    um erro silencioso, porque todos os valores continuariam plausiveis.
    """
    _mockar_as_duas_chamadas()

    nearby = app_com_dataset.get("/api/weather", params=BERLIM).json()["nearby"]

    assert [vizinha["temperature"] for vizinha in nearby] == TEMPERATURAS


@respx.mock
def test_vizinhas_vem_da_mais_perto_para_a_mais_longe(app_com_dataset):
    _mockar_as_duas_chamadas()

    nearby = app_com_dataset.get("/api/weather", params=BERLIM).json()["nearby"]
    distancias = [vizinha["distance_km"] for vizinha in nearby]

    assert distancias == sorted(distancias)


@respx.mock
def test_a_segunda_chamada_pede_apenas_current(app_com_dataset):
    """**77% menos banda**: o painel inteiro para seis coordenadas pesaria
    32.791 bytes contra os 7.417 destas duas chamadas.

    A tabela mostra so a temperatura de agora; pedir previsao para as vizinhas
    traria sete dias que ninguem le.
    """
    rota = _mockar_as_duas_chamadas()

    app_com_dataset.get("/api/weather", params=BERLIM)

    params = rota.calls.last.request.url.params
    assert "daily" not in params
    assert "hourly" not in params
    assert params["current"] == "temperature_2m,weather_code,is_day"


@respx.mock
def test_a_segunda_chamada_leva_as_cinco_coordenadas_de_uma_vez(app_com_dataset):
    """Uma requisicao para as cinco, nao cinco requisicoes."""
    rota = _mockar_as_duas_chamadas()

    app_com_dataset.get("/api/weather", params=BERLIM)

    params = rota.calls.last.request.url.params
    assert len(params["latitude"].split(",")) == 5
    assert len(params["longitude"].split(",")) == 5
    assert rota.call_count == 1


@respx.mock
def test_nearby_traduz_o_codigo_wmo_como_o_resto_do_painel(app_com_dataset):
    """O frontend nao conhece a tabela WMO em lugar algum do payload."""
    _mockar_as_duas_chamadas()

    nearby = app_com_dataset.get("/api/weather", params=BERLIM).json()["nearby"]

    assert nearby[0]["weather_code"] == 3
    assert nearby[0]["description"] == "Nublado"
    assert nearby[0]["icon"] == "overcast"


@respx.mock
def test_resposta_mais_curta_que_o_pedido_nao_desalinha_as_linhas(app_com_dataset):
    """Menos leituras que cidades rende menos linhas, nunca um par trocado.

    Preencher as faltantes com a leitura seguinte poria a temperatura de uma
    cidade sob o nome de outra — e nada no payload denunciaria a troca.
    """
    _mockar_as_duas_chamadas(temperaturas=[11.1, 12.2])

    nearby = app_com_dataset.get("/api/weather", params=BERLIM).json()["nearby"]

    assert [vizinha["temperature"] for vizinha in nearby] == [11.1, 12.2]


def test_sem_dataset_carregado_o_painel_nao_cai(monkeypatch):
    """Degrada para tabela vazia em vez de derrubar os outros oito paineis.

    O dataset e estado do processo, carregado pelo `lifespan`. Este teste o
    zera explicitamente em vez de contar com um app montado sem `lifespan`:
    outro teste do modulo ja o carregou, e o estado sobrevive entre eles — a
    ausencia precisa ser encenada, nao suposta.

    Sem cidades nao ha coordenada a pedir, e a segunda chamada nem acontece.
    """
    from fastapi.testclient import TestClient

    from app import dataset
    from app.main import app

    monkeypatch.setattr(dataset, "_cidades", [])

    with respx.mock:
        rota = respx.get(FORECAST_URL).mock(
            return_value=httpx.Response(200, json=FORECAST_BERLIM)
        )
        response = TestClient(app).get("/api/weather", params=BERLIM)

    assert response.status_code == 200
    assert response.json()["nearby"] == []
    # Uma so chamada: sem vizinhas, a segunda seria uma requisicao sem
    # coordenada alguma, que a API externa recusaria com `400`.
    assert rota.call_count == 1
