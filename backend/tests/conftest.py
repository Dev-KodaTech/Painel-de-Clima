import pytest

from app.services import open_meteo


@pytest.fixture
def anyio_backend():
    """Roda os testes assincronos so no asyncio, sem exigir trio instalado."""
    return "asyncio"


@pytest.fixture(autouse=True)
def cache_limpo():
    """Esvazia o cache do processo antes de cada teste.

    O cache e **estado de processo**: sem isto, a previsao que um teste deixa
    guardada e servida ao seguinte, que mockou outra resposta para a mesma
    coordenada. O sintoma seria uma falha que depende da ordem de execucao e
    some quando o teste roda sozinho.

    Autouse porque a armadilha atinge todo teste que bate em `/api/weather`,
    inclusive os que ainda nao existem — deixar a limpeza a cargo de quem
    escreve o teste seria confiar em que ninguem esquecera.
    """
    open_meteo.cache.limpar()
