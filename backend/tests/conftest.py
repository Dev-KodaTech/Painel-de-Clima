import pytest

from app import cache_do_processo


class Relogio:
    """Relogio injetado, avancado a mao.

    Todo teste de expiracao usa este: um que espera o TTL de verdade leva dez
    minutos, e um que encurta o TTL testa um valor que a producao nao usa.
    """

    def __init__(self) -> None:
        self.instante = 0.0

    def __call__(self) -> float:
        return self.instante

    def avancar(self, segundos: float) -> None:
        self.instante += segundos


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
    cache_do_processo.limpar()
