"""A bateria do repositorio, rodada contra as **duas** implementacoes.

O arquivo existe por causa do risco que a injecao do banco cria: se o
repositorio em memoria e o de SQL divergirem, a suite padrao fica verde
testando um comportamento que a producao nao tem. O jeito de nao deixar isso
acontecer e nao escrever duas baterias — e a mesma classe de casos,
parametrizada pela implementacao.

Como se divide:

- `TestRepositorio` roda **em memoria**, na execucao padrao, sem Docker.
- `TestRepositorioNoPostgres` herda os mesmos casos e roda contra o Postgres
  de verdade, marcada com `postgres`, fora da execucao padrao:

      docker compose up -d
      cd backend && uv run alembic upgrade head
      cd backend && uv run pytest -m postgres

Os casos que **so** existem no Postgres — que o banco recusa a segunda conta
por indice, que a cascata e do banco e nao do Python — ficam em
`TestSchemaNoPostgres`, no fim: nao sao comportamento do repositorio, sao
prova de que o schema e as migracoes funcionam.
"""

import os
from datetime import date, datetime, timedelta, timezone
from typing import get_args

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.db import schema
from app.models import Atividade, CidadeEscolhida
from app.db.repositorio import (
    EmailJaUsado,
    RepositorioEmMemoria,
    RepositorioSql,
    identidade_do_local,
)

BERLIM = CidadeEscolhida(
    name="Berlin",
    country="Germany",
    country_code="DE",
    admin1="Land Berlin",
    latitude=52.52437,
    longitude=13.41053,
)

#: A mesma cidade com a precisao que outra candidata traria. Arredondadas a
#: duas casas, as duas sao a mesma identidade — e o mesmo local salvo.
BERLIM_QUASE_IGUAL = BERLIM.model_copy(
    update={"latitude": 52.5244, "longitude": 13.4105}
)

LISBOA = CidadeEscolhida(
    name="Lisbon",
    country="Portugal",
    country_code="PT",
    admin1="Lisboa",
    latitude=38.71667,
    longitude=-9.13333,
)

DAQUI_UMA_HORA = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)

#: Dias de plano. Datas fixas e nao `date.today()`: um teste que monta o
#: cenario com o dia corrente muda de significado conforme a data em que roda,
#: que e o defeito que `test_trends.py::TestUv` ja carrega.
SEGUNDA = date(2026, 9, 21)
TERCA = date(2026, 9, 22)
QUARTA = date(2026, 9, 23)


def em(latitude: float, longitude: float, country_code: str) -> CidadeEscolhida:
    """Uma cidade so com o que a identidade olha, para os casos da funcao pura."""
    return CidadeEscolhida(
        name="Qualquer",
        country="Qualquer",
        country_code=country_code,
        admin1=None,
        latitude=latitude,
        longitude=longitude,
    )


class TestAtividadesAceitas:
    """O acoplamento entre o `CHECK` do banco e o `Literal` do dominio."""

    def test_as_quatro_atividades_do_check_sao_as_do_dominio(self):
        """O `CHECK` do banco e o `Literal` do dominio nao podem divergir.

        `schema.ATIVIDADES_ACEITAS` e escrita a mao e **nao** importada de
        `app.models`, porque o que ela alimenta e um `CHECK` em SQL — o banco o
        guarda como texto no catalogo e nao volta a consultar o Python. Um import
        daria a impressao de que mudar o `Literal` muda o banco, e nao muda: o que
        muda o banco e uma migracao.

        O acoplamento continua real, e e este caso que o guarda. Acrescentar a
        quinta atividade ao dominio sem migrar o `CHECK` faria o backend julgar uma
        atividade que o banco recusa gravar — e o erro apareceria so na primeira
        tentativa de criar o plano, em producao.
        """
        assert set(schema.ATIVIDADES_ACEITAS) == set(get_args(Atividade))


