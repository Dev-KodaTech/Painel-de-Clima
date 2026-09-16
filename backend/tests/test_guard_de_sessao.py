"""O guard de sessao, pela costura HTTP de um app montado para o caso.

As rotas protegidas de verdade ainda nao existem — a fatia 08 do Calendario e a
05 de `locais-salvos` e que as trazem —, e este arquivo nao espera por elas: um
`FastAPI` proprio com duas rotas minimas exercita o guard hoje, e nenhuma rota
de sonda vai para producao so para ser testada.

O que se observa e o que um cliente observa: status e corpo. Nenhum caso chama
`conta_da_sessao` direto nem espia a tabela — o guard existe para ser montado
num `Depends`, e e montado num `Depends` que ele precisa funcionar.
"""

from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import repositorio_do_processo
from app.db.repositorio import Conta, RepositorioEmMemoria
from app.dependencias import conta_exigida, conta_opcional
from app.main import app as app_real
from app.services import sessao as servico_de_sessao
from app.services.sessao import DURACAO, NOME_DO_COOKIE
from tests.test_conta_http import RelogioDaSessao, SENHA


def _app_de_teste() -> FastAPI:
    """Um app com uma rota por forma do guard, e nada mais.

    As duas rotas existem para responder **o que o guard entregou**: a exigida
    devolve o e-mail, que e como se verifica que a conta certa chegou ao
    handler, e a mista devolve o mesmo envelope de `/api/quem-sou` para que a
    ausencia seja um valor e nao um status.
    """
    app = FastAPI()

    @app.get("/protegida")
    def protegida(conta: Conta = Depends(conta_exigida)) -> dict[str, str]:
        return {"email": conta.email}

    @app.get("/mista")
    def mista(conta: Conta | None = Depends(conta_opcional)) -> dict[str, str | None]:
        return {"email": None if conta is None else conta.email}

    return app


@pytest.fixture
def cliente(monkeypatch):
    """O cliente sobre o app de teste, com o banco em memoria.

    Mesma mecanica da fixture de `test_conta_http.py`, e pela mesma razao:
    `AMBIENTE=desenvolvimento` porque o `TestClient` fala `http://testserver` e
    um cookie `Secure` nao voltaria por `http`.

    O cadastro e feito contra o app **de verdade**, porque e ele que sabe abrir
    sessao; o cookie resultante e levado para o app de teste a mao. Os dois
    compartilham o repositorio do processo, que e o que faz a sessao aberta num
    valer no outro.
    """
    monkeypatch.setenv("AMBIENTE", "desenvolvimento")
    repositorio_do_processo.substituir(RepositorioEmMemoria())
    with TestClient(_app_de_teste()) as cliente:
        yield cliente
    repositorio_do_processo.substituir(None)


@pytest.fixture
def relogio():
    """O relogio da sessao sob controle, devolvido no fim."""
    relogio = RelogioDaSessao()
    servico_de_sessao.substituir_relogio(relogio)
    yield relogio
    servico_de_sessao.substituir_relogio(None)


def sessao_valida(cliente, email: str = "ana@exemplo.com") -> str:
    """Abre uma sessao de verdade, poe o cookie no cliente e devolve o identificador.

    Passa pelo `/api/cadastro` do app real em vez de inserir a linha pelo
    repositorio: uma sessao montada a mao poderia divergir da que a aplicacao
    abre — outro formato de identificador, outra expiracao — e o guard estaria
    sendo provado contra um dado que a producao nunca produz.

    O `email` e parametro porque o caso das duas contas precisa de duas sessoes
    vivas ao mesmo tempo; devolve o identificador porque esse mesmo caso guarda
    um cookie enquanto abre o outro, e o repoe depois.
    """
    with TestClient(app_real) as do_app:
        do_app.post("/api/cadastro", json={"email": email, "senha": SENHA})
        id_da_sessao = do_app.cookies[NOME_DO_COOKIE]

    cliente.cookies.set(NOME_DO_COOKIE, id_da_sessao)
    return id_da_sessao


def test_a_rota_protegida_responde_a_conta_da_sessao(cliente):
    """O caso central: com sessao valida, a conta certa chega ao handler.

    Verifica o e-mail, e nao so o `200`: um guard que devolvesse a primeira
    conta da tabela passaria num teste que so olhasse o status, e entregaria a
    conta de outra pessoa assim que houvesse duas.
    """
    sessao_valida(cliente)

    resposta = cliente.get("/protegida")

    assert resposta.status_code == 200
    assert resposta.json() == {"email": "ana@exemplo.com"}


def test_cada_cookie_traz_a_sua_conta_e_nao_a_da_outra(cliente):
    """Duas contas ao mesmo tempo, e cada cookie resolve para a sua.

    O caso central acima passaria com um guard que devolvesse "a conta que
    existe" enquanto so houvesse uma — e e com duas que o app vive. Este e o
    erro que os consumidores desta fatia nao poderiam absorver: os planos de
    uma pessoa aparecendo para outra, e a fatia 05 de `locais-salvos` com a
    lista trocada.

    As duas sessoes sao abertas antes de qualquer leitura, e nao em sequencia
    com a verificacao no meio: e assim que elas coexistem de verdade na tabela,
    que e a condicao que o bug exigiria.
    """
    de_ana = sessao_valida(cliente)
    de_bia = sessao_valida(cliente, email="bia@exemplo.com")

    assert de_ana != de_bia

    cliente.cookies.set(NOME_DO_COOKIE, de_ana)
    assert cliente.get("/protegida").json() == {"email": "ana@exemplo.com"}

    cliente.cookies.set(NOME_DO_COOKIE, de_bia)
    assert cliente.get("/protegida").json() == {"email": "bia@exemplo.com"}


