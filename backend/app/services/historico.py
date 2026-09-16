"""Monta o historico climatologico: resolve a janela em datas e casa as series.

Quatro fatos deste modulo, todos medidos contra o servico real e nao supostos:

1. O arquivo cobre ate o dia corrente — nao ha vao entre ele e a previsao, e a
   janela atual sai dele inteira.
2. `uv_index_max` no arquivo devolve `null` sempre. O UV vem da previsao, num
   bloco irmao.
3. Umidade, vento e direcao existem no arquivo com valores reais.
4. Seis meses custam ~7 KB por chamada, entao duas chamadas sao baratas — nao
   se repete aqui o dilema de banda que levou o painel a dividir a sua.
"""

from datetime import date, timedelta

import httpx

from app.models import (
    UNIDADES_DO_HISTORICO,
    DiaDoHistorico,
    Janela,
    Periodo,
    PontoDeUv,
    TrendsResponse,
    UnitsDoHistorico,
    Uv,
    atribuicao,
)
from app.services import open_meteo, resumo

#: Quantos dias cada janela cobre.
#:
#: Seis meses sao 183 dias e nao "seis meses de calendario": a diferenca e de um
#: ou dois dias, e um numero fixo de dias mantem a janela do ano anterior com
#: **exatamente o mesmo comprimento** que a atual, que e o que torna as duas
#: series comparaveis ponto a ponto.
DIAS_DA_JANELA: dict[Janela, int] = {"7d": 7, "30d": 30, "6m": 183}

#: O texto que acompanha o grafico de UV. Existe porque um grafico de sete dias
#: numa pagina cuja janela e de seis meses parece defeito ate ser explicado.
NOTA_DO_UV = (
    "O indice UV so existe na previsao: a reanalise do passado nao o mede. "
    "Por isso ele nao acompanha a janela nem entra na comparacao com o ano "
    "anterior."
)


def resolver_periodo(janela: Janela, hoje: date) -> Periodo:
    """As quatro datas da pagina: as duas pontas de cada janela.

    A janela **termina hoje**: o arquivo cobre o dia corrente, e cortar em
    ontem descartaria um dia de dado que existe.

    A janela do ano anterior usa a **mesma data de calendario**, nao o mesmo dia
    da semana: a pergunta e "setembro esta fora do normal?", e alinhar por dia
    da semana compararia setembro com uma janela deslocada em ate tres dias.
    Isso vale igual nos dois hemisferios — "mesmo periodo do ano anterior" nao
    depende de estacao.
    """
    dias = DIAS_DA_JANELA[janela]
    # `dias - 1`: uma janela de sete dias que termina hoje comeca ha seis dias,
    # e inclui as duas pontas.
    inicio = hoje - timedelta(days=dias - 1)

    # **A ponta do ano anterior e deslocada, e o inicio derivado dela.**
    #
    # Recuar as duas pontas em separado parece equivalente e nao e: quando a
    # janela atravessa um 29 de fevereiro, um ano atras tem um dia a menos, e as
    # duas janelas saem com comprimentos diferentes. Uma comparacao entre 183 e
    # 182 dias deixa de casar dia a dia, e os acumulados passam a somar
    # quantidades distintas de dias.
    #
    # Derivar o inicio do fim com o **mesmo** `dias - 1` garante o invariante de
    # que as duas janelas tem o mesmo comprimento, que e do que a comparacao
    # depende.
    fim_anterior = _um_ano_antes(hoje)

    return Periodo(
        janela=janela,
        inicio=inicio.isoformat(),
        fim=hoje.isoformat(),
        inicio_anterior=(fim_anterior - timedelta(days=dias - 1)).isoformat(),
        fim_anterior=fim_anterior.isoformat(),
    )


def _um_ano_antes(dia: date) -> date:
    """A mesma data do calendario, um ano atras.

    29 de fevereiro nao existe no ano anterior e `replace` levantaria; 28 e a
    aproximacao que preserva "fim de fevereiro", que e o que a comparacao quer
    dizer.
    """
    try:
        return dia.replace(year=dia.year - 1)
    except ValueError:
        return dia.replace(year=dia.year - 1, day=28)