class TestIdentidadeDoLocal:
    """A funcao pura que decide o que e "o mesmo local"."""

    def test_a_coordenada_entra_arredondada_a_duas_casas(self):
        assert identidade_do_local(em(52.52437, 13.41053, "DE")) == identidade_do_local(
            em(52.5244, 13.4105, "DE")
        )

    def test_cidades_a_mais_de_um_quilometro_sao_locais_distintos(self):
        """Duas casas sao ~1,1 km: abaixo disso e a mesma cidade, acima nao."""
        assert identidade_do_local(em(52.52, 13.41, "DE")) != identidade_do_local(
            em(52.54, 13.41, "DE")
        )

    def test_a_mesma_coordenada_em_paises_diferentes_nao_e_o_mesmo_local(self):
        assert identidade_do_local(em(52.52, 13.41, "DE")) != identidade_do_local(
            em(52.52, 13.41, "PL")
        )

    def test_o_nome_da_cidade_nao_entra_na_identidade(self):
        """Grafias diferentes da mesma cidade sao o mesmo local salvo.

        E a razao de a identidade ser coordenada e pais: "Munich" e "Munchen"
        nao se comparam por nome.
        """
        munich = em(48.14, 11.58, "DE").model_copy(update={"name": "Munich"})
        munchen = em(48.14, 11.58, "DE").model_copy(update={"name": "Munchen"})

        assert identidade_do_local(munich) == identidade_do_local(munchen)

    def test_a_sigla_do_pais_nao_diferencia_maiusculas(self):
        assert identidade_do_local(em(52.52, 13.41, "de")) == identidade_do_local(
            em(52.52, 13.41, "DE")
        )


