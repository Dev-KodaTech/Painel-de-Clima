"""A transacao do banco: o `engine` e a fabrica de sessoes do SQLAlchemy.

**Nao se chama `sessao.py`** de proposito. `CONTEXT.md` reserva *sessao* para a
prova de que quem esta pedindo e o dono da conta — a linha da tabela e o cookie
—, e a sessao do SQLAlchemy e outra coisa inteira: uma unidade de trabalho
sobre uma conexao. Dois sentidos no mesmo nome, no mesmo pacote, e o tipo de
colisao que faz alguem ler `sessao.criar()` e entender o contrario do que o
codigo faz.

O `engine` mora aqui pela mesma razao que `cache_do_processo.py` e
`dataset.py`: e
**estado do processo**, nao logica. O `engine` guarda um pool de conexoes e
tem de existir uma vez por processo — um por requisicao abriria e fecharia
conexao a cada chamada.

Criado **sob demanda**, e nao na importacao: a suite padrao nao tem banco, e
um `create_engine` no topo do modulo faria `import app.main` exigir Postgres.
A URL e lida na primeira sessao, o que tambem permite ao teste marcado
apontar para outro banco pelo ambiente.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import database_url

#: **Uma** variavel, e nao um par `_engine`/`_fabrica` mantido em sincronia: a
#: fabrica carrega o proprio engine em `.kw["bind"]`, e dois globais que
#: precisam ser preenchidos juntos sao dois que podem discordar.
_fabrica: sessionmaker[Session] | None = None


def _fabrica_do_processo() -> sessionmaker[Session]:
    """A fabrica de sessoes, criada na primeira chamada."""
    global _fabrica
    if _fabrica is None:
        criado = create_engine(database_url(), pool_pre_ping=True)
        _fabrica = sessionmaker(bind=criado, expire_on_commit=False)
    return _fabrica


def engine() -> Engine:
    """O `engine` do processo. Existe para quem precisa dele direto: as
    migracoes e o descarte."""
    return cast(Engine, _fabrica_do_processo().kw["bind"])


@contextmanager
def transacao() -> Iterator[Session]:
    """Uma sessao do SQLAlchemy com transacao: comita ao sair, desfaz se algo
    levantar.

    O `commit` aqui e nao no repositorio: a transacao pertence a requisicao,
    que pode escrever em mais de uma tabela — abrir conta e abrir sessao e um
    caso, e as duas coisas precisam acontecer juntas ou nenhuma.
    """
    with _fabrica_do_processo()() as aberta:
        try:
            yield aberta
            aberta.commit()
        except Exception:
            aberta.rollback()
            raise


def descartar() -> None:
    """Fecha o pool e esquece a fabrica. Para o teste nao vazar conexao."""
    global _fabrica
    if _fabrica is not None:
        engine().dispose()
    _fabrica = None
