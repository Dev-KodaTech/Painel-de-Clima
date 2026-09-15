"""Os agregados do historico: o que e regra nossa, testado direto.

O caso obrigatorio e a media circular da direcao do vento. Ele nao aparece num
teste de costura porque o numero errado — 180° em vez de 0° — e plausivel: um
vento de sul e tao possivel quanto um de norte, e so quem conhece a entrada
percebe a troca.
"""

from datetime import date

import pytest

from app.models import DiaDoHistorico
from app.services import historico, resumo


def dia(**campos) -> DiaDoHistorico:
    """Um dia do historico com so os campos que o teste usa."""
    return DiaDoHistorico(date=campos.pop("date", "2026-09-14"), **campos)


class TestDirecaoDominante:
    def test_a_media_de_350_e_10_graus_e_norte_e_nao_sul(self):
        """**O caso que obriga a media vetorial.**

        A media aritmetica daria 180° — sul, o rumo exatamente oposto ao
        correto — e ninguem notaria: sul e um vento plausivel.
        """
        graus = resumo.direcao_dominante([350.0, 10.0])

        assert graus is not None
        assert resumo.rumo(graus) == "N"

    def test_direcoes_iguais_devolvem_a_propria_direcao(self):
        assert resumo.direcao_dominante([90.0, 90.0, 90.0]) == 90.0

    def test_sem_direcao_alguma_nao_ha_dominante(self):
        assert resumo.direcao_dominante([]) is None

    def test_direcoes_que_se_cancelam_nao_tem_dominante(self):
        """Norte e sul em igual medida nao apontam para lugar nenhum.

        `atan2(0, 0)` devolveria 0° — norte —, inventando uma direcao que o
        dado nao tem.
        """
        assert resumo.direcao_dominante([0.0, 180.0]) is None


class TestRumo:
    def test_os_quatro_cardeais(self):
        assert resumo.rumo(0) == "N"
        assert resumo.rumo(90) == "E"
        assert resumo.rumo(180) == "S"
        assert resumo.rumo(270) == "O"

    def test_o_rumo_e_circular_nas_pontas(self):
        """359° e norte, nao o ultimo item da lista."""
        assert resumo.rumo(359) == "N"

    def test_noroeste_se_le_onde_312_graus_se_calcula(self):
        assert resumo.rumo(312) == "NO"


class TestChuva:
    def test_a_chuva_da_janela_e_acumulada(self):
        serie = [
            dia(date="2026-09-12", precipitation_mm=0.6),
            dia(date="2026-09-13", precipitation_mm=2.1),
            dia(date="2026-09-14", precipitation_mm=0.0),
        ]

        assert resumo.montar(serie, []).chuva_total_mm == 2.7

    def test_dias_com_chuva_conta_dias_e_nao_milimetros(self):
        """60 mm em tres dias e 60 mm em vinte sao periodos diferentes."""
        serie = [
            dia(date="2026-09-12", precipitation_mm=20.0),
            dia(date="2026-09-13", precipitation_mm=0.0),
            dia(date="2026-09-14", precipitation_mm=40.0),
        ]

        assert resumo.montar(serie, []).dias_com_chuva == 2

    def test_um_traco_de_chuva_nao_conta_como_dia_de_chuva(self):
        """0,05 mm nao molhou ninguem, e conta-lo faria um mes seco parecer chuvoso."""
        serie = [dia(precipitation_mm=0.05)]

        assert resumo.montar(serie, []).dias_com_chuva == 0

    def test_a_chuva_do_ano_anterior_vem_ao_lado(self):
        atual = [dia(date="2026-09-14", precipitation_mm=5.0)]
        anterior = [dia(date="2025-09-14", precipitation_mm=30.0)]

        resultado = resumo.montar(atual, anterior)

        assert resultado.chuva_total_mm == 5.0
        assert resultado.chuva_total_anterior_mm == 30.0


