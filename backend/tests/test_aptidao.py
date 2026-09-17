"""As regras de aptidao: o quanto um dia serve para cada atividade.

O que se protege aqui, acima de tudo, e o **modo de falha do ADR 0011**: um
limiar absoluto calibrado so em cidade temperada marca o tropico umido como
ruim todos os dias do ano, e a pagina fica inutil em Manaus sem nunca dar erro.
O teste que guarda isso e
`test_cidade_tropical_umida_tem_dia_bom_de_lavar_roupa_no_ano`, e ele afirma
sobre uma **taxa** ao longo de um ano real — nao sobre um dia escolhido, que
passaria mesmo no cenario com o bug.

O segundo par que se protege e a **independencia entre aptidao e condicao
prevista** (verbete *Aptidao* do `CONTEXT.md`): um dia sem condicao severa
nenhuma pode ter aptidao pessima, e confundi-los faria a pagina Calendario
parecer uma segunda pagina Condicoes.
"""

import pytest

from app.services import aptidao
from app.services.aptidao import ATIVIDADES, BOA, MEDIA, RUIM
from tests.fixtures_aptidao import DIAS_DO_ANO, como_dia

#: Um dia de referencia: seco, ameno, sem vento, sem chuva. Serve de base para
#: os casos, que mudam **uma** variavel de cada vez — e o que faz o motivo da
#: reprovacao ser atribuivel aquela variavel, e nao a soma do cenario.
DIA_BOM = {
    "weather_code": 0,
    "temperature_2m_max": 24.0,
    "temperature_2m_min": 14.0,
    "precipitation_sum": 0.0,
    "wind_gusts_10m_max": 20.0,
    "relative_humidity_2m_mean": 55.0,
}


def julgar(**mudancas):
    """A aptidao de um dia igual ao `DIA_BOM`, com as mudancas aplicadas."""
    return aptidao.julgar_dia({**DIA_BOM, **mudancas})


def por_atividade(julgamentos, atividade):
    return next(j for j in julgamentos if j.atividade == atividade)


class TestAsQuatroAtividades:
    """Cada atividade julga, e julga por uma regra propria.

    Uma atividade sem regra propria seria um rotulo que nao julga nada — o
    verbete *Atividade* do `CONTEXT.md` e explicito, e por isso o teste que
    conta as quatro anda junto dos que exercitam cada uma.
    """

    def test_um_dia_produz_um_julgamento_por_atividade(self):
        julgamentos = julgar()

        assert len(julgamentos) == len(ATIVIDADES) == 4
        assert {j.atividade for j in julgamentos} == {
            "lavar_roupa",
            "esporte",
            "viagem",
            "plantio",
        }

    def test_o_dia_de_referencia_e_bom_para_as_tres_atividades_secas(self):
        """Seco, ameno e sem vento serve — a regra nao e so negativa.

        **Menos para o plantio**, e a excecao e a prova de que as quatro regras
        sao mesmo diferentes: um dia sem chuva nenhuma e apenas mediano para
        quem acabou de semear. E o caso ao lado, e nao um ajuste deste.
        """
        julgamentos = julgar()

        for atividade in ("lavar_roupa", "esporte", "viagem"):
            assert por_atividade(julgamentos, atividade).nivel == BOA

    def test_o_dia_totalmente_seco_e_apenas_mediano_para_o_plantio(self):
        """A chuva que atrapalha as outras tres faz falta a esta.

        Sem motivo: nada reprovou o dia — ele so nao atende o criterio de dia
        bom. O motivo existe para a reprovacao, e um dia medio nao tem um
        culpado unico a nomear.
        """
        julgamento = por_atividade(julgar(precipitation_sum=0.0), "plantio")

        assert julgamento.nivel == MEDIA
        assert julgamento.motivo is None


