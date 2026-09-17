"""Criar, listar e apagar planos, pela costura HTTP.

Dada uma requisicao, o que volta: status e corpo. Nenhum caso aqui espia a
tabela nem chama o repositorio direto — o estilo e o de `test_conta_http.py`, e
a razao e a mesma: o que esta sob teste e o contrato que o frontend consome.

O banco entra pelo repositorio em memoria, como nos outros testes de HTTP.

**A rota autenticada e a novidade do app aqui.** Todo CRUD anterior e leitura
publica (previsao, condicoes, noticias) ou a propria conta; planos sao a
primeira escrita que exige sessao, e por isso os casos de sessao ausente e de
conta alheia pesam tanto quanto os de sucesso.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import repositorio_do_processo
from app.db.repositorio import RepositorioEmMemoria
from app.dependencias import MSG_SEM_SESSAO
from app.main import app
from app.routers.planos import MSG_PLANO_NAO_ENCONTRADO

SENHA = "correia-de-bateria"
TERCA = "2026-09-22"
QUARTA = "2026-09-23"


@pytest.fixture
def cliente(monkeypatch):
    """Um cliente HTTP sobre a aplicacao, com o banco em memoria.

    `AMBIENTE=desenvolvimento` pela mesma razao de `test_conta_http.py`: o
    `TestClient` fala `http://testserver`, e um cookie `Secure` nao voltaria —
    todo caso que depende da sessao falharia por um motivo que nao e o que ele
    investiga.
    """
    monkeypatch.setenv("AMBIENTE", "desenvolvimento")
    repositorio_do_processo.substituir(RepositorioEmMemoria())
    with TestClient(app) as cliente:
        yield cliente
    repositorio_do_processo.substituir(None)


def cadastrar(cliente, email="ana@exemplo.com"):
    """Cadastra e **ja entra** — o cadastro devolve o cookie da sessao."""
    return cliente.post("/api/cadastro", json={"email": email, "senha": SENHA})


def criar_plano(cliente, titulo="Lavar as cortinas", dia=TERCA, atividade="lavar_roupa"):
    return cliente.post(
        "/api/planos", json={"titulo": titulo, "dia": dia, "atividade": atividade}
    )


class TestSemSessao:
    """As tres rotas recusam quem nao tem sessao, e recusam igual."""

    def test_criar_sem_sessao_da_401(self, cliente):
        resposta = criar_plano(cliente)

        assert resposta.status_code == 401
        assert resposta.json()["detail"] == MSG_SEM_SESSAO

    def test_listar_sem_sessao_da_401(self, cliente):
        """`401`, e nao uma lista vazia.

        A lista vazia diria "voce nao tem planos" a quem na verdade nao esta
        identificado — e o frontend mostraria a faixa vazia da conta no lugar
        do convite para entrar.
        """
        resposta = cliente.get("/api/planos")

        assert resposta.status_code == 401
        assert resposta.json()["detail"] == MSG_SEM_SESSAO

    def test_apagar_sem_sessao_da_401(self, cliente):
        resposta = cliente.delete("/api/planos/1")

        assert resposta.status_code == 401
        assert resposta.json()["detail"] == MSG_SEM_SESSAO


class TestCriar:
    def test_criar_devolve_o_plano_com_id(self, cliente):
        cadastrar(cliente)

        resposta = criar_plano(cliente)

        assert resposta.status_code == 201
        corpo = resposta.json()
        assert corpo["titulo"] == "Lavar as cortinas"
        assert corpo["dia"] == TERCA
        assert corpo["atividade"] == "lavar_roupa"
        assert isinstance(corpo["id"], int)

    def test_o_plano_criado_aparece_na_listagem(self, cliente):
        cadastrar(cliente)
        criar_plano(cliente)

        resposta = cliente.get("/api/planos")

        assert resposta.status_code == 200
        assert [plano["titulo"] for plano in resposta.json()] == ["Lavar as cortinas"]

    def test_o_dia_no_passado_e_aceito(self, cliente):
        """A decisao da issue: aceitar.

        A pagina lida com plano de dia passado de qualquer forma (story 28), e
        recusar aqui criaria uma regra que a listagem depois contradiz.
        """
        cadastrar(cliente)

        resposta = criar_plano(cliente, dia="2020-01-01")

        assert resposta.status_code == 201

    def test_a_resposta_nao_traz_a_conta(self, cliente):
        """`conta_id` nao sai na resposta.

        O frontend nao tem o que fazer com ele — os planos vem da sessao, nunca
        de um identificador que o cliente informe —, e publica-lo convidaria
        alguem a mandar um no corpo. Mesma razao de `ContaSaida` nao ter `id`.
        """
        cadastrar(cliente)

        corpo = criar_plano(cliente).json()

        assert "conta_id" not in corpo


class TestValidacao:
    def test_titulo_vazio_e_recusado(self, cliente):
        cadastrar(cliente)

        resposta = criar_plano(cliente, titulo="")

        assert resposta.status_code == 422

    def test_titulo_so_de_espacos_e_recusado(self, cliente):
        """Espaco em branco nao e titulo.

        Sem isto, `"   "` passaria pelo "nao vazio" e a faixa mostraria uma
        linha sem texto que ninguem consegue distinguir das outras.
        """
        cadastrar(cliente)

        resposta = criar_plano(cliente, titulo="   ")

        assert resposta.status_code == 422

    def test_o_titulo_e_guardado_sem_espaco_nas_pontas(self, cliente):
        cadastrar(cliente)

        corpo = criar_plano(cliente, titulo="  Lavar as cortinas  ").json()

        assert corpo["titulo"] == "Lavar as cortinas"

    def test_atividade_inexistente_e_recusada(self, cliente):
        """Uma atividade que nenhuma regra julga nao entra.

        E o motivo de `atividade` ser fechada: um plano de "dormir" nao teria
        aptidao nenhuma para cruzar na faixa.
        """
        cadastrar(cliente)

        resposta = criar_plano(cliente, atividade="dormir")

        assert resposta.status_code == 422

    def test_dia_invalido_e_recusado(self, cliente):
        cadastrar(cliente)

        resposta = criar_plano(cliente, dia="nao-e-data")

        assert resposta.status_code == 422

    def test_dia_com_hora_e_recusado(self, cliente):
        """Plano nao tem hora, e o tipo e o que impede que ela entre.

        Um `datetime` aceito aqui seria truncado em silencio pela coluna
        `Date`, e quem mandou `14:00` acreditaria que ele foi guardado.
        """
        cadastrar(cliente)

        resposta = criar_plano(cliente, dia="2026-09-22T14:00:00")

        assert resposta.status_code == 422

    def test_titulo_longo_demais_e_recusado(self, cliente):
        """O limite da coluna tem recusa amigavel antes do banco."""
        cadastrar(cliente)

        resposta = criar_plano(cliente, titulo="x" * 201)

        assert resposta.status_code == 422


class TestListagem:
    def test_a_listagem_vem_ordenada_por_dia(self, cliente):
        cadastrar(cliente)
        criar_plano(cliente, titulo="O ultimo", dia=QUARTA)
        criar_plano(cliente, titulo="O primeiro", dia=TERCA)

        corpo = cliente.get("/api/planos").json()

        assert [plano["titulo"] for plano in corpo] == ["O primeiro", "O ultimo"]

    def test_a_conta_nova_nao_tem_planos(self, cliente):
        """Lista vazia, e nao `404`: nenhum plano e o estado inicial de todos."""
        cadastrar(cliente)

        resposta = cliente.get("/api/planos")

        assert resposta.status_code == 200
        assert resposta.json() == []

    def test_uma_conta_nao_ve_os_planos_de_outra(self, cliente):
        cadastrar(cliente, email="ana@exemplo.com")
        criar_plano(cliente, titulo="Da ana")
        cliente.post("/api/saida")

        cadastrar(cliente, email="bia@exemplo.com")
        corpo = cliente.get("/api/planos").json()

        assert corpo == []


class TestApagar:
    def test_apagar_remove_o_plano(self, cliente):
        cadastrar(cliente)
        plano_id = criar_plano(cliente).json()["id"]

        resposta = cliente.delete(f"/api/planos/{plano_id}")

        assert resposta.status_code == 204
        assert cliente.get("/api/planos").json() == []

    def test_apagar_plano_de_outra_conta_da_404(self, cliente):
        """`404`, e **nunca** `403`.

        `403` confirmaria que o plano existe, e a indistinguibilidade ja e
        requisito no `conta.py` pelo mesmo motivo: quem testa identificadores
        nao pode descobrir quais existem.
        """
        cadastrar(cliente, email="ana@exemplo.com")
        da_ana = criar_plano(cliente, titulo="Da ana").json()["id"]
        cliente.post("/api/saida")

        cadastrar(cliente, email="bia@exemplo.com")
        resposta = cliente.delete(f"/api/planos/{da_ana}")

        assert resposta.status_code == 404

    def test_o_plano_de_outra_conta_sobrevive_a_tentativa(self, cliente):
        """A recusa nao e so no status: o plano continua la."""
        cadastrar(cliente, email="ana@exemplo.com")
        da_ana = criar_plano(cliente, titulo="Da ana").json()["id"]
        cliente.post("/api/saida")

        cadastrar(cliente, email="bia@exemplo.com")
        cliente.delete(f"/api/planos/{da_ana}")
        cliente.post("/api/saida")

        cliente.post("/api/entrada", json={"email": "ana@exemplo.com", "senha": SENHA})
        assert [p["titulo"] for p in cliente.get("/api/planos").json()] == ["Da ana"]

    def test_apagar_plano_que_nao_existe_da_404(self, cliente):
        """O mesmo `404` do plano alheio — sao indistinguiveis de proposito."""
        cadastrar(cliente)

        resposta = cliente.delete("/api/planos/404")

        assert resposta.status_code == 404
        assert resposta.json()["detail"] == MSG_PLANO_NAO_ENCONTRADO

    def test_o_plano_alheio_e_o_inexistente_respondem_igual(self, cliente):
        """**A propriedade**, e nao os dois status conferidos em separado.

        Que as duas respostas tenham `404` nao basta: o que impede alguem de
        mapear os planos dos outros e elas serem **iguais** — status e corpo.
        Com dois casos soltos, a divergencia seria uma questao de alguem achar
        que estava ajudando ao detalhar um deles, que e exatamente o risco que
        o `_recusar_credenciais` do `conta.py` registra.
        """
        cadastrar(cliente, email="ana@exemplo.com")
        da_ana = criar_plano(cliente, titulo="Da ana").json()["id"]
        cliente.post("/api/saida")

        cadastrar(cliente, email="bia@exemplo.com")
        alheio = cliente.delete(f"/api/planos/{da_ana}")
        inexistente = cliente.delete("/api/planos/999999")

        assert alheio.status_code == inexistente.status_code
        assert alheio.json() == inexistente.json()
