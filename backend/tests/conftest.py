import pytest


@pytest.fixture
def anyio_backend():
    """Roda os testes assincronos so no asyncio, sem exigir trio instalado."""
    return "asyncio"
