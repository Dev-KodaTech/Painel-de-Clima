"""Costura HTTP da secao de alertas oficiais: `/api/condicoes` e o painel.

`test_inmet.py` cobre o cliente isolado (dedup, poligono, cache); aqui o que
se verifica e o que os dois endpoints fazem com o resultado dele — os tres
estados da secao, a precedencia no painel e a atribuicao condicional.
"""

import httpx
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services import inmet
from app.services.open_meteo import FORECAST_URL
from tests.fixtures import (
    AVISO_INMET_PERIGO,
    AVISO_INMET_PERIGO_POTENCIAL,
    CURITIBA,
    DAILY_CAIRO,
    DAILY_WELLINGTON,
    SAO_PAULO,
    avisos_inmet,
    forecast_com_daily,
)

client = TestClient(app)

BERLIM = {"latitude": 52.52437, "longitude": 13.41053, "country_code": "DE"}


def _mockar_previsao(daily: dict = DAILY_CAIRO) -> None:
    payload = forecast_com_daily(daily)
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))


def _mockar_inmet(*avisos: dict) -> None:
    respx.get(inmet.ENDPOINT).mock(
        return_value=httpx.Response(200, json=avisos_inmet(*avisos))
    )


@respx.mock
def test_fora_do_brasil_o_status_e_fora_de_cobertura_e_o_inmet_nao_e_chamado():
    _mockar_previsao()
    rota_inmet = respx.get(inmet.ENDPOINT).mock(
        return_value=httpx.Response(200, json=avisos_inmet(AVISO_INMET_PERIGO))
    )

    resposta = client.get("/api/condicoes", params=BERLIM).json()

    assert resposta["status_dos_alertas"] == "fora_de_cobertura"
    assert resposta["alertas"] == []
    assert rota_inmet.call_count == 0


@respx.mock
def test_no_brasil_sem_alerta_ativo_o_status_e_ok_com_lista_vazia():
    _mockar_previsao()
    _mockar_inmet()  # nenhum aviso ativo

    resposta = client.get("/api/condicoes", params=CURITIBA).json()

    assert resposta["status_dos_alertas"] == "ok"
    assert resposta["alertas"] == []


@respx.mock
def test_no_brasil_com_alerta_cobrindo_a_cidade():
    _mockar_previsao()
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL)

    resposta = client.get("/api/condicoes", params=CURITIBA).json()

    assert resposta["status_dos_alertas"] == "ok"
    assert len(resposta["alertas"]) == 1
    alerta = resposta["alertas"][0]
    assert alerta["severidade"] == "Perigo Potencial"
    assert alerta["cor"] == "#FFFE00"
    assert alerta["riscos"]
    assert alerta["instrucoes"]


@respx.mock
def test_no_brasil_com_alerta_que_nao_cobre_a_cidade():
    """O aviso existe e esta ativo, mas o poligono nao alcanca Sao Paulo — a
    lista fica vazia com status `ok`, nao `fora_de_cobertura`: o Brasil foi
    consultado de verdade."""
    _mockar_previsao()
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL)

    resposta = client.get("/api/condicoes", params=SAO_PAULO).json()

    assert resposta["status_dos_alertas"] == "ok"
    assert resposta["alertas"] == []


@respx.mock
def test_falha_do_inmet_vira_status_indisponivel_sem_derrubar_a_pagina():
    """As condicoes previstas continuam mesmo com o INMET fora do ar (ADR 0008)."""
    _mockar_previsao(DAILY_WELLINGTON)
    respx.get(inmet.ENDPOINT).mock(side_effect=httpx.ConnectError("sem rede"))

    resposta = client.get("/api/condicoes", params=CURITIBA)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status_dos_alertas"] == "indisponivel"
    assert corpo["alertas"] == []
    assert corpo["condicoes"]  # Wellington dispara vento — a pagina nao esvaziou.


@respx.mock
def test_atribuicao_credita_o_inmet_so_quando_ha_alerta():
    _mockar_previsao()
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL)

    com_alerta = client.get("/api/condicoes", params=CURITIBA).json()["attribution"]
    assert "INMET" in com_alerta


@respx.mock
def test_atribuicao_nao_credita_o_inmet_sem_alerta():
    _mockar_previsao()
    _mockar_inmet()

    sem_alerta = client.get("/api/condicoes", params=CURITIBA).json()["attribution"]
    assert "INMET" not in sem_alerta


@respx.mock
def test_atribuicao_nao_credita_o_inmet_fora_do_brasil():
    _mockar_previsao()

    sem_cobertura = client.get("/api/condicoes", params=BERLIM).json()["attribution"]
    assert "INMET" not in sem_cobertura


