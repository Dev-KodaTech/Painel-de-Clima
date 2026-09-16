"""Costura HTTP de `/api/trends`: os blocos da pagina e as armadilhas do arquivo.

A costura e a mesma de `test_weather.py` — `TestClient` mais `respx` — e pelo
mesmo motivo: e a mais alta disponivel, exercita router, servico, modelos e
serializacao de uma vez, e continua valendo se os modulos internos forem
reorganizados. Nenhum teste aqui espia o interior do cache nem chama funcao
privada.

As datas sao lidas **da resposta**, nao fixadas: a janela termina hoje, e um
teste que carimbasse "2026-09-15" quebraria amanha sem que nada tivesse
quebrado.
"""

from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.services.historico import DIAS_DA_JANELA
from app.services.open_meteo import ARCHIVE_URL, FORECAST_URL
from tests.fixtures import (
    ARQUIVO_BERLIM,
    ARQUIVO_BERLIM_ANTERIOR,
    ARQUIVO_COM_UV_NULO,
    ARQUIVO_INCOMPLETO,
    ARQUIVO_VAZIO,
    UV_BERLIM,
)

client = TestClient(app)

BERLIM = {"latitude": 52.52437, "longitude": 13.41053}


class Chamadas:
    """Quantas vezes cada intervalo foi pedido ao arquivo.

    As duas chamadas batem na **mesma URL** e se distinguem so pelo intervalo,
    entao o roteamento e por `start_date`: o da janela do ano anterior comeca
    num ano que ja passou. Conta-las separadamente e o que torna verificavel
    que sao duas chamadas, e nao uma com intervalo largo.
    """

    def __init__(self, atual: dict, anterior: dict) -> None:
        self.atual = atual
        self.anterior = anterior
        self.recente = 0
        self.passado = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        inicio = request.url.params["start_date"]
        if inicio.startswith(str(date.today().year - 1)):
            self.passado += 1
            return httpx.Response(200, json=self.anterior)
        self.recente += 1
        return httpx.Response(200, json=self.atual)


def _mockar(atual=None, anterior=None, uv=None) -> Chamadas:
    """As duas chamadas ao arquivo e a do UV."""
    chamadas = Chamadas(atual or ARQUIVO_BERLIM, anterior or ARQUIVO_BERLIM_ANTERIOR)
    respx.get(ARCHIVE_URL).mock(side_effect=chamadas)
    respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=uv or UV_BERLIM)
    )
    return chamadas


def _buscar(**extras):
    return client.get("/api/trends", params={**BERLIM, **extras})


@respx.mock
def test_o_payload_traz_um_bloco_por_parte_da_pagina():
    """As seis chaves do contrato: uma por parte da pagina, mais unidades."""
    _mockar()

    corpo = _buscar().json()

    assert set(corpo) == {
        "periodo",
        "serie",
        "comparacao",
        "uv",
        "resumo",
        "units",
        "attribution",
    }
    assert corpo["units"] == {
        "temperature": "°C",
        "precipitation": "mm",
        "wind_speed": "km/h",
        "humidity": "%",
        # Vazia: o indice UV nao tem unidade.
        "uv": "",
    }
    assert corpo["attribution"]