def test_a_rota_protegida_recusa_sem_cookie(cliente):
    """Sem cookie nenhum: `401`, e nao `403` nem `200` com corpo vazio."""
    resposta = cliente.get("/protegida")

    assert resposta.status_code == 401


def test_a_rota_protegida_recusa_um_cookie_de_sessao_inexistente(cliente):
    """Adivinhar o identificador nao entra.

    Um `404` ou um `500` aqui contaria a quem testa identificadores quais
    existem — e o `500` ainda entregaria um traceback.
    """
    cliente.cookies.set(NOME_DO_COOKIE, "identificador-que-nunca-existiu")

    resposta = cliente.get("/protegida")

    assert resposta.status_code == 401


def test_a_rota_protegida_recusa_uma_sessao_expirada(cliente, relogio):
    """Passados os sete dias, a sessao deixa de abrir a rota — sem `sleep`.

    O relogio e injetado, como no cache e como em `test_conta_http.py`: um caso
    que esperasse a duracao de verdade levaria sete dias, e um que encurtasse a
    duracao provaria que um valor que a producao nao usa funciona.
    """
    sessao_valida(cliente)
    assert cliente.get("/protegida").status_code == 200

    relogio.avancar(DURACAO + timedelta(seconds=1))

    assert cliente.get("/protegida").status_code == 401


def test_a_sessao_ainda_abre_a_rota_um_instante_antes_de_expirar(cliente, relogio):
    """A fronteira, do lado de dentro: nao se recusa cedo demais."""
    sessao_valida(cliente)

    relogio.avancar(DURACAO - timedelta(seconds=1))

    assert cliente.get("/protegida").status_code == 200


def test_as_tres_recusas_sao_indistinguiveis_entre_si(cliente, relogio):
    """A propriedade que esta fatia existe para garantir.

    Cookie ausente, identificador inventado e sessao vencida tem de dar
    **exatamente** a mesma resposta. Qualquer diferenca — no status ou no corpo
    — deixaria alguem separar "esse identificador nunca existiu" de "esse
    existiu e venceu", e o segundo e a confirmacao de que ha uma conta por tras.

    Compara o corpo inteiro, e nao so o status, porque e na mensagem que a
    divergencia costuma nascer: "sessao expirada" no lugar de "entre para
    continuar" e uma gentileza que conta o que nao devia.
    """
    sem_cookie = cliente.get("/protegida")

    cliente.cookies.set(NOME_DO_COOKIE, "identificador-que-nunca-existiu")
    inventado = cliente.get("/protegida")

    cliente.cookies.clear()
    sessao_valida(cliente)
    relogio.avancar(DURACAO + timedelta(seconds=1))
    expirada = cliente.get("/protegida")

    assert sem_cookie.status_code == inventado.status_code == expirada.status_code
    assert sem_cookie.json() == inventado.json() == expirada.json()

    # O valor, e nao so a igualdade: tres respostas que regredissem juntas para
    # `200` continuariam iguais, e o caso passaria dizendo que a rota esta
    # protegida enquanto ela deixava entrar qualquer um.
    assert sem_cookie.status_code == 401


def test_a_recusa_nao_revela_o_email_a_expiracao_nem_o_cookie(cliente, relogio):
    """O corpo da recusa nao nomeia nada do que causou a recusa.

    Olha o texto cru das tres recusas atras das palavras que um erro prestativo
    usaria. "Sessao expirada" confirmaria que houve uma sessao; o e-mail
    confirmaria a conta; "cookie" diria em que sondar a seguir.
    """
    sem_cookie = cliente.get("/protegida")

    cliente.cookies.set(NOME_DO_COOKIE, "identificador-que-nunca-existiu")
    inventado = cliente.get("/protegida")

    cliente.cookies.clear()
    sessao_valida(cliente)
    relogio.avancar(DURACAO + timedelta(seconds=1))
    expirada = cliente.get("/protegida")

    for resposta in (sem_cookie, inventado, expirada):
        texto = resposta.text.lower()
        assert "ana@exemplo.com" not in texto
        assert "expir" not in texto
        assert "cookie" not in texto
        assert "sessao" not in texto and "sessão" not in texto


def test_a_rota_mista_responde_a_conta_quando_ha_sessao(cliente):
    """Com sessao, o guard opcional entrega a mesma conta que o exigido."""
    sessao_valida(cliente)

    resposta = cliente.get("/mista")

    assert resposta.status_code == 200
    assert resposta.json() == {"email": "ana@exemplo.com"}


def test_a_rota_mista_responde_sem_conta_em_vez_de_recusar(cliente, relogio):
    """Os tres casos de "sem sessao" viram `None`, e nenhum vira `401`.

    E o que a pagina Calendario precisa para ser parcialmente publica: previsao
    e aptidao sao funcao da cidade e servem a quem nunca entrou, e so a faixa de
    planos e da conta. Sem esta forma, a pagina inteira dependeria de um `401`
    interceptado pelo frontend para renderizar o que e publico.

    Os tres casos no mesmo teste porque a propriedade e "nenhum deles recusa",
    e nao tres propriedades separadas: um `401` que aparecesse so na expirada
    seria o mesmo bug.
    """
    sem_cookie = cliente.get("/mista")

    cliente.cookies.set(NOME_DO_COOKIE, "identificador-que-nunca-existiu")
    inventado = cliente.get("/mista")

    cliente.cookies.clear()
    sessao_valida(cliente)
    relogio.avancar(DURACAO + timedelta(seconds=1))
    expirada = cliente.get("/mista")

    for resposta in (sem_cookie, inventado, expirada):
        assert resposta.status_code == 200
        assert resposta.json() == {"email": None}