class TestRepositorio:
    """Os casos que valem para qualquer implementacao.

    `TestRepositorioNoPostgres` herda a classe inteira e so troca a fixture.
    """

    @pytest.fixture
    def repo(self):
        return RepositorioEmMemoria()

    # -- contas ------------------------------------------------------------

    def test_a_conta_criada_e_encontrada_pelo_email(self, repo):
        criada = repo.criar_conta("ana@exemplo.com", "hash-qualquer")

        assert repo.conta_por_email("ana@exemplo.com") == criada
        assert repo.conta_por_id(criada.id) == criada

    def test_o_email_e_encontrado_com_outras_maiusculas(self, repo):
        criada = repo.criar_conta("ana@exemplo.com", "hash-qualquer")

        assert repo.conta_por_email("ANA@Exemplo.COM") == criada

    def test_o_segundo_cadastro_com_o_mesmo_email_e_recusado(self, repo):
        repo.criar_conta("ana@exemplo.com", "hash-qualquer")

        with pytest.raises(EmailJaUsado):
            repo.criar_conta("ana@exemplo.com", "outro-hash")

    def test_o_segundo_cadastro_e_recusado_mesmo_diferindo_nas_maiusculas(self, repo):
        """O caso que a spec cita nominalmente: so as maiusculas mudam."""
        repo.criar_conta("ana@exemplo.com", "hash-qualquer")

        with pytest.raises(EmailJaUsado):
            repo.criar_conta("Ana@Exemplo.com", "outro-hash")

    def test_a_conta_nao_carrega_o_hash_da_senha(self, repo):
        """A credencial nao viaja junto do e-mail. Ver `Conta`."""
        conta = repo.criar_conta("ana@exemplo.com", "hash-secreto")

        assert "hash-secreto" not in repr(conta)
        assert not hasattr(conta, "senha_hash")

    def test_o_hash_sai_do_banco_para_quem_o_pede_pelo_nome(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash-secreto")

        assert repo.hash_da_senha(conta.id) == "hash-secreto"

    def test_email_sem_conta_nao_e_encontrado(self, repo):
        assert repo.conta_por_email("ninguem@exemplo.com") is None

    def test_conta_inexistente_nao_tem_hash(self, repo):
        assert repo.hash_da_senha(404) is None

    # -- sessoes -----------------------------------------------------------

    def test_a_sessao_criada_e_encontrada_pelo_identificador(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        sessao = repo.criar_sessao("id-da-sessao", conta.id, DAQUI_UMA_HORA)

        assert repo.sessao("id-da-sessao") == sessao
        assert sessao.conta_id == conta.id
        assert sessao.expira_em == DAQUI_UMA_HORA

    def test_a_sessao_expirada_continua_sendo_devolvida(self, repo):
        """Quem julga a expiracao e a camada de cima, com o relogio dela."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        vencida = DAQUI_UMA_HORA - timedelta(days=30)

        repo.criar_sessao("vencida", conta.id, vencida)

        guardada = repo.sessao("vencida")
        assert guardada is not None
        assert guardada.expira_em == vencida

    def test_sair_apaga_a_sessao(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        repo.criar_sessao("id-da-sessao", conta.id, DAQUI_UMA_HORA)

        repo.apagar_sessao("id-da-sessao")

        assert repo.sessao("id-da-sessao") is None

    def test_sair_de_um_navegador_nao_derruba_o_outro(self, repo):
        """Duas sessoes da mesma conta sao independentes. Ver ADR 0005."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        repo.criar_sessao("no-celular", conta.id, DAQUI_UMA_HORA)
        repo.criar_sessao("no-trabalho", conta.id, DAQUI_UMA_HORA)

        repo.apagar_sessao("no-celular")

        assert repo.sessao("no-celular") is None
        assert repo.sessao("no-trabalho") is not None

    def test_apagar_sessao_que_nao_existe_nao_levanta(self, repo):
        repo.apagar_sessao("nunca-existiu")

    # -- locais salvos -----------------------------------------------------

    def test_o_local_salvo_volta_na_listagem_com_os_seis_parametros(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        salvo = repo.salvar_local(conta.id, BERLIM)

        assert repo.locais_salvos(conta.id) == [salvo]
        assert salvo.cidade.name == "Berlin"
        assert salvo.cidade.country == "Germany"
        assert salvo.cidade.country_code == "DE"
        assert salvo.cidade.admin1 == "Land Berlin"
        assert salvo.cidade.latitude == pytest.approx(52.52437)
        assert salvo.cidade.longitude == pytest.approx(13.41053)

    def test_a_conta_nova_nao_tem_local_salvo(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        assert repo.locais_salvos(conta.id) == []

    def test_salvar_o_mesmo_local_duas_vezes_nao_duplica(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        primeiro = repo.salvar_local(conta.id, BERLIM)
        segundo = repo.salvar_local(conta.id, BERLIM)

        assert repo.locais_salvos(conta.id) == [primeiro]
        assert segundo.id == primeiro.id

    def test_a_mesma_cidade_com_outra_precisao_nao_duplica(self, repo):
        """O caso real: duas candidatas da mesma cidade, precisao diferente."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        primeiro = repo.salvar_local(conta.id, BERLIM)
        segundo = repo.salvar_local(conta.id, BERLIM_QUASE_IGUAL)

        assert repo.locais_salvos(conta.id) == [primeiro]
        assert segundo.id == primeiro.id

    def test_duas_contas_podem_salvar_a_mesma_cidade(self, repo):
        """A unicidade e por conta, nao global."""
        ana = repo.criar_conta("ana@exemplo.com", "hash")
        bia = repo.criar_conta("bia@exemplo.com", "hash")

        repo.salvar_local(ana.id, BERLIM)
        repo.salvar_local(bia.id, BERLIM)

        assert len(repo.locais_salvos(ana.id)) == 1
        assert len(repo.locais_salvos(bia.id)) == 1

    def test_a_listagem_traz_so_os_locais_da_conta(self, repo):
        ana = repo.criar_conta("ana@exemplo.com", "hash")
        bia = repo.criar_conta("bia@exemplo.com", "hash")
        repo.salvar_local(ana.id, BERLIM)
        repo.salvar_local(bia.id, LISBOA)

        assert [local.cidade.name for local in repo.locais_salvos(ana.id)] == ["Berlin"]
        assert [local.cidade.name for local in repo.locais_salvos(bia.id)] == ["Lisbon"]

    def test_a_ordem_e_a_de_insercao(self, repo):
        """Ordem previsivel, para reencontrar a lista onde foi deixada."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        repo.salvar_local(conta.id, BERLIM)
        repo.salvar_local(conta.id, LISBOA)

        assert [local.cidade.name for local in repo.locais_salvos(conta.id)] == [
            "Berlin",
            "Lisbon",
        ]

    def test_remover_apaga_o_local(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        salvo = repo.salvar_local(conta.id, BERLIM)

        assert repo.remover_local(conta.id, salvo.id) is True
        assert repo.locais_salvos(conta.id) == []

    def test_remover_local_de_outra_conta_nao_funciona(self, repo):
        """Acertar o identificador nao basta: a conta entra na condicao."""
        ana = repo.criar_conta("ana@exemplo.com", "hash")
        bia = repo.criar_conta("bia@exemplo.com", "hash")
        da_ana = repo.salvar_local(ana.id, BERLIM)

        assert repo.remover_local(bia.id, da_ana.id) is False
        assert repo.locais_salvos(ana.id) == [da_ana]

    def test_remover_local_que_nao_existe_devolve_falso(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        assert repo.remover_local(conta.id, 404) is False

    def test_o_local_salvo_aceita_pais_vazio(self, repo):
        """Territorios e regioes especiais chegam sem nome de pais."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        salvo = repo.salvar_local(
            conta.id,
            CidadeEscolhida(
                name="Papeete",
                country="",
                country_code="PF",
                admin1=None,
                latitude=-17.53333,
                longitude=-149.56667,
            ),
        )

        assert salvo.cidade.country == ""
        assert salvo.cidade.admin1 is None

    # -- planos ------------------------------------------------------------

    def test_o_plano_criado_aparece_na_listagem(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        criado = repo.criar_plano(conta.id, "Lavar as cortinas", TERCA, "lavar_roupa")

        assert repo.planos(conta.id) == [criado]
        assert criado.titulo == "Lavar as cortinas"
        assert criado.dia == TERCA
        assert criado.atividade == "lavar_roupa"

    def test_o_plano_guarda_o_dia_como_data_sem_hora(self, repo):
        """`date`, e nao `datetime`. A aptidao e diaria (verbete *Plano*).

        O tipo e o que impede que uma hora entre por descuido — e este caso e o
        que impede que uma implementacao futura troque a coluna por
        `DateTime` sem ninguem notar.
        """
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        criado = repo.criar_plano(conta.id, "Correr", TERCA, "esporte")

        assert criado.dia == TERCA
        assert isinstance(criado.dia, date)
        assert not isinstance(criado.dia, datetime)

    def test_a_listagem_e_ordenada_por_dia(self, repo):
        """Ordenada por dia, e nao por insercao: a faixa de planos e uma agenda."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        repo.criar_plano(conta.id, "O ultimo", QUARTA, "viagem")
        repo.criar_plano(conta.id, "O primeiro", SEGUNDA, "plantio")
        repo.criar_plano(conta.id, "O do meio", TERCA, "esporte")

        assert [plano.titulo for plano in repo.planos(conta.id)] == [
            "O primeiro",
            "O do meio",
            "O ultimo",
        ]

    def test_dois_planos_no_mesmo_dia_tem_ordem_estavel(self, repo):
        """Empate no dia desempata pela insercao, e nao por acaso.

        Sem criterio secundario a ordem de dois planos do mesmo dia ficaria a
        cargo do banco, e a faixa trocaria de ordem entre dois carregamentos
        sem nada ter mudado.
        """
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        primeiro = repo.criar_plano(conta.id, "Primeiro", TERCA, "esporte")
        segundo = repo.criar_plano(conta.id, "Segundo", TERCA, "viagem")

        assert repo.planos(conta.id) == [primeiro, segundo]

    def test_a_listagem_traz_so_os_planos_da_conta(self, repo):
        ana = repo.criar_conta("ana@exemplo.com", "hash")
        bia = repo.criar_conta("bia@exemplo.com", "hash")
        repo.criar_plano(ana.id, "Da ana", TERCA, "esporte")
        repo.criar_plano(bia.id, "Da bia", TERCA, "viagem")

        assert [plano.titulo for plano in repo.planos(ana.id)] == ["Da ana"]
        assert [plano.titulo for plano in repo.planos(bia.id)] == ["Da bia"]

    def test_apagar_remove_o_plano(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")
        criado = repo.criar_plano(conta.id, "Lavar as cortinas", TERCA, "lavar_roupa")

        assert repo.apagar_plano(conta.id, criado.id) is True
        assert repo.planos(conta.id) == []

    def test_apagar_plano_de_outra_conta_nao_funciona(self, repo):
        """Acertar o identificador nao basta: a conta entra na condicao.

        A mesma regra de `remover_local`, e pela mesma razao — apagar so por id
        deixaria uma conta apagar o plano de outra.
        """
        ana = repo.criar_conta("ana@exemplo.com", "hash")
        bia = repo.criar_conta("bia@exemplo.com", "hash")
        da_ana = repo.criar_plano(ana.id, "Da ana", TERCA, "esporte")

        assert repo.apagar_plano(bia.id, da_ana.id) is False
        assert repo.planos(ana.id) == [da_ana]

    def test_apagar_plano_que_nao_existe_devolve_falso(self, repo):
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        assert repo.apagar_plano(conta.id, 404) is False

    def test_o_plano_aceita_dia_no_passado(self, repo):
        """Dia passado e aceito na criacao, e a decisao esta registrada.

        A pagina lida com plano de dia passado de qualquer forma (story 28), e
        recusar aqui criaria uma regra que a listagem depois contradiz.
        """
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        criado = repo.criar_plano(conta.id, "Ja foi", date(2020, 1, 1), "viagem")

        assert repo.planos(conta.id) == [criado]

    def test_as_quatro_atividades_sao_aceitas(self, repo):
        """As quatro da regra do backend, e o repositorio guarda cada uma."""
        conta = repo.criar_conta("ana@exemplo.com", "hash")

        for atividade in ("lavar_roupa", "esporte", "viagem", "plantio"):
            repo.criar_plano(conta.id, f"Plano de {atividade}", TERCA, atividade)

        assert {plano.atividade for plano in repo.planos(conta.id)} == {
            "lavar_roupa",
            "esporte",
            "viagem",
            "plantio",
        }



#: O banco dos testes marcados. Separado do de desenvolvimento por padrao: os
#: testes apagam as tres tabelas a cada caso, e apontar para o banco de dev
#: levaria a conta de alguem junto.
URL_DE_TESTE_PADRAO = "postgresql+psycopg://painel:painel@localhost:5433/painel_teste"


@pytest.fixture(scope="module")
def engine_de_teste():
    """Cria o banco de teste, aplica as **migracoes** e devolve o engine.

    Migracoes, e nao `Base.metadata.create_all()`: o que estes testes existem
    para provar e que a migracao produz o schema completo num banco vazio.
    `create_all` produziria o schema a partir do mesmo `schema.py` que o resto
    do codigo usa, e uma migracao esquecida passaria verde.
    """
    url = os.environ.get("DATABASE_URL_DE_TESTE", URL_DE_TESTE_PADRAO)
    administrativo = create_engine(
        url.rsplit("/", 1)[0] + "/postgres", isolation_level="AUTOCOMMIT"
    )
    try:
        with administrativo.connect() as conexao:
            nome = url.rsplit("/", 1)[1]
            conexao.execute(text(f'DROP DATABASE IF EXISTS "{nome}"'))
            conexao.execute(text(f'CREATE DATABASE "{nome}"'))
    except OperationalError as erro:  # pragma: no cover - falta o container
        # Nao conectou. Sem esta captura, o traceback do psycopg — umas
        # quarenta linhas — se repete por caso e enterra a unica informacao
        # que importa: o comando a rodar. Erros de SQL **nao** sao capturados
        # de proposito; esses o teste precisa mostrar inteiros.
        pytest.exit(
            "Os testes marcados `postgres` exigem o container do banco:\n"
            "    docker compose up -d\n"
            f"Nao foi possivel conectar em {url.rsplit('@', 1)[-1]} "
            f"({type(erro.orig).__name__}).",
            returncode=1,
        )
    finally:
        administrativo.dispose()

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    criado = create_engine(url)
    yield criado
    criado.dispose()


@pytest.fixture
def sessao_de_teste(engine_de_teste):
    """Uma sessao por caso, desfeita no fim.

    A transacao externa e revertida em vez de as tabelas serem truncadas:
    e mais rapido e nao depende de o teste lembrar de limpar.
    """
    conexao = engine_de_teste.connect()
    transacao = conexao.begin()
    aberta = Session(bind=conexao, expire_on_commit=False)

    yield aberta

    aberta.close()
    # `if transacao.is_active`: os casos que provocam `IntegrityError` deixam a
    # transacao abortada pelo proprio Postgres, e chamar `rollback()` nela
    # avisa que ela ja se desligou da conexao. Fechar a conexao ja descarta o
    # que ficou.
    if transacao.is_active:
        transacao.rollback()
    conexao.close()


@pytest.mark.postgres
class TestRepositorioNoPostgres(TestRepositorio):
    """A **mesma** bateria, contra o Postgres de verdade.

    Nenhum caso e reescrito: a classe herda tudo e troca a fixture. E o que
    prova que o repositorio em memoria da suite padrao nao esconde erro de
    SQL — se as duas divergirem, o caso falha aqui.
    """

    @pytest.fixture
    def repo(self, sessao_de_teste):
        return RepositorioSql(sessao_de_teste)


@pytest.mark.postgres
class TestSchemaNoPostgres:
    """O que so o banco prova: os vinculos estao no schema, nao no Python.

    Cada caso aqui passa por cima do repositorio e fala SQL direto. E de
    proposito: o que esta sob teste e a migracao, nao o codigo de acesso.
    """

    def test_o_indice_recusa_o_email_repetido_sem_diferenciar_maiusculas(
        self, sessao_de_teste
    ):
        """A unicidade e do **banco**, e vale para quem insere por fora.

        O repositorio consulta antes de inserir, e por isso levanta
        `EmailJaUsado` sem chegar a tentar. Este caso pula essa consulta: e o
        que prova que a garantia sobrevive a um caminho que esqueceu de
        normalizar o e-mail.
        """
        sessao_de_teste.add(schema.Conta(email="ana@exemplo.com", senha_hash="h"))
        sessao_de_teste.flush()

        sessao_de_teste.add(schema.Conta(email="ANA@EXEMPLO.COM", senha_hash="h"))
        with pytest.raises(IntegrityError):
            sessao_de_teste.flush()

    def test_apagar_a_conta_por_sql_leva_locais_e_sessoes_junto(
        self, sessao_de_teste
    ):
        """A cascata e `ON DELETE CASCADE`, nao um laco em Python.

        O `DELETE` vai direto na tabela, sem passar pelo ORM: se a cascata
        estivesse so no `cascade=` do relacionamento, as linhas filhas
        sobreviveriam e a chave estrangeira levantaria.
        """
        conta = schema.Conta(email="ana@exemplo.com", senha_hash="h")
        sessao_de_teste.add(conta)
        sessao_de_teste.flush()

        sessao_de_teste.add(
            schema.LocalSalvo(
                conta_id=conta.id,
                name="Berlin",
                country="Germany",
                country_code="DE",
                admin1="Land Berlin",
                latitude=52.52,
                longitude=13.41,
                identidade=identidade_do_local(em(52.52, 13.41, "DE")),
            )
        )
        sessao_de_teste.add(
            schema.Sessao(id="s", conta_id=conta.id, expira_em=DAQUI_UMA_HORA)
        )
        sessao_de_teste.flush()

        sessao_de_teste.execute(
            text("DELETE FROM contas WHERE id = :id"), {"id": conta.id}
        )

        for tabela in ("locais_salvos", "sessoes"):
            restantes = sessao_de_teste.execute(
                text(f"SELECT count(*) FROM {tabela}")
            ).scalar()
            assert restantes == 0

    def test_a_unicidade_do_local_e_por_conta(self, sessao_de_teste):
        """`uq_local_por_conta` recusa a repeticao dentro da mesma conta."""
        conta = schema.Conta(email="ana@exemplo.com", senha_hash="h")
        sessao_de_teste.add(conta)
        sessao_de_teste.flush()

        identidade = identidade_do_local(em(52.52, 13.41, "DE"))
        for _ in range(2):
            sessao_de_teste.add(
                schema.LocalSalvo(
                    conta_id=conta.id,
                    name="Berlin",
                    country="Germany",
                    country_code="DE",
                    admin1=None,
                    latitude=52.52,
                    longitude=13.41,
                    identidade=identidade,
                )
            )

        with pytest.raises(IntegrityError):
            sessao_de_teste.flush()

    def test_o_instante_de_expiracao_preserva_o_fuso(self, sessao_de_teste):
        """`DateTime(timezone=True)`: o que entra com fuso volta com fuso.

        Sem isso, comparar a expiracao com `datetime.now(timezone.utc)`
        levantaria — e num banco em outro fuso compararia errado em silencio.
        """
        conta = schema.Conta(email="ana@exemplo.com", senha_hash="h")
        sessao_de_teste.add(conta)
        sessao_de_teste.flush()

        sessao_de_teste.add(
            schema.Sessao(id="s", conta_id=conta.id, expira_em=DAQUI_UMA_HORA)
        )
        sessao_de_teste.flush()
        sessao_de_teste.expire_all()

        guardada = sessao_de_teste.get(schema.Sessao, "s")
        assert guardada is not None
        assert guardada.expira_em.tzinfo is not None
        assert guardada.expira_em == DAQUI_UMA_HORA
        # `criada_em` vem do `now()` do banco, e tambem precisa trazer fuso.
        assert guardada.criada_em.tzinfo is not None

    def test_apagar_a_conta_por_sql_leva_os_planos_junto(self, sessao_de_teste):
        """A cascata dos planos e do **banco**, e nao um laco em Python.

        O `DELETE` vai direto na tabela, sem passar pelo ORM: se a cascata
        estivesse so no `cascade=` do relacionamento, os planos sobreviveriam
        e a chave estrangeira levantaria. E o mesmo caso que locais e sessoes
        ja tem, e ele existe por plano porque a coluna e nova — a garantia nao
        se herda do vizinho.
        """
        conta = schema.Conta(email="ana@exemplo.com", senha_hash="h")
        sessao_de_teste.add(conta)
        sessao_de_teste.flush()

        sessao_de_teste.add(
            schema.Plano(
                conta_id=conta.id,
                titulo="Lavar as cortinas",
                dia=TERCA,
                atividade="lavar_roupa",
            )
        )
        sessao_de_teste.flush()

        sessao_de_teste.execute(
            text("DELETE FROM contas WHERE id = :id"), {"id": conta.id}
        )

        restantes = sessao_de_teste.execute(
            text("SELECT count(*) FROM planos WHERE conta_id = :id"), {"id": conta.id}
        ).scalar_one()
        assert restantes == 0

    def test_o_banco_recusa_atividade_fora_das_quatro(self, sessao_de_teste):
        """O `CHECK` vale para quem insere **por fora** da rota.

        A rota ja recusa pelo `Literal` do Pydantic, e este caso pula a rota: e
        o que prova que a garantia sobrevive a um caminho que nao passou por
        ela — um script de importacao, um `INSERT` manual. Sem o `CHECK`, o
        banco guardaria um plano cuja atividade nenhuma regra julga, e a faixa
        nao teria aptidao para cruzar com ele.
        """
        conta = schema.Conta(email="ana@exemplo.com", senha_hash="h")
        sessao_de_teste.add(conta)
        sessao_de_teste.flush()

        sessao_de_teste.add(
            schema.Plano(
                conta_id=conta.id, titulo="Dormir", dia=TERCA, atividade="dormir"
            )
        )
        with pytest.raises(IntegrityError):
            sessao_de_teste.flush()

    def test_o_dia_do_plano_nao_guarda_hora(self, sessao_de_teste):
        """A coluna e `DATE`: uma hora nao tem onde ficar.

        O tipo e a decisao de dominio — a aptidao e diaria —, e este caso e o
        que impede que alguem a troque por `TIMESTAMP` numa migracao futura
        sem perceber o que esta prometendo.
        """
        conta = schema.Conta(email="ana@exemplo.com", senha_hash="h")
        sessao_de_teste.add(conta)
        sessao_de_teste.flush()

        sessao_de_teste.add(
            schema.Plano(
                conta_id=conta.id, titulo="Correr", dia=TERCA, atividade="esporte"
            )
        )
        sessao_de_teste.flush()
        sessao_de_teste.expire_all()

        tipo = sessao_de_teste.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'planos' AND column_name = 'dia'"
            )
        ).scalar_one()
        assert tipo == "date"
