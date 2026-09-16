"""Cadastro, entrada, saida e "quem sou", pela costura HTTP.

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
from app.services.conta import MINIMO_DA_SENHA, MSG_CREDENCIAIS_INVALIDAS
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


def entrar(cliente, email="ana@exemplo.com", senha=SENHA):
    return cliente.post("/api/entrada", json={"email": email, "senha": senha})


def sair(cliente):
    return cliente.post("/api/saida")


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
class TestContaNoPostgres:
    """A conta inteira contra o Postgres de verdade, sob demanda.

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

    def test_entrar_e_sair_atravessa_o_sql(self, cliente):
        """O ciclo inteiro contra o banco de verdade.

        O que este caso alcanca e o em memoria nao pode provar e o `DELETE` da
        saida: em memoria e um `dict.pop`, e aqui e o SQL que a sessao
        realmente executa.
        """
        cadastrar(cliente)
        cliente.cookies.clear()

        assert entrar(cliente).status_code == 200
        assert cliente.get("/api/quem-sou").json()["conta"] is not None

        assert sair(cliente).status_code == 200
        assert cliente.get("/api/quem-sou").json() == {"conta": None}

    def test_sair_de_uma_sessao_nao_derruba_a_outra_no_banco(self, cliente):
        """Duas linhas na tabela, e o `DELETE` acerta **uma**.

        A condicao do `DELETE` e por identificador, e este caso e o que prova
        que ela nao varre a conta inteira — um `WHERE conta_id` no lugar do
        `WHERE id` passaria em memoria se o em memoria tivesse o mesmo erro, e
        aqui nao passa.
        """
        cadastrar(cliente)
        computador = cliente.cookies[NOME_DO_COOKIE]

        cliente.cookies.clear()
        entrar(cliente)

        sair(cliente)

        cliente.cookies.set(NOME_DO_COOKIE, computador)
        assert cliente.get("/api/quem-sou").json()["conta"] is not None

    def test_a_entrada_com_email_inexistente_e_recusada_pelo_banco(self, cliente):
        assert entrar(cliente, email="ninguem@exemplo.com").status_code == 401


def test_entrar_com_credenciais_corretas_abre_sessao_e_devolve_o_cookie(cliente):
    """O caso central: quem tem conta volta.

    O cadastro sai do caminho antes de entrar — `cliente.cookies.clear()` —
    porque cadastrar ja abre sessao. Sem limpar, o `quem-sou` seguinte
    passaria com a sessao do cadastro e o teste ficaria verde mesmo que
    entrar nao abrisse sessao nenhuma.
    """
    cadastrar(cliente)
    cliente.cookies.clear()

    resposta = entrar(cliente)

    assert resposta.status_code == 200
    assert resposta.json() == {"email": "ana@exemplo.com"}
    assert NOME_DO_COOKIE in resposta.cookies
    assert cliente.get("/api/quem-sou").json() == {"conta": {"email": "ana@exemplo.com"}}


def test_entrar_com_senha_errada_e_recusado(cliente):
    cadastrar(cliente)
    cliente.cookies.clear()

    resposta = entrar(cliente, senha="nao-e-a-senha-certa")

    assert resposta.status_code == 401
    assert NOME_DO_COOKIE not in resposta.cookies
    assert cliente.get("/api/quem-sou").json() == {"conta": None}


def test_entrar_com_email_inexistente_e_recusado(cliente):
    resposta = entrar(cliente, email="ninguem@exemplo.com")

    assert resposta.status_code == 401
    assert NOME_DO_COOKIE not in resposta.cookies


def test_senha_errada_e_email_inexistente_dao_a_mesma_resposta(cliente):
    """A propriedade que este ticket existe para garantir.

    Respostas diferentes deixariam qualquer um descobrir **quais e-mails tem
    conta**, testando um por um: bastaria comparar a resposta de um endereco
    conhecido com a de um inventado. O caso compara status e corpo inteiro, e
    nao so o status, porque a diferenca costuma nascer na mensagem — "senha
    incorreta" contra "conta nao encontrada".
    """
    cadastrar(cliente)
    cliente.cookies.clear()

    senha_errada = entrar(cliente, senha="nao-e-a-senha-certa")
    email_inexistente = entrar(cliente, email="ninguem@exemplo.com")

    assert senha_errada.status_code == email_inexistente.status_code
    assert senha_errada.json() == email_inexistente.json()

    # O valor, e nao so a igualdade: duas respostas que regredissem juntas
    # para `200` continuariam iguais, e o caso passaria dizendo que a conta
    # esta protegida enquanto a entrada aceitava qualquer senha.
    assert senha_errada.status_code == 401
    assert senha_errada.json() == {"detail": MSG_CREDENCIAIS_INVALIDAS}



def test_entrar_nao_diferencia_maiusculas_no_email(cliente):
    """Quem cadastrou `ana@` entra como `Ana@`.

    A mesma regra que o cadastro usa para recusar o e-mail repetido; se as
    duas divergissem, existiria uma conta impossivel de reencontrar pela
    caixa que a pessoa digitasse no dia seguinte.
    """
    cadastrar(cliente, email="ana@exemplo.com")
    cliente.cookies.clear()

    assert entrar(cliente, email="Ana@Exemplo.COM").status_code == 200


def test_entrar_ignora_o_espaco_em_volta_do_email(cliente):
    """O espaco colado do gerenciador de senhas nao impede a entrada."""
    cadastrar(cliente, email="ana@exemplo.com")
    cliente.cookies.clear()

    assert entrar(cliente, email="  ana@exemplo.com  ").status_code == 200