class TestJanelaTemporal:
    @respx.mock
    @pytest.mark.parametrize("janela", ["7d", "30d", "6m"])
    def test_cada_janela_produz_o_intervalo_do_seu_tamanho(self, janela):
        _mockar()

        periodo = _buscar(janela=janela).json()["periodo"]

        inicio = date.fromisoformat(periodo["inicio"])
        fim = date.fromisoformat(periodo["fim"])

        assert periodo["janela"] == janela
        # As duas pontas incluidas: sete dias vao de hoje-6 a hoje.
        assert (fim - inicio).days + 1 == DIAS_DA_JANELA[janela]

    @respx.mock
    def test_a_janela_termina_hoje_porque_o_arquivo_cobre_o_dia_corrente(self):
        """Medido: o arquivo responde para o dia corrente, sem lag."""
        _mockar()

        periodo = _buscar(janela="7d").json()["periodo"]

        # Sem margem: a ponta e ancorada em UTC justamente para ser exata. Uma
        # tolerancia de um dia aqui esconderia o pedido fora de faixa que o
        # arquivo recusa — ver o teste de regressao acima.
        assert periodo["fim"] == datetime.now(timezone.utc).date().isoformat()

    @respx.mock
    @pytest.mark.parametrize(
        ("cidade", "longitude"),
        [("Wellington", 174.77), ("Honolulu", -157.86), ("Kiritimati", -157.48)],
    )
    def test_o_arquivo_nunca_e_pedido_alem_do_dia_corrente_em_utc(
        self, cidade, longitude
    ):
        """**Regressao.** Wellington (UTC+12) ja esta no dia seguinte enquanto o
        arquivo so vai ate hoje em UTC, e pedir esse dia devolve `400` — que
        chegava ao usuario como `503` e a pagina inteira nao abria.

        A reanalise e publicada num calendario so, entao a ponta da janela e
        ancorada em UTC e nao na hora local da cidade. O teste vale para os dois
        extremos do globo: a cidade adiantada nao pode pedir demais, e a atrasada
        nao pode perder dias.
        """
        pedidos = []

        def responder(request: httpx.Request) -> httpx.Response:
            pedidos.append(request.url.params["end_date"])
            return httpx.Response(200, json=ARQUIVO_BERLIM)

        respx.get(ARCHIVE_URL).mock(side_effect=responder)
        respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=UV_BERLIM))

        resposta = client.get(
            "/api/trends",
            params={"latitude": 0.0, "longitude": longitude, "janela": "7d"},
        )

        assert resposta.status_code == 200
        hoje = datetime.now(timezone.utc).date()
        assert date.fromisoformat(pedidos[0]) <= hoje
        # E nao anterior a hoje: perder o dia corrente descartaria um dia de
        # dado que o arquivo tem.
        assert date.fromisoformat(pedidos[0]) == hoje

    @respx.mock
    def test_a_janela_do_ano_anterior_usa_a_mesma_data_de_calendario(self):
        """Setembro com setembro, e nao o mesmo dia da semana.

        Alinhar por dia da semana deslocaria a comparacao em ate tres dias, e a
        pergunta da pagina e "este mes esta fora do normal?".
        """
        _mockar()

        periodo = _buscar(janela="30d").json()["periodo"]

        inicio = date.fromisoformat(periodo["inicio"])
        anterior = date.fromisoformat(periodo["inicio_anterior"])

        assert anterior.year == inicio.year - 1
        assert (anterior.month, anterior.day) == (inicio.month, inicio.day)

    @respx.mock
    def test_as_duas_janelas_tem_o_mesmo_comprimento(self):
        """Comparar 183 dias com 182 tornaria os acumulados incomparaveis."""
        _mockar()

        periodo = _buscar(janela="6m").json()["periodo"]

        atual = date.fromisoformat(periodo["fim"]) - date.fromisoformat(
            periodo["inicio"]
        )
        anterior = date.fromisoformat(periodo["fim_anterior"]) - date.fromisoformat(
            periodo["inicio_anterior"]
        )

        assert atual == anterior

    @respx.mock
    def test_sem_janela_a_pagina_abre_nos_sete_dias(self):
        _mockar()

        assert _buscar().json()["periodo"]["janela"] == "7d"

    @respx.mock
    @pytest.mark.parametrize("invalida", ["6000d", "1y", "", "7"])
    def test_janela_fora_do_conjunto_fechado_e_422(self, invalida):
        """O conjunto fechado e o que impede "6000d" de virar dezesseis anos."""
        _mockar()

        assert _buscar(janela=invalida).status_code == 422

    @respx.mock
    def test_sao_duas_chamadas_ao_arquivo_e_nao_uma(self):
        """Um intervalo por requisicao: pedir de setembro passado ate hoje
        traria 365 dias para usar 7."""
        chamadas = _mockar()

        _buscar(janela="7d")

        assert chamadas.recente == 1
        assert chamadas.passado == 1