class TestLavarRoupa:
    """Chuva e umidade, que sao as duas que decidem se a roupa seca."""

    def test_aprova_dia_seco_e_de_ar_seco(self):
        assert por_atividade(julgar(), "lavar_roupa").nivel == BOA

    def test_reprova_por_chuva_e_diz_a_chuva(self):
        julgamento = por_atividade(julgar(precipitation_sum=8.0), "lavar_roupa")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo is not None
        assert julgamento.motivo.variavel == "chuva"
        assert "8" in julgamento.motivo.texto

    def test_reprova_por_umidade_e_diz_a_umidade(self):
        """**O caso que separa aptidao de condicao prevista.**

        Sem chuva, sem vento e sem tempestade: nada aqui dispara condicao
        severa alguma. A roupa nao seca assim mesmo, e e a aptidao que sabe
        dizer isso.
        """
        julgamento = por_atividade(
            julgar(relative_humidity_2m_mean=95.0), "lavar_roupa"
        )

        assert julgamento.nivel == RUIM
        assert julgamento.motivo is not None
        assert julgamento.motivo.variavel == "umidade"
        assert "95" in julgamento.motivo.texto

    def test_sem_umidade_no_payload_julga_pelo_resto(self):
        """A variavel pode faltar numa resposta parcial; o dia nao some por isso."""
        julgamento = por_atividade(
            julgar(relative_humidity_2m_mean=None), "lavar_roupa"
        )

        assert julgamento.nivel in {BOA, MEDIA}


class TestEsporte:
    def test_reprova_por_tempestade(self):
        julgamento = por_atividade(julgar(weather_code=95), "esporte")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "tempestade"

    def test_reprova_por_calor_extremo(self):
        julgamento = por_atividade(julgar(temperature_2m_max=38.0), "esporte")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "calor"
        assert "38" in julgamento.motivo.texto

    def test_reprova_por_frio_extremo(self):
        julgamento = por_atividade(julgar(temperature_2m_min=-3.0), "esporte")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "frio"

    def test_reprova_por_rajada(self):
        julgamento = por_atividade(julgar(wind_gusts_10m_max=70.0), "esporte")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "vento"


class TestViagem:
    def test_reprova_por_chuva_forte(self):
        julgamento = por_atividade(julgar(precipitation_sum=20.0), "viagem")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "chuva"

    def test_reprova_por_neve(self):
        """Neve atrapalha deslocamento mesmo em volume que nao e chuva forte."""
        julgamento = por_atividade(
            julgar(weather_code=75, precipitation_sum=1.0), "viagem"
        )

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "neve"

    def test_chuva_fraca_nao_reprova_viagem_mas_reprovaria_roupa(self):
        """As regras sao proprias de cada atividade, e nao um score compartilhado."""
        julgamentos = julgar(precipitation_sum=4.0)

        assert por_atividade(julgamentos, "viagem").nivel != RUIM
        assert por_atividade(julgamentos, "lavar_roupa").nivel == RUIM


class TestPlantio:
    def test_chuva_fraca_e_boa_para_plantio(self):
        """A chuva que atrapalha as outras tres **ajuda** esta."""
        assert por_atividade(julgar(precipitation_sum=5.0), "plantio").nivel == BOA

    def test_reprova_por_geada(self):
        julgamento = por_atividade(julgar(temperature_2m_min=0.0), "plantio")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "frio"

    def test_reprova_por_chuva_excessiva(self):
        julgamento = por_atividade(julgar(precipitation_sum=30.0), "plantio")

        assert julgamento.nivel == RUIM
        assert julgamento.motivo.variavel == "chuva"


class TestAptidaoNaoEeMesmoQueCondicaoPrevista:
    """Os dois conceitos sao independentes, e o `CONTEXT.md` os separa."""

    def test_dia_sem_condicao_severa_pode_ter_aptidao_pessima(self):
        """Nada aqui dispara `condicoes.py`: sem tempestade, chuva de 1 mm
        (o limiar de la e 20) e rajada de 20 km/h (o limiar de la e 60).

        E mesmo assim a roupa nao seca a 95% de umidade.
        """
        julgamentos = julgar(relative_humidity_2m_mean=95.0, precipitation_sum=1.0)

        assert por_atividade(julgamentos, "lavar_roupa").nivel == RUIM

    def test_dia_de_tempestade_reprova_as_atividades_ao_ar_livre(self):
        julgamentos = julgar(weather_code=95)

        for atividade in ("esporte", "viagem", "plantio", "lavar_roupa"):
            assert por_atividade(julgamentos, atividade).nivel == RUIM