def _serie(arquivo: dict) -> list[DiaDoHistorico]:
    """Os dias do arquivo, um `DiaDoHistorico` cada.

    O bloco `daily` vem como colunas paralelas — uma lista por variavel, todas
    do mesmo comprimento que `time`. Um dia sem medicao vem como `null` **na
    coluna**, e nao como dia ausente: por isso o dia entra na serie de qualquer
    forma, com o campo nulo, em vez de ser descartado inteiro. Um arquivo
    incompleto rende os dias que existem, nunca um erro.

    Uma coluna pode faltar por inteiro numa resposta parcial; `.get` a trata
    como ausente em vez de levantar `KeyError` no meio de um payload util.
    """
    daily = arquivo.get("daily") or {}
    datas = daily.get("time") or []

    def coluna(nome: str) -> list:
        """A coluna, esticada com nulos se vier mais curta que `time`."""
        valores = daily.get(nome) or []
        return valores + [None] * (len(datas) - len(valores))

    colunas = {
        "high": coluna("temperature_2m_max"),
        "low": coluna("temperature_2m_min"),
        "precipitation_mm": coluna("precipitation_sum"),
        "humidity": coluna("relative_humidity_2m_mean"),
        "wind_speed": coluna("wind_speed_10m_max"),
        "wind_direction": coluna("wind_direction_10m_dominant"),
    }

    return [
        DiaDoHistorico(
            date=data,
            **{campo: valores[indice] for campo, valores in colunas.items()},
        )
        for indice, data in enumerate(datas)
    ]


def _uv(previsao: dict) -> Uv:
    """O UV do dia corrente hora a hora, mais a maxima dos sete dias.

    O recorte e **por data**, como o da tendencia horaria do painel: pedir sete
    dias traz 168 horas e o grafico mostra o dia inteiro, de 00:00 a 23:00.

    **A data vem da propria previsao**, e nao da ponta da janela. As duas
    discordam: a janela termina no dia corrente em UTC, porque e nesse
    calendario que a reanalise e publicada, enquanto a previsao vem com
    `timezone=auto` e seus timestamps sao horario de parede da cidade. Em
    Wellington (UTC+12) a primeira ja e dia 15 e a segunda ja esta no dia 16, e
    filtrar uma pela outra nao casava com hora nenhuma — o painel de UV ficava
    vazio na cidade inteira. Medido.

    Este e o unico lugar da pagina onde a data da cidade manda, e e o certo: o
    UV e o unico bloco que nao vem do arquivo.

    Nulos sao descartados aqui e nao repassados: o grafico nao tem o que
    desenhar num ponto sem valor, e uma lista com buracos faria cada consumidor
    decidir de novo o que fazer com eles.
    """
    horario = previsao.get("hourly") or {}
    tempos = horario.get("time") or []
    # O primeiro timestamp da previsao e o dia corrente **na cidade**, que e o
    # dia que o grafico mostra.
    hoje = tempos[0][:10] if tempos else ""

    horas = [
        PontoDeUv(time=time, uv=valor)
        for time, valor in zip(tempos, horario.get("uv_index") or [])
        if valor is not None and time.startswith(hoje)
    ]

    diario = previsao.get("daily") or {}
    maximos = [valor for valor in (diario.get("uv_index_max") or []) if valor is not None]

    return Uv(
        horas=horas,
        maximo_da_semana=max(maximos) if maximos else None,
        nota=NOTA_DO_UV,
    )


async def montar(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    janela: Janela,
    hoje: date,
) -> TrendsResponse:
    """O historico climatologico de uma coordenada, para uma janela.

    Tres chamadas externas: a janela atual, a mesma janela do ano anterior e o
    UV previsto. A primeira e a terceira usam o TTL curto; a do ano anterior, o
    longo — o passado nao muda.
    """
    periodo = resolver_periodo(janela, hoje)

    atual = await open_meteo.buscar_arquivo(
        client, latitude, longitude, periodo.inicio, periodo.fim, passado=False
    )
    anterior = await open_meteo.buscar_arquivo(
        client,
        latitude,
        longitude,
        periodo.inicio_anterior,
        periodo.fim_anterior,
        passado=True,
    )
    previsao_uv = await open_meteo.buscar_uv(client, latitude, longitude)

    serie = _serie(atual)
    comparacao = _serie(anterior)

    return TrendsResponse(
        periodo=periodo,
        serie=serie,
        comparacao=comparacao,
        uv=_uv(previsao_uv),
        resumo=resumo.montar(serie, comparacao),
        units=UnitsDoHistorico(**UNIDADES_DO_HISTORICO),
        attribution=atribuicao(),
    )