class TestUmidade:
    def test_a_amplitude_acompanha_a_media(self):
        """Minima e maxima existem porque a media sozinha esconde a amplitude."""
        serie = [dia(humidity=62.0), dia(humidity=80.0), dia(humidity=71.0)]

        resultado = resumo.montar(serie, [])

        assert resultado.umidade_minima == 62.0
        assert resultado.umidade_maxima == 80.0
        assert resultado.umidade_media == 71.0


class TestTemperatura:
    def test_a_diferenca_media_compara_os_dois_periodos(self):
        atual = [dia(date="2026-09-14", high=22.0, low=12.0)]
        anterior = [dia(date="2025-09-14", high=20.0, low=10.0)]

        assert resumo.montar(atual, anterior).diferenca_media == 2.0

    def test_sem_ano_anterior_nao_ha_diferenca(self):
        """`None`, e nao zero: zero diria "os dois periodos foram iguais"."""
        resultado = resumo.montar([dia(high=22.0, low=12.0)], [])

        assert resultado.temperatura_media == 17.0
        assert resultado.diferenca_media is None


class TestJanelaSemDado:
    def test_uma_janela_vazia_nao_inventa_zeros(self):
        """Media de lista vazia seria `0`, que se le como "fez zero grau"."""
        resultado = resumo.montar([], [])

        assert resultado.chuva_total_mm is None
        assert resultado.umidade_media is None
        assert resultado.vento_maximo is None
        assert resultado.rumo_dominante is None
        assert resultado.dias_com_chuva == 0

    def test_um_dia_sem_uma_variavel_nao_descarta_as_outras(self):
        """O arquivo tem buracos nas bordas: falta uma coluna, nao o dia."""
        serie = [
            dia(date="2026-09-13", high=20.0, low=10.0, humidity=None),
            dia(date="2026-09-14", high=22.0, low=12.0, humidity=70.0),
        ]

        resultado = resumo.montar(serie, [])

        assert resultado.temperatura_media == 16.0
        assert resultado.umidade_media == 70.0


class TestPeriodo:
    """A resolucao da janela em datas. Pura, e por isso testada direto:
    exercitar um 29 de fevereiro pela costura HTTP exigiria viajar no tempo."""

    @pytest.mark.parametrize("janela", ["7d", "30d", "6m"])
    @pytest.mark.parametrize(
        "hoje",
        [
            date(2026, 9, 15),
            # Os casos bissextos: a janela termina no 29, e a janela que
            # **atravessa** um 29 de fevereiro sem terminar nele.
            date(2028, 2, 29),
            date(2028, 3, 1),
            date(2028, 8, 28),
            date(2027, 3, 1),
        ],
    )
    def test_as_duas_janelas_sempre_tem_o_mesmo_comprimento(self, janela, hoje):
        """**O invariante de que a comparacao depende.**

        Recuar as duas pontas em separado parece equivalente e nao e: quando a
        janela atravessa um 29 de fevereiro, um ano atras tem um dia a menos. A
        comparacao entre 183 e 182 dias deixa de casar dia a dia, e os
        acumulados passam a somar quantidades diferentes de dias.
        """
        periodo = historico.resolver_periodo(janela, hoje)

        atual = date.fromisoformat(periodo.fim) - date.fromisoformat(periodo.inicio)
        anterior = date.fromisoformat(periodo.fim_anterior) - date.fromisoformat(
            periodo.inicio_anterior
        )

        assert atual == anterior
        assert atual.days + 1 == historico.DIAS_DA_JANELA[janela]

    def test_a_janela_do_ano_anterior_usa_a_mesma_data_de_calendario(self):
        periodo = historico.resolver_periodo("30d", date(2026, 9, 15))

        assert periodo.fim == "2026-09-15"
        assert periodo.fim_anterior == "2025-09-15"

    def test_29_de_fevereiro_recua_para_28(self):
        """O ano anterior nao tem 29; 28 preserva "fim de fevereiro"."""
        periodo = historico.resolver_periodo("7d", date(2028, 2, 29))

        assert periodo.fim_anterior == "2027-02-28"