@respx.mock
def test_codigo_do_pais_minusculo_ainda_consulta_o_inmet():
    """**Regressao.** `br` minusculo caia em "fora de cobertura" para uma
    coordenada brasileira — a falsa afirmacao de seguranca do ADR 0008,
    disparada pela caixa em vez da geografia."""
    _mockar_previsao()
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL)

    resposta = client.get(
        "/api/condicoes", params={**CURITIBA, "country_code": "br"}
    ).json()

    assert resposta["status_dos_alertas"] == "ok"
    assert len(resposta["alertas"]) == 1


@respx.mock
def test_feed_malformado_vira_indisponivel_e_nao_500():
    """**Regressao.** O feed e proprietario e sem versao: um campo que sumiu
    subia como `500` e derrubava a pagina inteira, em vez de virar "nao foi
    possivel consultar" (ADR 0008)."""
    _mockar_previsao(DAILY_WELLINGTON)
    sem_instrucoes = {
        chave: valor
        for chave, valor in AVISO_INMET_PERIGO_POTENCIAL.items()
        if chave != "instrucoes"
    }
    _mockar_inmet(sem_instrucoes)

    resposta = client.get("/api/condicoes", params=CURITIBA)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status_dos_alertas"] == "indisponivel"
    assert corpo["condicoes"]  # As condicoes previstas sobreviveram.


@respx.mock
def test_corpo_nao_json_vira_indisponivel_e_nao_500():
    """`response.json()` levanta `ValueError`, que nao e `httpx.HTTPError` —
    um proxy respondendo `200` com HTML derrubava a pagina."""
    _mockar_previsao(DAILY_WELLINGTON)
    respx.get(inmet.ENDPOINT).mock(
        return_value=httpx.Response(200, text="<html>erro do proxy</html>")
    )

    resposta = client.get("/api/condicoes", params=CURITIBA)

    assert resposta.status_code == 200
    assert resposta.json()["status_dos_alertas"] == "indisponivel"


# ---------------------------------------------------------------------------
# Precedencia no painel da Visao geral (ADR 0007)
# ---------------------------------------------------------------------------

CURITIBA_PAINEL = {
    "latitude": CURITIBA["latitude"],
    "longitude": CURITIBA["longitude"],
    "name": "Curitiba",
    "country": "Brazil",
    "country_code": "BR",
}


@respx.mock
def test_alerta_oficial_ocupa_o_primeiro_slot_do_painel():
    _mockar_previsao(DAILY_WELLINGTON)  # dispara condicao prevista de vento
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL)

    painel = client.get("/api/weather", params=CURITIBA_PAINEL).json()

    slots = painel["condicoes"]
    assert len(slots) == 2
    # O alerta nao tem `kind`: e o jeito de distinguir as duas formas no
    # payload sem campo discriminador extra.
    assert "kind" not in slots[0]
    assert slots[0]["severidade"] == "Perigo Potencial"
    assert slots[1]["kind"] == "wind"


@respx.mock
def test_sem_alerta_o_painel_mostra_so_condicoes_previstas():
    _mockar_previsao(DAILY_WELLINGTON)
    _mockar_inmet()

    painel = client.get("/api/weather", params=CURITIBA_PAINEL).json()

    slots = painel["condicoes"]
    assert all("kind" in slot for slot in slots)


@respx.mock
def test_painel_continua_com_no_maximo_dois_slots_mesmo_com_alerta():
    _mockar_previsao(DAILY_WELLINGTON)
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL, AVISO_INMET_PERIGO)

    painel = client.get("/api/weather", params=CURITIBA_PAINEL).json()

    assert len(painel["condicoes"]) == 2
    assert all("kind" not in slot for slot in painel["condicoes"])


@respx.mock
def test_painel_credita_o_inmet_quando_exibe_alerta():
    """**Regressao.** O painel exibia um card do INMET e nao o creditava: a
    atribuicao era montada sem `com_inmet`, e so `/api/condicoes` tinha sido
    atualizado."""
    _mockar_previsao(DAILY_WELLINGTON)
    _mockar_inmet(AVISO_INMET_PERIGO_POTENCIAL)

    painel = client.get("/api/weather", params=CURITIBA_PAINEL).json()

    assert "INMET" in painel["attribution"]


@respx.mock
def test_painel_nao_credita_o_inmet_sem_alerta():
    _mockar_previsao(DAILY_WELLINGTON)
    _mockar_inmet()

    painel = client.get("/api/weather", params=CURITIBA_PAINEL).json()

    assert "INMET" not in painel["attribution"]


@respx.mock
def test_falha_do_inmet_nao_derruba_o_painel():
    """O painel nao declara os tres estados — sao dois cards de altura fixa —,
    mas tampouco pode sumir porque o fornecedor secundario caiu."""
    _mockar_previsao(DAILY_WELLINGTON)
    respx.get(inmet.ENDPOINT).mock(side_effect=httpx.ConnectError("sem rede"))

    resposta = client.get("/api/weather", params=CURITIBA_PAINEL)

    assert resposta.status_code == 200
    painel = resposta.json()
    assert painel["condicoes"]  # As condicoes previstas continuam.
    assert "INMET" not in painel["attribution"]