class TestOsLimiaresSaoAbsolutos:
    """ADR 0011: a mesma entrada meteorologica produz a mesma aptidao em
    qualquer cidade. Nao ha referencia climatologica na conta."""

    def test_a_mesma_entrada_produz_a_mesma_aptidao(self):
        """`julgar_dia` recebe so o dia — nao ha por onde uma cidade entrar.

        O teste e quase tautologico de proposito: e a tautologia que se quer
        preservar. No dia em que alguem acrescentar um parametro de cidade
        aqui, e este caso que deixa de compilar.
        """
        dia = {**DIA_BOM, "relative_humidity_2m_mean": 85.0, "precipitation_sum": 2.0}

        assert aptidao.julgar_dia(dia) == aptidao.julgar_dia(dict(dia))


class TestCalibracaoDoTropicoUmido:
    """**O teste que guarda o modo de falha do ADR 0011.**

    Se alguem apertar o limiar de umidade achando que 78% e generoso demais,
    e aqui que a consequencia aparece — e nao numa reclamacao de que a pagina
    e inutil em Manaus.
    """

    @pytest.mark.parametrize("cidade", ["Manaus", "Belem"])
    def test_cidade_tropical_umida_tem_dia_bom_de_lavar_roupa_no_ano(self, cidade):
        """**Nenhuma cidade pode reprovar em todos os dias do ano.**

        A afirmacao e sobre uma **taxa**, e nao sobre um dia escolhido: com
        quatro dias secos a dedo, este teste passaria mesmo que a cidade
        tivesse exatamente aqueles quatro dias bons no ano — que e o proprio
        bug que o ADR 0011 descreve.

        O piso e deliberadamente baixo. Medido na calibracao, Manaus tem 21%
        dos dias do ano bons para lavar roupa e Belem 9%; exigir aqui os 9%
        exatos faria o teste quebrar a cada reajuste legitimo de limiar. O que
        ele guarda e a fronteira entre **poucos** e **nenhum**, que e onde mora
        a diferenca entre o fato e o defeito.
        """
        dias = [como_dia(linha) for linha in DIAS_DO_ANO[cidade]]

        bons = [
            dia
            for dia in dias
            if por_atividade(aptidao.julgar_dia(dia), "lavar_roupa").nivel == BOA
        ]

        assert len(bons) >= 2, (
            f"{cidade} ficou com {len(bons)} dias bons de lavar roupa em "
            f"{len(dias)} do ano — o modo de falha do ADR 0011"
        )

    def test_a_cidade_temperada_continua_tendo_muito_mais_dias_bons(self):
        """A contraprova: sem ela, um modulo que aprovasse tudo passaria acima.

        Sorocaba tem 53% dos dias do ano bons para lavar roupa contra os 9% de
        Belem, e e essa distancia que mostra que o limiar **julga** em vez de
        so deixar passar. Tolerante nao e permissivo.
        """
        def bons(cidade: str) -> int:
            return sum(
                1
                for linha in DIAS_DO_ANO[cidade]
                if por_atividade(
                    aptidao.julgar_dia(como_dia(linha)), "lavar_roupa"
                ).nivel
                == BOA
            )

        assert bons("Sorocaba") > bons("Belem")

    def test_a_umidade_tipica_do_tropico_nao_reprova_sozinha(self):
        """84% e a mediana de Manaus no ano: nao pode ser reprovacao.

        E o numero exato do ADR 0011 — "umidade relativa media em torno de
        80%" —, e o limiar de reprovacao mora acima dele de proposito.
        """
        julgamento = por_atividade(
            julgar(relative_humidity_2m_mean=84.0), "lavar_roupa"
        )

        assert julgamento.nivel != RUIM
