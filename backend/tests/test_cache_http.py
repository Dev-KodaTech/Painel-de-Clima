"""O cache visto de fora: quantas chamadas externas duas consultas produzem.

Esta e a costura que o ticket pede — nenhum teste aqui espia o interior do
cache. O que se observa e o contador de requisicoes do `respx`, que e
exatamente a cota que o cache existe para poupar.

O relogio e injetado para a expiracao; nao ha `sleep` algum.
"""

from datetime import date

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app import cache_do_processo
from app.main import app
from app.services.cache import Cache
from app.services.cache import TTL_DO_PASSADO_SEGUNDOS
from app.services.open_meteo import ARCHIVE_URL, FORECAST_URL
from tests.conftest import Relogio
from tests.fixtures import (
    ARQUIVO_BERLIM,
    ARQUIVO_BERLIM_ANTERIOR,
    FORECAST_BERLIM,
    FORECAST_DEZESSEIS_BERLIM,
    UV_BERLIM,
    atual_de_varias,
)

client = TestClient(app)

BERLIM = {
    "latitude": 52.52437,
    "longitude": 13.41053,
    "name": "Berlin",
    "country": "Germany",
    "country_code": "DE",
    "admin1": "Land Berlin",
}

#: A mesma cidade com a precisao que outra candidata traria. Arredondadas a
#: duas casas (~1,1 km), as duas sao a mesma chave.
BERLIM_QUASE_IGUAL = {**BERLIM, "latitude": 52.5244, "longitude": 13.4105}


@pytest.fixture
def relogio():
    """Substitui o cache do processo por um com relogio sob controle.

    O cache e estado de processo compartilhado: sem a troca, uma entrada
    deixada por um teste serviria o seguinte, e a ordem de execucao mudaria o
    resultado.
    """
    relogio = Relogio()
    originais = (cache_do_processo.atual(), cache_do_processo.do_passado())
    cache_do_processo.substituir(
        Cache(ttl_segundos=600, agora=relogio),
        # O **mesmo relogio** nas duas familias: o que se quer observar e que
        # elas expiram em momentos diferentes, e dois relogios independentes
        # provariam so que sao dois objetos.
        Cache(ttl_segundos=TTL_DO_PASSADO_SEGUNDOS, agora=relogio),
    )
    yield relogio
    cache_do_processo.substituir(*originais)


@respx.mock
def test_duas_consultas_iguais_produzem_uma_chamada_externa(relogio):
    """O caso que justifica o cache: a segunda consulta nao gasta cota."""
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    assert client.get("/api/weather", params=BERLIM).status_code == 200
    assert client.get("/api/weather", params=BERLIM).status_code == 200

    assert rota.call_count == 1


@respx.mock
def test_apos_o_ttl_a_consulta_volta_a_bater_na_api(relogio):
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    client.get("/api/weather", params=BERLIM)
    relogio.avancar(601)
    client.get("/api/weather", params=BERLIM)

    assert rota.call_count == 2


@respx.mock
def test_coordenadas_proximas_compartilham_a_entrada(relogio):
    """A mesma cidade vinda de duas candidatas nao vira duas chamadas."""
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    client.get("/api/weather", params=BERLIM)
    client.get("/api/weather", params=BERLIM_QUASE_IGUAL)

    assert rota.call_count == 1


@respx.mock
def test_cidades_distintas_nao_compartilham_a_entrada(relogio):
    rota = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    client.get("/api/weather", params=BERLIM)
    client.get(
        "/api/weather",
        params={**BERLIM, "latitude": 48.85341, "longitude": 2.3488, "name": "Paris"},
    )

    assert rota.call_count == 2


@respx.mock
def test_a_consulta_servida_do_cache_devolve_o_mesmo_painel(relogio):
    """Servir do cache nao pode mudar o que o usuario ve."""
    respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )

    primeira = client.get("/api/weather", params=BERLIM).json()
    segunda = client.get("/api/weather", params=BERLIM).json()

    assert primeira == segunda


@respx.mock
def test_falha_da_api_nao_fica_cacheada(relogio):
    """Uma indisponibilidade passageira nao pode prender o painel por 10 min."""
    rota = respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("sem rede"))

    assert client.get("/api/weather", params=BERLIM).status_code == 503

    rota.mock(return_value=httpx.Response(200, json=FORECAST_BERLIM))

    assert client.get("/api/weather", params=BERLIM).status_code == 200