class TestHistoricoClimatologico:
    @respx.mock
    def test_a_serie_traz_um_ponto_por_dia_do_arquivo(self):
        _mockar()

        serie = _buscar().json()["serie"]

        assert len(serie) == 7
        assert serie[0]["date"] == "2026-09-09"
        assert serie[0]["high"] == 21.2
        assert serie[0]["low"] == 16.0

    @respx.mock
    def test_cada_ponto_traz_chuva_umidade_e_vento(self):
        """As tres variaveis novas existem no arquivo — so o UV falta."""
        _mockar()

        ponto = _buscar().json()["serie"][4]

        assert ponto["precipitation_mm"] == 2.1
        assert ponto["humidity"] == 80
        assert ponto["wind_speed"] == 13.7
        assert ponto["wind_direction"] == 239

    @respx.mock
    def test_a_comparacao_tem_a_mesma_forma_da_serie(self):
        """Duas series no mesmo grafico so funcionam se tiverem a mesma forma."""
        _mockar()

        corpo = _buscar().json()

        assert set(corpo["comparacao"][0]) == set(corpo["serie"][0])
        assert corpo["comparacao"][0]["date"].startswith("2025-")

    @respx.mock
    def test_a_diferenca_media_conclui_a_comparacao_em_numeros(self):
        """A conclusao vem pronta: a pagina nao reimplementa estatistica."""
        _mockar()

        resumo = _buscar().json()["resumo"]

        assert resumo["temperatura_media"] is not None
        assert resumo["temperatura_media_anterior"] is not None
        # A fixture do ano anterior e deliberadamente mais fria.
        assert resumo["diferenca_media"] > 0

    @respx.mock
    def test_sem_arquivo_do_ano_anterior_a_comparacao_vem_vazia_e_a_atual_intacta(self):
        """Caminho normal, nao erro: a pagina esconde a segunda serie."""
        _mockar(anterior=ARQUIVO_VAZIO)

        corpo = _buscar().json()

        assert corpo["comparacao"] == []
        assert len(corpo["serie"]) == 7
        # Sem os dois periodos nao ha diferenca — e `null`, nao zero, que diria
        # "os dois foram iguais".
        assert corpo["resumo"]["diferenca_media"] is None
        assert corpo["resumo"]["chuva_total_anterior_mm"] is None

    @respx.mock
    def test_arquivo_incompleto_devolve_os_dias_que_existem(self):
        """Tres dias em vez de sete nao sao erro: sao a borda da reanalise."""
        _mockar(atual=ARQUIVO_INCOMPLETO)

        corpo = _buscar()

        assert corpo.status_code == 200
        assert len(corpo.json()["serie"]) == 3

    @respx.mock
    def test_um_dia_sem_uma_variavel_entra_na_serie_com_o_campo_nulo(self):
        """Descartar o dia inteiro esconderia os outros quatro valores dele."""
        _mockar(atual=ARQUIVO_INCOMPLETO)

        meio = _buscar().json()["serie"][1]

        assert meio["date"] == "2026-09-14"
        assert meio["high"] == 18.8
        assert meio["humidity"] is None


