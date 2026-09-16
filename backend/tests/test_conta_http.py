"""Cadastro e "quem sou", pela costura HTTP.

Dada uma requisicao, o que volta: status, corpo e cookie. Nenhum caso aqui
espia a tabela nem chama funcao interna — o prior art e `test_cache_http.py`,
que verifica o cache contando requisicoes em vez de olhar suas entradas.

O banco entra pelo repositorio em memoria, como o relogio e o cache ja entram.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import repositorio_do_processo
from app.db.repositorio import RepositorioEmMemoria, RepositorioSql
from app.main import app
from app.services import sessao as servico_de_sessao
from app.services.conta import MINIMO_DA_SENHA
from app.services.sessao import DURACAO, NOME_DO_COOKIE
from tests.test_repositorio import engine_de_teste, sessao_de_teste  # noqa: F401

SENHA = "correia-de-bateria"


@pytest.fixture
def cliente(monkeypatch):
    """Um cliente HTTP sobre a aplicacao, com o banco em memoria.

    `AMBIENTE=desenvolvimento` porque o `TestClient` fala `http://testserver`,
    e um cookie `Secure` nao volta por `http`: sem isto, todo caso que depende
    da sessao falharia por uma razao que nao e a que ele investiga. Que o
    `Secure` **esteja** la fora de desenvolvimento e verificado a parte, em
    `test_o_cookie_e_secure_fora_de_desenvolvimento`.

    A troca do repositorio e desfeita no fim: e estado de processo, e um
    substituto que vazasse serviria o teste seguinte.
    """
    monkeypatch.setenv("AMBIENTE", "desenvolvimento")
    repositorio_do_processo.substituir(RepositorioEmMemoria())
    with TestClient(app) as cliente:
        yield cliente
    repositorio_do_processo.substituir(None)


class RelogioDaSessao:
    """O relogio da sessao, avancado a mao.

    Devolve `datetime` com fuso, e nao segundos como o `Relogio` de
    `conftest.py`: a expiracao da sessao e comparada com uma coluna
    `timestamptz`, e um instante ingenuo levantaria na comparacao.
    """

    def __init__(self) -> None:
        self.instante = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.instante

    def avancar(self, quanto: timedelta) -> None:
        self.instante += quanto


@pytest.fixture
def relogio():
    """Poe o relogio da sessao sob controle, e o devolve no fim."""
    relogio = RelogioDaSessao()
    servico_de_sessao.substituir_relogio(relogio)
    yield relogio
    servico_de_sessao.substituir_relogio(None)


def cadastrar(cliente, email="ana@exemplo.com", senha=SENHA):
    return cliente.post("/api/cadastro", json={"email": email, "senha": senha})


def test_cadastrar_cria_a_conta_e_devolve_o_cookie(cliente):
    """O caso que o ticket demonstra: cadastrar ja entra."""
    resposta = cadastrar(cliente)

    assert resposta.status_code == 201
    assert resposta.json()["email"] == "ana@exemplo.com"
    assert NOME_DO_COOKIE in resposta.cookies


def test_quem_sou_identifica_a_conta_quando_ha_sessao(cliente):
    """O endpoint que o frontend consulta ao abrir o app."""
    cadastrar(cliente)

    resposta = cliente.get("/api/quem-sou")

    assert resposta.status_code == 200
    assert resposta.json() == {"conta": {"email": "ana@exemplo.com"}}


def test_quem_sou_sem_sessao_responde_que_nao_ha_conta_sem_erro(cliente):
    """Visitante sem conta nao e erro: e o estado normal de quem nunca entrou.

    `401` aqui obrigaria o frontend a tratar como falha o caso mais comum de
    todos, e encheria o console de erro em toda visita anonima.
    """
    resposta = cliente.get("/api/quem-sou")

    assert resposta.status_code == 200
    assert resposta.json() == {"conta": None}


def test_cadastrar_com_email_ja_usado_e_recusado_com_mensagem_clara(cliente):
    """Quem ja tem conta precisa saber que deve **entrar**, nao cadastrar."""
    cadastrar(cliente)

    resposta = cadastrar(cliente)

    assert resposta.status_code == 409
    assert "entrar" in resposta.json()["detail"].lower()


def test_dois_emails_que_diferem_so_por_maiusculas_sao_o_mesmo_email(cliente):
    """`ana@exemplo.com` e `Ana@Exemplo.com` sao a mesma pessoa.

    Sem isto, duas contas conviveriam com o mesmo endereco e quem entrasse
    veria a lista de uma delas conforme a caixa que digitou naquele dia.
    """
    cadastrar(cliente, email="ana@exemplo.com")

    resposta = cadastrar(cliente, email="Ana@Exemplo.COM")

    assert resposta.status_code == 409


def test_nenhuma_resposta_contem_a_senha_nem_o_hash(cliente):
    """A senha nao sai — nem no sucesso, nem no erro, nem em "quem sou".

    O caso olha o **corpo cru**, e nao o JSON decodificado: a senha poderia
    aparecer dentro de uma mensagem de erro do Pydantic, onde nenhum campo
    nomeado a revelaria.
    """
    respostas = [
        cadastrar(cliente),
        cadastrar(cliente),
        cliente.get("/api/quem-sou"),
        cadastrar(cliente, email="nao-e-email", senha=SENHA),
        cadastrar(cliente, email="bia@exemplo.com", senha="curta"),
    ]

    for resposta in respostas:
        assert SENHA not in resposta.text
        assert "curta" not in resposta.text
        # O prefixo do Argon2. Um hash vazado na resposta comecaria por ele.
        assert "$argon2" not in resposta.text


def test_senha_abaixo_do_minimo_e_recusada_com_o_requisito_na_mensagem(cliente):
    """A mensagem tem de **dizer o numero**.

    "Senha invalida" faria a pessoa tentar de novo no escuro; a spec pede que
    os requisitos sejam conhecidos antes do envio, e o erro e a ultima linha de
    defesa disso.
    """
    resposta = cadastrar(cliente, senha="a" * (MINIMO_DA_SENHA - 1))

    assert resposta.status_code == 422
    assert str(MINIMO_DA_SENHA) in resposta.json()["detail"]


def test_a_senha_no_minimo_exato_e_aceita(cliente):
    """A fronteira, do lado de dentro: o minimo e "ao menos", nao "mais que"."""
    assert cadastrar(cliente, senha="a" * MINIMO_DA_SENHA).status_code == 201


@pytest.mark.parametrize(
    "malformado",
    [
        "sem-arroba",
        "sem@dominio",
        "@exemplo.com",
        "ana@",
        "com espaco@exemplo.com",
        "",
    ],
)
def test_email_malformado_e_recusado(cliente, malformado):
    resposta = cadastrar(cliente, email=malformado)

    assert resposta.status_code == 422


def test_o_espaco_em_volta_do_email_nao_cria_conta_separada(cliente):
    """" ana@exemplo.com " e `ana@exemplo.com`.

    Sem a normalizacao, um espaco colado do gerenciador de senhas daria uma
    segunda conta que a pessoa nunca reencontraria.
    """
    cadastrar(cliente, email="ana@exemplo.com")

    assert cadastrar(cliente, email="  ana@exemplo.com  ").status_code == 409


def test_o_hash_nunca_e_igual_entre_duas_contas_de_mesma_senha(cliente):
    """Duas contas, a mesma senha, hashes diferentes — vistos pelo repositorio.

    E o unico caso deste arquivo que olha alem da resposta HTTP, e olha porque
    a propriedade e **invisivel** na costura: o hash nunca sai na resposta, e e
    justamente isso que os outros casos exigem. Observa-lo pelo unico metodo
    que o expoe e o que resta.
    """
    cadastrar(cliente, email="ana@exemplo.com")
    cadastrar(cliente, email="bia@exemplo.com")

    with repositorio_do_processo.atual() as repositorio:
        hashes = {repositorio.hash_da_senha(1), repositorio.hash_da_senha(2)}

    assert len(hashes) == 2


def test_o_cookie_e_httponly_e_samesite_lax(cliente):
    """As duas flags que o ADR 0005 comprou.

    `HttpOnly` e o ponto inteiro da decisao: o cookie nao e legivel por script
    nenhum da pagina, nem pelo nosso. `SameSite=Lax` barra o envio em
    requisicao disparada por terceiro.
    """
    carimbo = cadastrar(cliente).headers["set-cookie"].lower()

    assert "httponly" in carimbo
    assert "samesite=lax" in carimbo


def test_o_cookie_nao_e_secure_em_desenvolvimento(cliente):
    """Em `http://localhost` um cookie `Secure` nao voltaria, e ninguem entraria."""
    assert "secure" not in cadastrar(cliente).headers["set-cookie"].lower()


def test_o_cookie_e_secure_fora_de_desenvolvimento(monkeypatch):
    """O padrao e seguro: quem **nao** configura nada leva `Secure`.

    O caso monta o proprio cliente porque a fixture `cliente` existe para o
    caso oposto — sem ela, nenhum outro teste conseguiria mandar o cookie de
    volta por `http`.
    """
    monkeypatch.delenv("AMBIENTE", raising=False)
    repositorio_do_processo.substituir(RepositorioEmMemoria())
    with TestClient(app) as proprio:
        carimbo = cadastrar(proprio).headers["set-cookie"].lower()
    repositorio_do_processo.substituir(None)

    assert "secure" in carimbo


def test_uma_sessao_expirada_e_recusada_pelo_quem_sou(cliente, relogio):
    """Passados os sete dias, a sessao deixa de valer — sem `sleep` algum.

    O relogio e injetado, como no cache: um teste que esperasse a duracao de
    verdade levaria sete dias, e um que encurtasse a duracao provaria que um
    valor que a producao nao usa funciona.
    """
    cadastrar(cliente)
    assert cliente.get("/api/quem-sou").json()["conta"] is not None

    relogio.avancar(DURACAO + timedelta(seconds=1))

    assert cliente.get("/api/quem-sou").json() == {"conta": None}


def test_a_sessao_ainda_vale_um_instante_antes_de_expirar(cliente, relogio):
    """A fronteira, do lado de dentro: nao se expira cedo demais."""
    cadastrar(cliente)

    relogio.avancar(DURACAO - timedelta(seconds=1))

    assert cliente.get("/api/quem-sou").json()["conta"] is not None


def test_um_cookie_de_sessao_inventado_e_recusado(cliente):
    """Adivinhar o identificador nao entra, e nao da erro diferente de "nao ha".

    Um `500` ou um `404` aqui contaria a quem testa identificadores quais
    existem.
    """
    cliente.cookies.set(NOME_DO_COOKIE, "identificador-que-nunca-existiu")

    resposta = cliente.get("/api/quem-sou")

    assert resposta.status_code == 200
    assert resposta.json() == {"conta": None}


@pytest.mark.postgres
class TestCadastroNoPostgres:
    """Cadastro e "quem sou" contra o Postgres de verdade, sob demanda.

    A suite padrao roda contra o repositorio em memoria, e e o que a mantem em
    segundos sem exigir Docker de ninguem. O que ela **nao** pode provar e que
    o SQL por tras dos mesmos endpoints funciona: um `INSERT` que violasse o
    tamanho de uma coluna, ou um indice que nao existisse na migracao, passaria
    verde em memoria e quebraria no primeiro cadastro de verdade.

    Mesma razao e mesmo mecanismo de `TestRepositorioNoPostgres`: fora da
    execucao padrao, acionado por marcador.

        docker compose up -d
        cd backend && uv run pytest -m postgres
    """

    @pytest.fixture
    def cliente(self, monkeypatch, sessao_de_teste):
        """O cliente HTTP com o repositorio **SQL** por tras.

        A transacao do `sessao_de_teste` e desfeita no fim, entao os casos nao
        deixam conta nenhuma no banco de teste.
        """
        monkeypatch.setenv("AMBIENTE", "desenvolvimento")
        repositorio_do_processo.substituir(RepositorioSql(sessao_de_teste))
        with TestClient(app) as cliente:
            yield cliente
        repositorio_do_processo.substituir(None)

    def test_cadastrar_e_perguntar_quem_sou_atravessa_o_sql(self, cliente):
        """O caminho inteiro contra o banco de verdade, pela costura HTTP."""
        resposta = cadastrar(cliente)

        assert resposta.status_code == 201
        assert cliente.get("/api/quem-sou").json() == {
            "conta": {"email": "ana@exemplo.com"}
        }

    def test_o_email_repetido_e_recusado_pelo_banco(self, cliente):
        """A unicidade sem maiusculas e do **indice**, e este caso a alcanca.

        Em memoria a regra e um `casefold()` em Python; aqui e o indice
        funcional sobre `lower(email)` que a migracao criou.
        """
        cadastrar(cliente, email="ana@exemplo.com")

        assert cadastrar(cliente, email="Ana@Exemplo.COM").status_code == 409
