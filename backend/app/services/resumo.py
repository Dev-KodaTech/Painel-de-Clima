"""Os agregados do historico climatologico. Puro: sem rede, sem cache.

Existe separado do modulo que busca porque e **regra nossa**, nao repasse de
dado — o mesmo criterio que deu modulo proprio a `alertas` e `vizinhas`. Media,
acumulado e contagem sobre ate 180 pontos sao a mesma operacao para qualquer
cliente, e calcula-las aqui impede que a pagina reimplemente estatistica.

O caso que obriga este modulo a existir e a **direcao do vento**, que nao se
promedia como numero: ver `direcao_dominante`.
"""

import math

from app.models import DiaDoHistorico, ResumoDoHistorico

#: Os 16 rumos, na ordem em que os graus os percorrem a partir do norte.
#:
#: Dezesseis e nao oito: "NNO" e "NO" apontam para lugares perceptivelmente
#: diferentes, e a resolucao existe no dado (a API devolve o grau inteiro).
RUMOS = (
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO",
)

#: Quantos graus cabem em cada rumo: 360 / 16.
GRAUS_POR_RUMO = 360 / len(RUMOS)

#: A partir de quanto um dia conta como "dia com chuva", em mm.
#:
#: Nao e zero: o arquivo devolve tracos de 0,05 mm que nao molharam ninguem, e
#: conta-los faria "choveu em 20 dos 30 dias" num mes que a pessoa lembra como
#: seco. Um decimo de milimetro e o menor valor que a propria fonte distingue.
LIMIAR_DIA_COM_CHUVA_MM = 0.1


def rumo(graus: float) -> str:
    """O ponto cardeal de uma direcao em graus.

    O arredondamento e circular: 350° e 10° caem ambos em "N", e nao em rumos
    opostos das pontas da lista.
    """
    return RUMOS[round(graus / GRAUS_POR_RUMO) % len(RUMOS)]


def direcao_dominante(direcoes: list[float]) -> float | None:
    """A direcao media de uma lista de rumos, em graus de 0 a 360.

    **Media vetorial, nao aritmetica.** Direcao e um angulo, e a media
    aritmetica de 350° e 10° e 180° — o rumo exatamente *oposto* ao correto, e
    um numero plausivel o bastante para ninguem notar. Somar os vetores
    unitarios e tirar o angulo da soma da 0°, que e a resposta.

    `None` quando nao ha direcao alguma, e tambem quando os vetores se cancelam
    (ventos igualmente distribuidos por todos os rumos): ali nao ha direcao
    dominante, e devolver um angulo qualquer inventaria uma que o dado nao tem.
    """
    if not direcoes:
        return None

    seno = sum(math.sin(math.radians(grau)) for grau in direcoes)
    cosseno = sum(math.cos(math.radians(grau)) for grau in direcoes)

    # Vetores que se cancelam: `atan2(0, 0)` devolveria 0° — norte — para um
    # vento que nao tem norte algum.
    if math.isclose(seno, 0, abs_tol=1e-9) and math.isclose(cosseno, 0, abs_tol=1e-9):
        return None

    return math.degrees(math.atan2(seno, cosseno)) % 360


def _valores(dias: list[DiaDoHistorico], campo: str) -> list[float]:
    """Os valores nao nulos de um campo. O arquivo tem buracos nas bordas."""
    return [
        valor
        for dia in dias
        if (valor := getattr(dia, campo)) is not None
    ]


def _media(valores: list[float]) -> float | None:
    """A media, ou `None` para lista vazia — nunca `0`, que se leria como zero grau."""
    return sum(valores) / len(valores) if valores else None


def _arredondar(valor: float | None, casas: int) -> float | None:
    return None if valor is None else round(valor, casas)


def _temperatura_media(dias: list[DiaDoHistorico]) -> float | None:
    """A media do periodo: a media das medias diarias de maxima e minima.

    E a media do *dia*, nao das maximas: comparar as maximas de dois anos
    responderia "os picos foram maiores", que e outra pergunta.
    """
    medias = [
        (dia.high + dia.low) / 2
        for dia in dias
        if dia.high is not None and dia.low is not None
    ]
    return _media(medias)


def montar(
    serie: list[DiaDoHistorico], comparacao: list[DiaDoHistorico]
) -> ResumoDoHistorico:
    """Os numeros de resumo das duas janelas.

    `comparacao` vazia e caminho normal — o arquivo nao cobre o ano anterior —,
    e o que dela deriva sai `None` em vez de zero.
    """
    chuva = _valores(serie, "precipitation_mm")
    chuva_anterior = _valores(comparacao, "precipitation_mm")
    umidade = _valores(serie, "humidity")
    ventos = _valores(serie, "wind_speed")
    direcoes = _valores(serie, "wind_direction")

    media_atual = _temperatura_media(serie)
    media_anterior = _temperatura_media(comparacao)

    graus = direcao_dominante(direcoes)

    return ResumoDoHistorico(
        # Uma casa: a fonte serve a chuva em decimos de mm, e somar 180 delas
        # em ponto flutuante rende caudas como 60.30000000000001.
        chuva_total_mm=round(sum(chuva), 1) if chuva else None,
        chuva_total_anterior_mm=(
            round(sum(chuva_anterior), 1) if chuva_anterior else None
        ),
        dias_com_chuva=sum(1 for mm in chuva if mm >= LIMIAR_DIA_COM_CHUVA_MM),
        umidade_minima=min(umidade) if umidade else None,
        umidade_media=_arredondar(_media(umidade), 1),
        umidade_maxima=max(umidade) if umidade else None,
        vento_maximo=max(ventos) if ventos else None,
        direcao_dominante=_arredondar(graus, 1),
        rumo_dominante=None if graus is None else rumo(graus),
        temperatura_media=_arredondar(media_atual, 1),
        temperatura_media_anterior=_arredondar(media_anterior, 1),
        # `None`, e nao zero, quando falta um dos dois: zero significaria "os
        # dois periodos foram iguais", que e uma conclusao, nao uma ausencia.
        diferenca_media=(
            None
            if media_atual is None or media_anterior is None
            else round(media_atual - media_anterior, 1)
        ),
    )