class TestUv:
    @respx.mock
    def test_o_uv_e_um_bloco_irmao_e_nao_uma_coluna_da_serie(self):
        """Um campo dentro de `serie` seria nulo em 173 dos 180 pontos."""
        _mockar()

        corpo = _buscar(janela="6m").json()

        assert "uv" not in corpo["serie"][0]
        assert set(corpo["uv"]) == {"horas", "maximo_da_semana", "nota"}

    @respx.mock
    def test_o_uv_cobre_o_dia_corrente_hora_a_hora(self):
        _mockar()

        uv = _buscar().json()["uv"]

        # So as horas do primeiro dia da previsao, nao as 168 pedidas.
        assert len(uv["horas"]) == 24
        assert all(hora["time"].startswith("2026-09-15") for hora in uv["horas"])

    @respx.mock
    def test_o_uv_traz_a_maxima_da_semana_prevista(self):
        _mockar()

        assert _buscar().json()["uv"]["maximo_da_semana"] == 3.55

    @respx.mock
    def test_o_uv_nao_acompanha_a_janela_e_o_payload_diz_por_que(self):
        """Um grafico de sete dias numa pagina de seis meses parece defeito
        ate ser explicado."""
        _mockar()

        uv = _buscar(janela="6m").json()["uv"]

        assert len(uv["horas"]) == 24
        assert uv["nota"]

    @respx.mock
    def test_uv_nulo_no_arquivo_nao_vira_uma_serie_de_nulos_no_payload(self):
        """**A armadilha medida.** A reanalise aceita `uv_index_max` e devolve
        `null` para todos os dias; plota-la daria uma linha reta no zero."""
        _mockar(atual=ARQUIVO_COM_UV_NULO, anterior=ARQUIVO_COM_UV_NULO)

        corpo = _buscar().json()

        assert corpo["uv"]["horas"]
        assert all(hora["uv"] is not None for hora in corpo["uv"]["horas"])
        assert all("uv" not in ponto for ponto in corpo["serie"])

    @respx.mock
    def test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela(self):
        """**Regressao.** As duas datas discordam e o UV segue a da cidade.

        A janela termina no dia corrente em UTC — e o calendario da reanalise —,
        mas a previsao vem com `timezone=auto` e seus timestamps sao horario de
        parede. Em Wellington (UTC+12) a cidade ja esta no dia seguinte, e
        filtrar as horas pela ponta da janela nao casava com hora nenhuma: o
        painel de UV ficava vazio na cidade inteira.
        """
        # A previsao comeca um dia depois da ponta da janela, como em Wellington.
        #
        # O dia da cidade e **derivado** de hoje, e nao carimbado: com a data
        # fixa, o teste passava a acusar o proprio calendario no dia em que hoje
        # alcancasse o literal — as duas datas coincidiam, e o cenario que ele
        # existe para exercitar (as duas discordam) deixava de ser montado. E a
        # regra que o docstring do modulo ja declara.
        dia_da_cidade = (date.today() + timedelta(days=1)).isoformat()
        adiantada = {
            **UV_BERLIM,
            "hourly": {
                "time": [f"{dia_da_cidade}T{hora:02d}:00" for hora in range(24)],
                "uv_index": [1.5] * 24,
            },
        }
        _mockar(uv=adiantada)

        corpo = _buscar().json()

        assert corpo["periodo"]["fim"] != dia_da_cidade
        assert len(corpo["uv"]["horas"]) == 24
        assert corpo["uv"]["horas"][0]["time"].startswith(dia_da_cidade)

    @respx.mock
    def test_sem_uv_previsto_o_bloco_vem_vazio_e_nao_derruba_a_pagina(self):
        sem_uv = {**UV_BERLIM, "hourly": {"time": [], "uv_index": []}, "daily": {"time": [], "uv_index_max": []}}
        _mockar(uv=sem_uv)

        corpo = _buscar()

        assert corpo.status_code == 200
        assert corpo.json()["uv"]["horas"] == []
        assert corpo.json()["uv"]["maximo_da_semana"] is None


class TestResumo:
    @respx.mock
    def test_o_resumo_traz_os_numeros_prontos(self):
        _mockar()

        resumo = _buscar().json()["resumo"]

        # 0.0 + 0.1 + 0.0 + 0.7 + 2.1 + 0.2 + 0.0
        assert resumo["chuva_total_mm"] == 3.1
        assert resumo["dias_com_chuva"] == 4
        assert resumo["umidade_minima"] == 62
        assert resumo["umidade_maxima"] == 80
        assert resumo["vento_maximo"] == 20.1

    @respx.mock
    def test_a_direcao_dominante_vem_em_graus_e_em_ponto_cardeal(self):
        """"Noroeste" se le e "312°" se calcula — o payload manda os dois."""
        _mockar()

        resumo = _buscar().json()["resumo"]

        assert resumo["direcao_dominante"] is not None
        # As direcoes da fixture giram em torno de oeste.
        assert resumo["rumo_dominante"] in {"O", "OSO", "ONO", "SO", "NO"}

    @respx.mock
    def test_a_chuva_dos_dois_periodos_vem_lado_a_lado(self):
        """Para responder "este periodo foi mais seco que o normal?"."""
        _mockar()

        resumo = _buscar().json()["resumo"]

        assert resumo["chuva_total_mm"] == 3.1
        # 4.0 + 6.1 + 0.0 + 3.7 + 8.1 + 1.2 + 0.0
        assert resumo["chuva_total_anterior_mm"] == 23.1


class TestFalhas:
    @respx.mock
    def test_api_externa_fora_do_ar_vira_503_com_mensagem_legivel(self):
        respx.get(ARCHIVE_URL).mock(side_effect=httpx.ConnectError("sem rede"))

        resposta = _buscar()

        assert resposta.status_code == 503
        assert resposta.json()["detail"]

    @respx.mock
    @pytest.mark.parametrize(
        "coordenada",
        [{"latitude": 91}, {"longitude": 181}, {"latitude": -91}],
    )
    def test_coordenada_fora_do_globo_e_422(self, coordenada):
        _mockar()

        assert _buscar(**coordenada).status_code == 422
