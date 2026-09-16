"""Costura HTTP da pagina Noticias: `/api/noticias`.

`test_noticias.py` cobre o agregador isolado (parsing, ordem, falha parcial);
aqui o que se verifica e o que o endpoint faz com o resultado dele — o payload,
a atribuicao que nomeia os veiculos e a **ausencia de `503`**, que e a decisao
mais facil de desfazer por engano numa mudanca futura.
"""

import httpx
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services import noticias
from tests.conftest import mockar_todos_os_feeds, resposta_de_feed
from tests.fixtures_rss import FEED_FAPESP, FEED_OBSERVATORIO

client = TestClient(app)


@respx.mock
def test_devolve_as_noticias_agregadas():
    mockar_todos_os_feeds()

    corpo = client.get("/api/noticias").json()

    assert corpo["status"] == "ok"
    assert corpo["veiculos_fora_do_ar"] == []
    assert len(corpo["noticias"]) == 6

    item = corpo["noticias"][0]
    # Os cinco campos que a pagina promete de cada linha.
    assert set(item) == {"titulo", "veiculo", "link", "publicada_em", "resumo"}


@respx.mock
def test_o_endpoint_nao_pede_cidade():
    """A unica rota do backend **sem** coordenada — e o teste que a protege.

    As noticias sao nacionais (ADR 0009). Se alguem acrescentar `latitude` por
    simetria com o resto da API, isto quebra: uma coordenada obrigatoria viraria
    `422` e a pagina passaria a exigir uma cidade que ela nao usa.
    """
    mockar_todos_os_feeds()

    assert client.get("/api/noticias").status_code == 200


@respx.mock
def test_um_feed_fora_do_ar_ainda_responde_200():
    """Nao ha `503` parcial: as materias dos outros dois continuam servidas."""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(return_value=httpx.Response(500))
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.PESQUISA_FAPESP.url).mock(return_value=resposta_de_feed(FEED_FAPESP))

    resposta = client.get("/api/noticias")
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["status"] == "ok"
    assert corpo["veiculos_fora_do_ar"] == [noticias.AGENCIA_BRASIL.veiculo]
    assert len(corpo["noticias"]) == 4


@respx.mock
def test_todos_fora_do_ar_responde_200_com_status_indisponivel():
    """**Nao** e `503`: o estado viaja no corpo, para a pagina o distinguir.

    Um `503` aqui daria a pagina a mesma mensagem generica que a falha de rede
    produz, e perderia a diferenca entre "nenhum veiculo respondeu" e "nao ha
    materia" — que e a distincao inteira que `status` existe para carregar.
    """
    for feed in noticias.FEEDS:
        respx.get(feed.url).mock(side_effect=httpx.ConnectError("sem rede"))

    resposta = client.get("/api/noticias")
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["status"] == "indisponivel"
    assert corpo["noticias"] == []
    assert corpo["veiculos_fora_do_ar"] == [feed.veiculo for feed in noticias.FEEDS]
    # Sem procedencia, sem credito. Uma linha generica ali creditaria
    # justamente quem nao forneceu nada — a imprecisao que a atribuicao por
    # veiculo existe para evitar.
    assert corpo["attribution"] == ""


@respx.mock
def test_a_atribuicao_nomeia_os_veiculos():
    """A licenca pede credito, e o credito e por veiculo (ADR 0009)."""
    mockar_todos_os_feeds()

    corpo = client.get("/api/noticias").json()

    for feed in noticias.FEEDS:
        assert feed.veiculo in corpo["attribution"]


@respx.mock
def test_a_atribuicao_omite_o_veiculo_que_nao_respondeu():
    """Creditar quem nao forneceu materia alguma afirmaria uma procedencia falsa."""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(side_effect=httpx.ConnectError("x"))
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.PESQUISA_FAPESP.url).mock(return_value=resposta_de_feed(FEED_FAPESP))

    atribuicao = client.get("/api/noticias").json()["attribution"]

    assert noticias.AGENCIA_BRASIL.veiculo not in atribuicao
    assert noticias.OBSERVATORIO_DO_CLIMA.veiculo in atribuicao


@respx.mock
def test_a_atribuicao_nao_cita_a_open_meteo_nem_o_geonames():
    """A unica resposta do app que **nao** os credita, porque nao os consulta."""
    mockar_todos_os_feeds()

    atribuicao = client.get("/api/noticias").json()["attribution"]

    assert "Open-Meteo" not in atribuicao
    assert "GeoNames" not in atribuicao
