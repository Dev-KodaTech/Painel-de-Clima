"""O endpoint de dezesseis dias da pagina Calendario.

O que se verifica aqui e a **fronteira do dia 8** vista de fora: que ela chega
ao frontend como campo declarado e nao como regra de indice, e que o horizonte
longo nao carrega o que a interface nao deve exibir.

A contagem de chamadas externas fica em `test_cache_http.py`, junto das demais
— e la que o `respx` ja e usado como contador de cota.
"""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services.open_meteo import FORECAST_URL, PRIMEIRO_DIA_DO_HORIZONTE_LONGO
from tests.fixtures import (
    FORECAST_DEZESSEIS_BERLIM,
    FORECAST_DEZESSEIS_COM_BORDA_INCOMPLETA,
)

client = TestClient(app)

BERLIM = {"latitude": 52.52437, "longitude": 13.41053}


@pytest.fixture
def horizonte():
    """O payload de `/api/horizonte` para Berlim, com a API externa mockada."""
    with respx.mock:
        respx.get(FORECAST_URL).mock(
            return_value=httpx.Response(200, json=FORECAST_DEZESSEIS_BERLIM)
        )
        resposta = client.get("/api/horizonte", params=BERLIM)

    assert resposta.status_code == 200
    return resposta.json()


def test_o_payload_traz_exatamente_dezesseis_dias(horizonte):
    """Dezesseis e o teto do endpoint, e a grade inteira conta com ele."""
    assert len(horizonte["dias"]) == 16


def test_os_sete_primeiros_sao_horizonte_curto_e_trazem_icone(horizonte):
    """O que a Visao geral ja mostra continua mostravel na grade."""
    curtos = horizonte["dias"][:PRIMEIRO_DIA_DO_HORIZONTE_LONGO]

    assert len(curtos) == 7
    for dia in curtos:
        assert dia["horizonte"] == "curto"
        assert dia["icon"]
        assert dia["description"]


def test_do_oitavo_em_diante_e_horizonte_longo_e_nao_ha_icone(horizonte):
    """**A regra que o backend faz valer, e nao o frontend.**

    O horizonte longo nao carrega `icon` nem `description`: enviar o dado e
    confiar que a interface o ignore e o erro que o campo `alerts` do ADR 0001
    cometeu — o dado sugere um uso que a regra proibe.
    """
    longos = horizonte["dias"][PRIMEIRO_DIA_DO_HORIZONTE_LONGO:]

    assert len(longos) == 9
    for dia in longos:
        assert dia["horizonte"] == "longo"
        assert dia["icon"] is None
        assert dia["description"] is None


def test_a_probabilidade_de_chuva_vem_em_todos_os_dias(horizonte):
    """A interface so a exibe no longo, mas o dado e o mesmo nos dois lados.

    Pedida para os dezesseis, e nao so para o lado que a exibe: e o mesmo campo,
    e recorta-lo no backend obrigaria a mexer aqui no dia em que a fronteira
    mudasse de lugar.
    """
    for dia in horizonte["dias"]:
        assert dia["precipitation_probability_max"] is not None


def test_o_horizonte_e_campo_declarado_e_nao_regra_de_indice(horizonte):
    """Cada dia diz a que horizonte pertence, sem o frontend redescobrir.

    Se a Open-Meteo mudar o encadeamento de modelos, o ajuste e aqui — e nao
    em dois lugares que precisariam concordar.
    """
    horizontes = [dia["horizonte"] for dia in horizonte["dias"]]

    assert horizontes == ["curto"] * 7 + ["longo"] * 9


def test_os_dias_vem_com_data_maxima_e_minima(horizonte):
    """A grade desenha os dezesseis; o que muda entre os lados e so o resto."""
    for dia in horizonte["dias"]:
        assert dia["date"]
        assert isinstance(dia["high"], float)
        assert isinstance(dia["low"], float)


def test_a_atribuicao_vem_da_funcao_e_nao_de_uma_constante(horizonte):
    """O padrao que a pagina Noticias estabeleceu: cada endpoint credita o seu.

    Sem INMET aqui — a pagina nao consulta alertas, e nomea-lo creditaria um
    fornecedor que nao forneceu nada.
    """
    assert "Open-Meteo.com" in horizonte["attribution"]
    assert "INMET" not in horizonte["attribution"]


@respx.mock
def test_a_borda_incompleta_nao_derruba_a_resposta():
    """**O caso que a fixture golden esconde**, medido no servico real.

    A API devolve as dezesseis datas e deixa os valores da ponta nulos, variando
    com a cidade e a hora local. Com maxima e minima obrigatorias, a validacao
    do Pydantic falhava e a pagina inteira abria em erro por causa de uma celula
    — e nenhum teste sobre a golden pegava isso.
    """
    respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(
            200, json=FORECAST_DEZESSEIS_COM_BORDA_INCOMPLETA
        )
    )

    resposta = client.get("/api/horizonte", params=BERLIM)

    assert resposta.status_code == 200

    dias = resposta.json()["dias"]
    # O dia continua na grade, com a data — o que falta e o valor, e some-lo
    # faria a contagem e a fronteira do dia 8 deixarem de casar.
    assert len(dias) == 16
    assert dias[-1]["date"]
    assert dias[-1]["high"] is None
    assert dias[-1]["horizonte"] == "longo"
    # E o penultimo, que so perdeu a probabilidade, conserva o resto.
    assert dias[-2]["precipitation_probability_max"] is None
    assert dias[-2]["high"] is not None


@respx.mock
def test_uma_janela_mais_curta_nao_vira_uma_grade_silenciosamente_menor():
    """Se a API devolver menos dias, o payload nao pode fingir que esta inteiro.

    A fronteira do dia 8 continuaria no lugar certo e a resposta continuaria
    valida — so que com menos celulas e sem explicacao. E o mesmo modo de
    falhar que a colisao de chave de cache produziria, entrando por outra porta.
    """
    truncada = {
        **FORECAST_DEZESSEIS_BERLIM,
        "daily": {
            campo: valores[:7]
            for campo, valores in FORECAST_DEZESSEIS_BERLIM["daily"].items()
        },
    }
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=truncada))

    resposta = client.get("/api/horizonte", params=BERLIM)

    # Nao ha o que exibir como grade de dezesseis: a API quebrou o contrato, e
    # isso e indisponibilidade do servico, nao uma pagina meio pronta.
    assert resposta.status_code == 503


@respx.mock
def test_falha_da_api_externa_vira_503_e_nao_500():
    """Como as demais rotas: a indisponibilidade e declarada, nao vazada."""
    respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("sem rede"))

    resposta = client.get("/api/horizonte", params=BERLIM)

    assert resposta.status_code == 503


@respx.mock
def test_coordenada_invalida_e_recusada_antes_da_chamada_externa():
    """A mesma validacao de coordenada das outras rotas, pelo Pydantic."""
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_DEZESSEIS_BERLIM)
    )

    resposta = client.get("/api/horizonte", params={"latitude": 91, "longitude": 0})

    assert resposta.status_code == 422
    assert rota.call_count == 0