def test_sair_apaga_a_sessao_e_expira_o_cookie(cliente):
    """Sair carimba a expiracao do cookie, alem de apagar a linha.

    As duas metades importam: a linha apagada e o que faz o logout ser real,
    e o cookie expirado e o que impede o navegador de continuar mandando um
    identificador que ja nao vale.
    """
    cadastrar(cliente)

    resposta = sair(cliente)

    assert resposta.status_code == 200
    carimbo = resposta.headers["set-cookie"].lower()
    assert "max-age=0" in carimbo or "expires=" in carimbo


def test_depois_de_sair_o_quem_sou_responde_que_nao_ha_conta(cliente):
    cadastrar(cliente)

    sair(cliente)

    assert cliente.get("/api/quem-sou").json() == {"conta": None}


def test_a_sessao_apagada_nao_vale_mesmo_apresentando_o_cookie_de_novo(cliente):
    """O ponto do ADR 0005, e o que um JWT nao daria.

    Sair apaga a **linha**: o identificador antigo, reapresentado a mao, e
    recusado. Com um token auto-contido ele continuaria valendo ate expirar,
    e o logout seria apenas o navegador esquecendo um papel ainda valido.
    """
    cadastrar(cliente)
    id_da_sessao = cliente.cookies[NOME_DO_COOKIE]

    sair(cliente)
    cliente.cookies.set(NOME_DO_COOKIE, id_da_sessao)

    assert cliente.get("/api/quem-sou").json() == {"conta": None}


def test_sair_de_uma_sessao_nao_invalida_as_outras_da_mesma_conta(cliente):
    """A segunda propriedade que este ticket existe para garantir.

    A mesma pessoa no computador e no celular sao duas linhas, e sair do
    celular nao pode encerrar a sessao do computador.

    Um cliente so, com o cookie guardado a mao e reposto no fim: e o
    equivalente a dois navegadores, sem montar dois `TestClient`. O
    `assert computador != celular` e o que impede o caso de passar a vazio —
    se a entrada reaproveitasse a sessao, a verificacao final estaria olhando
    a mesma linha que a saida acabou de apagar e nao provaria nada.
    """
    cadastrar(cliente)
    computador = cliente.cookies[NOME_DO_COOKIE]

    cliente.cookies.clear()
    entrar(cliente)
    celular = cliente.cookies[NOME_DO_COOKIE]
    assert computador != celular

    sair(cliente)

    cliente.cookies.set(NOME_DO_COOKIE, computador)
    assert cliente.get("/api/quem-sou").json() == {"conta": {"email": "ana@exemplo.com"}}


def test_entrar_duas_vezes_produz_duas_sessoes_independentes(cliente):
    """Entrar de novo nao reaproveita nem derruba a sessao anterior."""
    cadastrar(cliente)
    cliente.cookies.clear()

    entrar(cliente)
    primeira = cliente.cookies[NOME_DO_COOKIE]
    cliente.cookies.clear()
    entrar(cliente)
    segunda = cliente.cookies[NOME_DO_COOKIE]

    assert primeira != segunda

    cliente.cookies.set(NOME_DO_COOKIE, primeira)
    assert cliente.get("/api/quem-sou").json()["conta"] is not None


def test_sair_sem_sessao_nao_e_erro(cliente):
    """Nao ha o que apagar, e isso nao e falha.

    Quem chega a saida sem cookie — cookie ja expirado, segunda aba, clique
    duplo no botao — recebe o mesmo `200` de quem tinha sessao. Um `401` aqui
    faria o frontend tratar como problema o caminho mais inofensivo que
    existe.
    """
    assert sair(cliente).status_code == 200


def test_sair_com_um_cookie_inventado_nao_e_erro(cliente):
    cliente.cookies.set(NOME_DO_COOKIE, "identificador-que-nunca-existiu")

    assert sair(cliente).status_code == 200


def test_uma_sessao_expirada_e_recusada_como_se_nao_existisse(cliente, relogio):
    """Vencida e inexistente sao indistinguiveis.

    O `quem-sou` responde o mesmo `{"conta": None}` para as duas, e a saida
    responde o mesmo `200`: uma diferenca aqui diria a quem testa
    identificadores quais um dia existiram.
    """
    cadastrar(cliente)

    relogio.avancar(DURACAO + timedelta(seconds=1))

    assert cliente.get("/api/quem-sou").json() == {"conta": None}
    assert sair(cliente).status_code == 200


def test_entrar_depois_de_expirar_abre_uma_sessao_que_vale(cliente, relogio):
    """A sessao vencida nao contamina a nova: quem volta, volta mesmo."""
    cadastrar(cliente)
    relogio.avancar(DURACAO + timedelta(seconds=1))
    cliente.cookies.clear()

    assert entrar(cliente).status_code == 200
    assert cliente.get("/api/quem-sou").json()["conta"] is not None


def test_nenhuma_resposta_de_entrada_ou_saida_contem_a_senha(cliente):
    """A senha nao sai por caminho nenhum — nem no erro de credencial.

    Olha o corpo cru, e nao o JSON decodificado, como o caso irmao do
    cadastro: a senha poderia aparecer dentro de uma mensagem do Pydantic,
    onde nenhum campo nomeado a revelaria.
    """
    cadastrar(cliente)
    respostas = [
        entrar(cliente),
        entrar(cliente, senha=SENHA + "-errada"),
        entrar(cliente, email="ninguem@exemplo.com"),
        sair(cliente),
    ]

    for resposta in respostas:
        assert SENHA not in resposta.text
        assert "$argon2" not in resposta.text
