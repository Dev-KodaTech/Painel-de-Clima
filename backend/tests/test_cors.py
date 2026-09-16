"""O CORS que a sessao exige, visto pela resposta ao preflight.

Em desenvolvimento nada disto aparece — o proxy do Vite faz o browser ver uma
origem so — e e justamente por isso que ha teste: o problema nasceria inteiro
no primeiro deploy que separasse as origens, longe de onde a decisao foi
tomada. Ver ADR 0005.

O que se observa sao os cabecalhos que o browser le para decidir se entrega a
resposta ao script. Nenhum caso aqui inspeciona o middleware.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

ORIGEM = "https://painel.exemplo.com"


@pytest.fixture
def cliente(monkeypatch):
    """A aplicacao com uma origem configurada, como em producao.

    `app` e reconstruido porque o middleware le `CORS_ORIGINS` **na montagem**:
    mudar a variavel depois nao mexeria no que ja foi montado.
    """
    monkeypatch.setenv("CORS_ORIGINS", ORIGEM)
    from app import main

    importlib.reload(main)
    with TestClient(main.app) as cliente:
        yield cliente


def preflight(cliente, metodo):
    return cliente.options(
        "/api/cadastro",
        headers={
            "Origin": ORIGEM,
            "Access-Control-Request-Method": metodo,
        },
    )


def test_o_cors_permite_credenciais(cliente):
    """Sem este cabecalho o browser descarta o cookie da resposta em silencio."""
    resposta = preflight(cliente, "POST")

    assert resposta.headers["access-control-allow-credentials"] == "true"


@pytest.mark.parametrize("metodo", ["GET", "POST", "DELETE"])
def test_o_cors_permite_os_metodos_de_escrita(cliente, metodo):
    """Cadastro e entrada sao `POST`, e remover local e `DELETE`.

    `allow_methods=["GET"]` bastava enquanto o app so lia.
    """
    resposta = preflight(cliente, metodo)

    assert resposta.status_code == 200
    assert metodo in resposta.headers["access-control-allow-methods"]


def test_a_origem_permitida_e_explicita_e_nao_curinga(cliente):
    """`allow_credentials=True` **proibe** o curinga.

    Com `*` o browser recusa a resposta inteira, e a mensagem fala de CORS em
    vez de falar da combinacao que a causou.
    """
    devolvida = preflight(cliente, "POST").headers["access-control-allow-origin"]

    assert devolvida == ORIGEM
    assert devolvida != "*"


def test_uma_origem_nao_listada_nao_e_permitida(cliente):
    """A lista e uma lista: quem nao esta nela nao passa."""
    resposta = cliente.options(
        "/api/cadastro",
        headers={
            "Origin": "https://site-de-outra-pessoa.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in resposta.headers
