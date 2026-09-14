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


def test_busca_sem_termo_e_rejeitada():
    assert client.get("/api/cities").status_code == 422


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