@pytest.fixture
def app_com_dataset():
    """O app com o `lifespan` executado, e portanto com o dataset carregado.

    Sem ele a lista de cidades fica vazia, o bloco `nearby` sai vazio e a
    **segunda** chamada externa nunca acontece — os testes acima contam so a da
    previsao, ainda que as duas batam na mesma URL.
    """
    with TestClient(app) as cliente:
        yield cliente


def _mockar_as_duas_chamadas():
    """As duas chamadas batem na mesma URL e se distinguem pelos parametros.

    A da previsao pede sete dias; a das vizinhas pede um. Contar as duas
    separadamente e o que torna visivel que o cache cobre **as duas**, e nao
    so a cara.
    """
    previsao = respx.get(FORECAST_URL, params__contains={"forecast_days": "7"}).mock(
        return_value=httpx.Response(200, json=FORECAST_BERLIM)
    )
    vizinhas = respx.get(FORECAST_URL, params__contains={"forecast_days": "1"}).mock(
        return_value=httpx.Response(200, json=atual_de_varias(TEMPERATURAS_VIZINHAS))
    )
    return previsao, vizinhas


#: Uma por vizinha de Berlim, todas distintas.
TEMPERATURAS_VIZINHAS = [11.1, 12.2, 13.3, 14.4, 15.5]


@respx.mock
def test_o_cache_cobre_tambem_a_chamada_das_vizinhas(relogio, app_com_dataset):
    """Ambas as chamadas externas sao poupadas, nao apenas a da previsao."""
    previsao, vizinhas = _mockar_as_duas_chamadas()

    primeiro = app_com_dataset.get("/api/weather", params=BERLIM).json()
    segundo = app_com_dataset.get("/api/weather", params=BERLIM).json()

    # A primeira consulta faz as duas; a segunda, nenhuma.
    assert previsao.call_count == 1
    assert vizinhas.call_count == 1
    # E a tabela servida do cache continua preenchida e igual.
    assert len(segundo["nearby"]) == 5
    assert primeiro["nearby"] == segundo["nearby"]


@respx.mock
def test_apos_o_ttl_as_duas_chamadas_sao_refeitas(relogio, app_com_dataset):
    previsao, vizinhas = _mockar_as_duas_chamadas()

    app_com_dataset.get("/api/weather", params=BERLIM)
    relogio.avancar(601)
    app_com_dataset.get("/api/weather", params=BERLIM)

    assert previsao.call_count == 2
    assert vizinhas.call_count == 2


TENDENCIA_BERLIM = {"latitude": 52.52437, "longitude": 13.41053}


def _mockar_o_historico():
    """As duas chamadas ao arquivo, contadas separadamente pelo intervalo.

    Elas batem na mesma URL, entao o que as distingue e o `start_date` — e e
    justamente a separacao que este arquivo precisa, porque as duas tem **TTLs
    diferentes**.
    """
    chamadas = {"recente": 0, "passado": 0}

    def responder(request: httpx.Request) -> httpx.Response:
        inicio = request.url.params["start_date"]
        if inicio.startswith(str(date.today().year - 1)):
            chamadas["passado"] += 1
            return httpx.Response(200, json=ARQUIVO_BERLIM_ANTERIOR)
        chamadas["recente"] += 1
        return httpx.Response(200, json=ARQUIVO_BERLIM)

    respx.get(ARCHIVE_URL).mock(side_effect=responder)
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=UV_BERLIM))
    return chamadas


@respx.mock
def test_duas_consultas_ao_historico_produzem_uma_chamada_ao_arquivo(relogio):
    chamadas = _mockar_o_historico()

    client.get("/api/trends", params=TENDENCIA_BERLIM)
    client.get("/api/trends", params=TENDENCIA_BERLIM)

    assert chamadas == {"recente": 1, "passado": 1}


@respx.mock
def test_janelas_diferentes_da_mesma_cidade_sao_consultas_diferentes(relogio):
    """Pelo mesmo motivo que a chave inclui a coordenada: sao pedidos distintos.

    Sem a janela na chave, trocar de 7 dias para 30 devolveria os sete dias
    guardados — o cache erraria justamente no caso que a pagina mais exercita.
    """
    chamadas = _mockar_o_historico()

    client.get("/api/trends", params={**TENDENCIA_BERLIM, "janela": "7d"})
    client.get("/api/trends", params={**TENDENCIA_BERLIM, "janela": "30d"})

    assert chamadas["recente"] == 2


