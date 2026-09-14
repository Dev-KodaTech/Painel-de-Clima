"""Costura HTTP de `/api/cities`: busca, ambiguidade e cidade inexistente."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services.open_meteo import GEOCODING_URL
from tests.fixtures import (
    GEOCODING_BERLIM,
    GEOCODING_PAPEETE,
    GEOCODING_SPRINGFIELD,
    GEOCODING_VAZIO,
)

client = TestClient(app)


@pytest.fixture(scope="module")
def com_dataset():
    """Um cliente com o dataset local carregado, via `lifespan`.

    `TestClient(app)` **nao** roda o `lifespan`: so o gerenciador de contexto o
    faz. Sem ele o dataset fica vazio e o modo coordenada devolveria lista
    vazia para qualquer lugar — inclusive o centro de Berlim, passando pelo
    teste da coordenada remota pelo motivo errado.

    Por modulo: sao ~200 ms de carga, e paga-los por teste nao testa nada a
    mais.
    """
    with TestClient(app) as cliente:
        yield cliente


@respx.mock
def test_cidade_encontrada_devolve_candidata_com_nome_estado_e_pais():
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODING_BERLIM)
    )

    response = client.get("/api/cities", params={"q": "Berlim"})

    assert response.status_code == 200
    (cidade,) = response.json()["results"]
    assert cidade["name"] == "Berlin"
    assert cidade["admin1"] == "Land Berlin"
    assert cidade["country"] == "Germany"
    assert cidade["population"] == 3426354


@respx.mock
def test_cidade_nao_encontrada_devolve_lista_vazia_e_nao_excecao():
    """A API externa omite a chave `results` quando nada casa.

    Acessa-la direto levantaria `KeyError`; o esperado e uma resposta bem
    formada com lista vazia, que a interface exibe como "nao encontrada".
    """
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODING_VAZIO)
    )

    response = client.get("/api/cities", params={"q": "zzzqqqxyz"})

    assert response.status_code == 200
    assert response.json() == {"results": []}


@respx.mock
def test_nome_ambiguo_devolve_todas_as_candidatas_distinguiveis():
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODING_SPRINGFIELD)
    )

    response = client.get("/api/cities", params={"q": "Springfield"})

    candidatas = response.json()["results"]
    assert len(candidatas) == 3
    # Cada candidata carrega o que permite escolher entre homonimas.
    estados = [candidata["admin1"] for candidata in candidatas]
    assert estados == ["Missouri", "Illinois", "Massachusetts"]
    assert all(candidata["country"] == "United States" for candidata in candidatas)
    # Populacao ausente em lugares pequenos nao quebra a resposta.
    assert candidatas[2]["population"] is None


def test_busca_com_termo_vazio_e_rejeitada():
    """`q` vazio nao e busca: seria um pedido do dataset inteiro."""
    assert client.get("/api/cities", params={"q": ""}).status_code == 400


@respx.mock
def test_api_externa_fora_do_ar_vira_mensagem_compreensivel():
    respx.get(GEOCODING_URL).mock(side_effect=httpx.ConnectError("sem rede"))

    response = client.get("/api/cities", params={"q": "Berlim"})

    assert response.status_code == 503
    assert "indisponivel" in response.json()["detail"]


@respx.mock
def test_territorio_sem_nome_de_pais_ainda_vira_candidata():
    """**Armadilha da API**: a chave `country` some para territorios.

    Papeete (PF), Noumea (NC), Hong Kong (HK), Macau (MO) e Saint-Denis (RE)
    voltam sem ela — como `results` some quando nada casa. A candidata precisa
    sobreviver a ausencia: sem ela nao ha o que escolher, e Papeete e o caso de
    cidade isolada que o painel de vizinhas existe para servir.
    """
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODING_PAPEETE)
    )

    response = client.get("/api/cities", params={"q": "Papeete"})

    assert response.status_code == 200
    (candidata,) = response.json()["results"]
    assert candidata["name"] == "Papeete"
    # A sigla sempre vem, e e ela que identifica o lugar na ausencia do nome.
    assert candidata["country_code"] == "PF"
    assert candidata["country"] == ""


def test_coordenada_urbana_devolve_uma_candidata_do_dataset_local(com_dataset):
    """O modo coordenada nao chama a API externa: o dataset ja esta carregado.

    Sem `respx.mock` de proposito — qualquer requisicao de rede aqui seria a
    prova de que o reverse geocoding vazou para fora do processo.
    """
    response = com_dataset.get(
        "/api/cities", params={"lat": 52.52437, "lon": 13.41053}
    )

    assert response.status_code == 200
    (candidata,) = response.json()["results"]
    assert candidata["country_code"] == "DE"
    assert candidata["timezone"] == "Europe/Berlin"


def test_coordenada_remota_devolve_lista_vazia(com_dataset):
    """Acima de 50 km nada e sugerido: o painel cai no estado inicial.

    Meio do Pacifico — a cidade mais proxima esta a 1.043 km.
    """
    response = com_dataset.get("/api/cities", params={"lat": -10.0, "lon": -140.0})

    assert response.status_code == 200
    assert response.json() == {"results": []}


@pytest.mark.parametrize(
    ("caso", "params"),
    [
        ("nenhum dos dois", {}),
        ("ambos", {"q": "Berlim", "lat": 52.5, "lon": 13.4}),
        ("lat sem lon", {"lat": 52.5}),
        ("lon sem lat", {"lon": 13.4}),
        # `q` vazio com coordenada continua sendo "ambos os modos": o erro e a
        # ambiguidade, e responder `422` por causa do vazio esconderia isso.
        ("q vazio com coordenada", {"q": "", "lat": 52.5, "lon": 13.4}),
    ],
)
def test_q_e_coordenada_sao_mutuamente_exclusivos(caso, params):
    """`400`, e nao um dos dois modos escolhido em silencio.

    Adivinhar a intencao aqui esconderia um bug do chamador: o par `lat`/`lon`
    incompleto e tipicamente uma coordenada que se perdeu no caminho, e
    responder com a busca por texto devolveria a cidade errada sem sinal algum.
    """
    assert client.get("/api/cities", params=params).status_code == 400


@pytest.mark.parametrize(
    ("caso", "params"),
    [
        ("latitude fora da faixa", {"lat": 91.0, "lon": 0.0}),
        ("longitude fora da faixa", {"lat": 0.0, "lon": 181.0}),
    ],
)
def test_coordenada_fora_da_faixa_e_rejeitada(caso, params):
    assert client.get("/api/cities", params=params).status_code == 422
