"""O acesso ao banco, atras de uma interface — e as duas implementacoes.

Existe por uma razao de teste, e ela decide a qualidade da suite daqui em
diante. A suite padrao roda contra `RepositorioEmMemoria` e continua rodando em
cerca de um segundo, **sem exigir Docker de ninguem**; um punhado de testes
marcados roda contra o Postgres real sob demanda, exatamente como o teste de
contrato ja faz com a API externa. Sem esses, o repositorio em memoria
esconderia erros de SQL; sem o em memoria, a suite inteira dependeria de
infraestrutura.

As duas implementacoes precisam concordar, e e por isso que os testes de
schema rodam **a mesma bateria** contra as duas: o em memoria nao e um mock
escrito por teste, e uma implementacao de verdade da mesma interface.

O que **nao** mora aqui: hash de senha, geracao de identificador de sessao e
qualquer regra de quem pode o que. Isto e guarda-volumes, e os tickets
seguintes trazem as regras.

Nao ha `apagar_conta`: apagar a conta esta fora de escopo (e lacuna conhecida,
registrada na spec). Que apagar uma conta leve seus locais e suas sessoes junto
e garantia do **schema**, por `ON DELETE CASCADE`, e e testada onde ela mora —
em SQL cru, em `TestSchemaNoPostgres`. Um metodo aqui so para o teste
alcanca-la seria codigo de producao que nenhuma producao chama.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.orm import Session as SessaoDoSqlAlchemy  # nao a `Sessao` do dominio

from app.db import schema
from app.models import CidadeEscolhida
from app.services.cache import CASAS_DA_CHAVE

#: Casas decimais da coordenada na identidade do local salvo.
#:
#: E **a mesma constante** da chave do cache, importada e nao redeclarada: uma
#: regra de arredondamento em duas copias divergiria no dia em que uma fosse
#: ajustada, e aqui as duas existem pela mesma razao — `52.52437` e `52.5244`
#: sao a mesma cidade vinda de duas candidatas com precisao diferente.
CASAS_DA_IDENTIDADE = CASAS_DA_CHAVE


def identidade_do_local(cidade: CidadeEscolhida) -> str:
    """A identidade de um local salvo, para efeito de nao duplicar.

    Coordenada arredondada mais codigo do pais. O pais entra porque o
    arredondamento a ~1 km nao separa sozinho dois lugares homonimos vizinhos
    de fronteira, e o codigo e o dado que a API externa sempre fornece.
    """
    return (
        f"{cidade.latitude:.{CASAS_DA_IDENTIDADE}f},"
        f"{cidade.longitude:.{CASAS_DA_IDENTIDADE}f},"
        f"{cidade.country_code.upper()}"
    )


@dataclass(frozen=True)
class Conta:
    """Uma conta, como o resto da aplicacao a ve.

    **Nao carrega a senha nem o hash dela.** Devolver o hash junto do e-mail
    poria a credencial em toda leitura de conta, e um dia em log ou resposta de
    erro; quem precisa verificar senha pede o hash explicitamente por
    `hash_da_senha`.
    """

    id: int
    email: str


@dataclass(frozen=True)
class Sessao:
    id: str
    conta_id: int
    expira_em: datetime


@dataclass(frozen=True)
class LocalSalvo:
    """Um local salvo: a cidade, e nada de clima.

    A cidade vem como `CidadeEscolhida` — o mesmo tipo que ja viaja na URL e
    que `/api/weather` recebe — e nao como seis campos soltos. Os seis andavam
    juntos por cinco assinaturas, e o projeto ja tinha o tipo que os agrupa.
    """

    id: int
    conta_id: int
    cidade: CidadeEscolhida


class Repositorio(ABC):
    """O acesso ao banco, do ponto de vista da aplicacao.

    Metodos sincronos, ao contrario do cliente da API externa: o driver e
    sincrono e o SQL local custa menos que o overhead de uma thread. Os
    endpoints que os chamam sao `def`, nao `async def` — o FastAPI os roda no
    pool de threads e o loop nao bloqueia.
    """

    # -- contas ------------------------------------------------------------

    def criar_conta(self, email: str, senha_hash: str) -> Conta:
        """Cria a conta. Levanta `EmailJaUsado` se o e-mail ja existe.

        A comparacao **nao diferencia maiusculas**: `ana@x.com` e `Ana@X.com`
        sao a mesma conta.

        Concreto no ABC, e nao abstrato: a checagem e identica nas duas
        implementacoes, e duplica-la seria duas chances de uma esquecer. O que
        cada uma implementa e so a insercao, em `_inserir_conta`.

        No SQL a consulta antes da insercao **nao** e a garantia — o indice
        unico e. Sob concorrencia, quem perder a corrida leva `IntegrityError`
        do banco, e e o comportamento certo: a alternativa seria duas contas
        com o mesmo e-mail.
        """
        if self.conta_por_email(email) is not None:
            raise EmailJaUsado(email)
        return self._inserir_conta(email, senha_hash)

    @abstractmethod
    def _inserir_conta(self, email: str, senha_hash: str) -> Conta:
        """Grava a conta. Chamado por `criar_conta`, ja com o e-mail livre."""

    @abstractmethod
    def conta_por_email(self, email: str) -> Conta | None:
        """A conta desse e-mail, sem diferenciar maiusculas, ou `None`."""

    @abstractmethod
    def conta_por_id(self, conta_id: int) -> Conta | None: ...

    @abstractmethod
    def hash_da_senha(self, conta_id: int) -> str | None:
        """O hash guardado, para a verificacao de senha.

        Separado de `Conta` de proposito: a credencial so sai do banco para
        quem a pede pelo nome.
        """

    # -- sessoes -----------------------------------------------------------

    @abstractmethod
    def criar_sessao(self, id: str, conta_id: int, expira_em: datetime) -> Sessao: ...

    @abstractmethod
    def sessao(self, id: str) -> Sessao | None:
        """A sessao, **mesmo expirada**.

        Quem decide se ainda vale e a camada de cima, com o relogio que ela ja
        injeta: um repositorio que filtrasse por expiracao precisaria de um
        relogio proprio, e os testes de expiracao passariam a controlar dois.
        """

    @abstractmethod
    def apagar_sessao(self, id: str) -> None:
        """Apaga **esta** sessao. As outras da mesma conta continuam valendo."""

    # -- locais salvos -----------------------------------------------------

    @abstractmethod
    def locais_salvos(self, conta_id: int) -> list[LocalSalvo]:
        """Os locais da conta, do mais antigo ao mais recente.

        Ordem estavel para que a lista seja reencontrada onde foi deixada.
        """

    @abstractmethod
    def salvar_local(self, conta_id: int, cidade: CidadeEscolhida) -> LocalSalvo:
        """Acrescenta um local a conta. Salvar um ja salvo **nao duplica**.

        Devolve o local existente nesse caso, em vez de levantar: salvar duas
        vezes e o que acontece quando alguem clica duas vezes na estrela, e
        isso nao e erro.
        """

    @abstractmethod
    def remover_local(self, conta_id: int, local_id: int) -> bool:
        """Apaga o local **se for dessa conta**. Devolve se apagou.

        A conta entra na condicao, e nao so no `if` de quem chama: e o que
        impede alguem de remover o local de outra conta acertando o
        identificador.
        """


class EmailJaUsado(Exception):
    """O e-mail ja tem conta. Levantada por `criar_conta`."""


class RepositorioEmMemoria(Repositorio):
    """A implementacao da suite padrao: dicionarios, sem banco algum.

    Nao e um mock. Implementa as mesmas regras que o SQL implementa — a
    unicidade do e-mail sem maiusculas, a nao duplicacao por identidade, a
    remocao em cascata — e os testes de schema provam que as duas concordam.
    """

    def __init__(self) -> None:
        self._contas: dict[int, _ContaGuardada] = {}
        self._sessoes: dict[str, Sessao] = {}
        self._locais: dict[int, LocalSalvo] = {}
        self._proxima_conta = count(1)
        self._proximo_local = count(1)

    def _inserir_conta(self, email: str, senha_hash: str) -> Conta:
        guardada = _ContaGuardada(
            id=next(self._proxima_conta), email=email, senha_hash=senha_hash
        )
        self._contas[guardada.id] = guardada
        return guardada.publica()

    def conta_por_email(self, email: str) -> Conta | None:
        procurado = email.casefold()
        for guardada in self._contas.values():
            if guardada.email.casefold() == procurado:
                return guardada.publica()
        return None

    def conta_por_id(self, conta_id: int) -> Conta | None:
        guardada = self._contas.get(conta_id)
        return None if guardada is None else guardada.publica()

    def hash_da_senha(self, conta_id: int) -> str | None:
        guardada = self._contas.get(conta_id)
        return None if guardada is None else guardada.senha_hash

    def criar_sessao(self, id: str, conta_id: int, expira_em: datetime) -> Sessao:
        sessao = Sessao(id=id, conta_id=conta_id, expira_em=expira_em)
        self._sessoes[id] = sessao
        return sessao

    def sessao(self, id: str) -> Sessao | None:
        return self._sessoes.get(id)

    def apagar_sessao(self, id: str) -> None:
        self._sessoes.pop(id, None)

    def locais_salvos(self, conta_id: int) -> list[LocalSalvo]:
        # A ordem de insercao dos dicionarios e a ordem cronologica, que e o
        # que o SQL obtem ordenando por `salvo_em, id`.
        return [local for local in self._locais.values() if local.conta_id == conta_id]

    def salvar_local(self, conta_id: int, cidade: CidadeEscolhida) -> LocalSalvo:
        identidade = identidade_do_local(cidade)
        for local in self.locais_salvos(conta_id):
            if identidade_do_local(local.cidade) == identidade:
                return local

        local = LocalSalvo(
            id=next(self._proximo_local), conta_id=conta_id, cidade=cidade
        )
        self._locais[local.id] = local
        return local

    def remover_local(self, conta_id: int, local_id: int) -> bool:
        local = self._locais.get(local_id)
        if local is None or local.conta_id != conta_id:
            return False
        del self._locais[local_id]
        return True


@dataclass
class _ContaGuardada:
    """A conta com o hash, que so o repositorio em memoria ve."""

    id: int
    email: str
    senha_hash: str

    def publica(self) -> Conta:
        return Conta(id=self.id, email=self.email)


class RepositorioSql(Repositorio):
    """A implementacao de producao, sobre uma sessao do SQLAlchemy.

    Recebe a sessao em vez de cria-la: e o que permite ao endpoint abrir uma
    transacao por requisicao e ao teste marcado usar uma que ele desfaz no
    fim.
    """

    def __init__(self, sessao: SessaoDoSqlAlchemy) -> None:
        #: A sessao **do SQLAlchemy** — a unidade de trabalho —, e nao a
        #: `Sessao` do dominio que este mesmo modulo define. O alias no import
        #: existe para que a assinatura nao pareca receber a segunda.
        self._sessao = sessao

    def _inserir_conta(self, email: str, senha_hash: str) -> Conta:
        linha = schema.Conta(email=email, senha_hash=senha_hash)
        self._sessao.add(linha)
        self._sessao.flush()
        return Conta(id=linha.id, email=linha.email)

    def conta_por_email(self, email: str) -> Conta | None:
        linha = self._sessao.scalars(
            select(schema.Conta).where(
                func.lower(schema.Conta.email) == email.casefold()
            )
        ).first()
        return None if linha is None else Conta(id=linha.id, email=linha.email)

    def conta_por_id(self, conta_id: int) -> Conta | None:
        linha = self._sessao.get(schema.Conta, conta_id)
        return None if linha is None else Conta(id=linha.id, email=linha.email)

    def hash_da_senha(self, conta_id: int) -> str | None:
        return self._sessao.scalars(
            select(schema.Conta.senha_hash).where(schema.Conta.id == conta_id)
        ).first()

    def criar_sessao(self, id: str, conta_id: int, expira_em: datetime) -> Sessao:
        linha = schema.Sessao(id=id, conta_id=conta_id, expira_em=expira_em)
        self._sessao.add(linha)
        self._sessao.flush()
        return Sessao(id=linha.id, conta_id=linha.conta_id, expira_em=linha.expira_em)

    def sessao(self, id: str) -> Sessao | None:
        linha = self._sessao.get(schema.Sessao, id)
        if linha is None:
            return None
        return Sessao(id=linha.id, conta_id=linha.conta_id, expira_em=linha.expira_em)

    def apagar_sessao(self, id: str) -> None:
        self._sessao.execute(delete(schema.Sessao).where(schema.Sessao.id == id))

    def locais_salvos(self, conta_id: int) -> list[LocalSalvo]:
        linhas = self._sessao.scalars(
            select(schema.LocalSalvo)
            .where(schema.LocalSalvo.conta_id == conta_id)
            # `id` como segundo criterio: `salvo_em` vem do `now()` do banco,
            # que e o mesmo instante para tudo que entra na mesma transacao.
            .order_by(schema.LocalSalvo.salvo_em, schema.LocalSalvo.id)
        ).all()
        return [_local_publico(linha) for linha in linhas]

    def salvar_local(self, conta_id: int, cidade: CidadeEscolhida) -> LocalSalvo:
        identidade = identidade_do_local(cidade)
        existente = self._sessao.scalars(
            select(schema.LocalSalvo).where(
                schema.LocalSalvo.conta_id == conta_id,
                schema.LocalSalvo.identidade == identidade,
            )
        ).first()
        if existente is not None:
            return _local_publico(existente)

        linha = schema.LocalSalvo(
            conta_id=conta_id,
            name=cidade.name,
            country=cidade.country,
            country_code=cidade.country_code,
            admin1=cidade.admin1,
            latitude=cidade.latitude,
            longitude=cidade.longitude,
            identidade=identidade,
        )
        self._sessao.add(linha)
        self._sessao.flush()
        return _local_publico(linha)

    def remover_local(self, conta_id: int, local_id: int) -> bool:
        # `CursorResult` e o tipo que um `DELETE` devolve, e e quem tem
        # `rowcount`; o `Result` generico da assinatura de `execute` nao tem.
        resultado = cast(
            "CursorResult[Any]",
            self._sessao.execute(
                delete(schema.LocalSalvo).where(
                    schema.LocalSalvo.id == local_id,
                    # A conta na condicao do `DELETE`, nao num `if` antes dele.
                    schema.LocalSalvo.conta_id == conta_id,
                )
            ),
        )
        return resultado.rowcount > 0


def _local_publico(linha: schema.LocalSalvo) -> LocalSalvo:
    return LocalSalvo(
        id=linha.id,
        conta_id=linha.conta_id,
        cidade=CidadeEscolhida(
            name=linha.name,
            country=linha.country,
            country_code=linha.country_code,
            admin1=linha.admin1,
            latitude=linha.latitude,
            longitude=linha.longitude,
        ),
    )