@respx.mock
def test_voltar_a_janela_ja_vista_nao_gasta_cota(relogio):
    """A historia que o cache atende: trocar de janela e voltar e instantaneo.

    A pagina refaz a requisicao a cada visita — o historico e buscado nela, nao
    no `Shell` —, e e o cache do backend que absorve isso.
    """
    chamadas = _mockar_o_historico()

    client.get("/api/trends", params={**TENDENCIA_BERLIM, "janela": "7d"})
    client.get("/api/trends", params={**TENDENCIA_BERLIM, "janela": "30d"})
    client.get("/api/trends", params={**TENDENCIA_BERLIM, "janela": "7d"})

    assert chamadas["recente"] == 2


@respx.mock
def test_o_ano_anterior_sobrevive_ao_ttl_curto(relogio):
    """**As duas familias de TTL, observadas de fora.**

    Passado o TTL do painel, a janela atual e rebuscada — o dia corrente ainda
    muda — e a do ano anterior nao: aquele setembro ja esta fechado, e
    reconsulta-lo gastaria cota para receber os mesmos numeros.
    """
    chamadas = _mockar_o_historico()

    client.get("/api/trends", params=TENDENCIA_BERLIM)
    relogio.avancar(601)
    client.get("/api/trends", params=TENDENCIA_BERLIM)

    assert chamadas["recente"] == 2
    assert chamadas["passado"] == 1


@respx.mock
def test_passado_o_ttl_longo_o_ano_anterior_tambem_e_rebuscado(relogio):
    """Longo nao e infinito: a reanalise recebe correcoes tardias raras."""
    chamadas = _mockar_o_historico()

    client.get("/api/trends", params=TENDENCIA_BERLIM)
    relogio.avancar(TTL_DO_PASSADO_SEGUNDOS + 1)
    client.get("/api/trends", params=TENDENCIA_BERLIM)

    assert chamadas["passado"] == 2


# ---------------------------------------------------------------------------
# O horizonte de dezesseis dias da pagina Calendario.


HORIZONTE_BERLIM = {"latitude": 52.52437, "longitude": 13.41053}


def _mockar_as_duas_previsoes():
    """As duas chamadas de previsao, contadas separadamente por `forecast_days`.

    Elas batem na mesma URL e so se distinguem pelos parametros — que e
    exatamente o que este arquivo precisa provar: que as **chaves de cache** nao
    colidem, ainda que a URL seja uma so.
    """
    sete, _ = _mockar_as_duas_chamadas()
    dezesseis = respx.get(FORECAST_URL, params__contains={"forecast_days": "16"}).mock(
        return_value=httpx.Response(200, json=FORECAST_DEZESSEIS_BERLIM)
    )
    return sete, dezesseis


@respx.mock
def test_duas_consultas_ao_horizonte_produzem_uma_chamada_externa(relogio):
    """O caso que justifica o cache, na chamada mais cara do app."""
    _, dezesseis = _mockar_as_duas_previsoes()

    assert client.get("/api/horizonte", params=HORIZONTE_BERLIM).status_code == 200
    assert client.get("/api/horizonte", params=HORIZONTE_BERLIM).status_code == 200

    assert dezesseis.call_count == 1


@respx.mock
def test_o_horizonte_nao_colide_com_a_previsao_de_sete_dias(relogio):
    """**A chave tem prefixo proprio, e e isto que o prova.**

    As duas chamadas partem da mesma coordenada e batem na mesma URL. Sem
    prefixos distintos, pedir o painel e depois os dezesseis dias devolveria os
    sete guardados — e a grade perderia nove dias sem erro algum, que e o pior
    modo de falhar.
    """
    sete, dezesseis = _mockar_as_duas_previsoes()

    painel = client.get("/api/weather", params=BERLIM)
    grade = client.get("/api/horizonte", params=HORIZONTE_BERLIM)

    assert sete.call_count == 1
    assert dezesseis.call_count == 1
    # E cada uma devolveu o seu: sete dias no painel, dezesseis na grade.
    assert len(painel.json()["daily"]) == 7
    assert len(grade.json()["dias"]) == 16


@respx.mock
def test_apos_o_ttl_o_horizonte_volta_a_bater_na_api(relogio):
    """Familia de dez minutos, como as demais: e previsao, e ela muda."""
    _, dezesseis = _mockar_as_duas_previsoes()

    client.get("/api/horizonte", params=HORIZONTE_BERLIM)
    relogio.avancar(601)
    client.get("/api/horizonte", params=HORIZONTE_BERLIM)

    assert dezesseis.call_count == 2
