"""Deriva as condicoes severas previstas a partir do bloco diario.

A Open-Meteo **nao tem alertas meteorologicos** — confirmado por tres vias, e
o mantenedor declara nao haver plano. Um segundo provedor exigiria chave de
API, contra a restricao do projeto. Entao os avisos sao derivados da propria
previsao, e o vocabulario os separa dos oficiais: aqui sao *condicoes
previstas*, nunca *alertas*.

Os limiares sao **absolutos**, nao relativos ao clima da cidade. O relativo
foi testado e rejeitado por ser perigoso: com 1,5x a mediana da semana,
Wellington (mediana de rajada 76 km/h) trata 86 km/h como normal e nao emite
aviso nenhum numa semana de rajadas de 86. Perigo e absoluto — 86 km/h derruba
galho em Wellington igual a Cairo.

**O `services/aptidao.py` tambem usa limiares absolutos, e o motivo dele nao e
este.** Os dois arquivos tem constantes de limiar no topo com comentario de
calibracao, e a semelhanca e superficial: la se julga se o tempo *serve para
uma intencao*, e nao se ele e perigoso — nao ha nada de absoluto em "bom dia
para secar roupa" da forma como ha em "vento que derruba galho". O argumento
daqui **nao transfere para la**, e o
`docs/adr/0011-aptidao-e-absoluta-pelo-motivo-oposto.md` registra a diferenca
justamente para que quem mexer num dos dois nao aplique o raciocinio do outro.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from app.models import CondicaoPrevista
from app.services.wmo import CODIGOS_TEMPESTADE

#: Rajada maxima do dia, em km/h. Calibrado sobre 42 dias-cidade: >=40 marca
#: 26% dos dias e >=50 marca 21% (ruidoso demais); >=80 perde eventos reais.
#: >=60 marca 14%.
LIMIAR_VENTO_KMH = 60.0

#: Precipitacao acumulada do dia, em mm. Na mesma amostra, >=10 mm marca 14%
#: dos dias e >=20 mm marca 4%.
LIMIAR_CHUVA_MM = 20.0

#: Os codigos de tempestade vem de `wmo.py`, que e onde a tabela mora.
#:
#: **Nao sao um limiar calibrado, ao contrario dos dois acima**: quais codigos
#: significam trovoada e fato externo, e nao decisao deste modulo. Por isso sao
#: compartilhados com o `aptidao.py`, enquanto os limiares de vento e de chuva
#: continuam calibrados aqui, para o que este modulo julga. Nao ha metrica a
#: comparar — o codigo e o gatilho.

#: Quantos cards o painel comporta. Com o dedup por categoria, nenhuma das seis
#: cidades da amostra passou de dois; o limite existe para a semana que passar.
MAXIMO_DE_CARDS = 2


@dataclass(frozen=True)
class _Categoria:
    """Uma das tres condicoes que o painel sabe exibir.

    Duas formas de disparo, nao tres regras soltas: ou o dia cruza um `limiar`
    numa metrica (vento, chuva), ou o `weather_code` do dia esta em `codigos`
    (tempestade). Tempestade nao tem metrica a comparar — o codigo *e* o
    gatilho —, e por isso `campo` e `limiar` sao nulos nela, em vez de uma
    funcao que devolve `None` para satisfazer um contrato que nao a serve.
    """

    kind: str
    label: str
    icon: str
    detalhe: Callable[[float | None], str]
    #: O campo do bloco diario que decide o disparo, ou `None` quando a
    #: categoria e disparada por codigo.
    campo: str | None = None
    limiar: float | None = None
    #: Os codigos WMO que disparam, quando nao ha metrica.
    codigos: frozenset[int] = frozenset()

    def valor(self, daily: dict, indice: int) -> float | None:
        """O valor da metrica do dia, ou `None` quando nao ha metrica a ler.

        O campo pode faltar do bloco diario — `wind_gusts_10m_max` e uma
        variavel a mais pedida a API externa, e uma resposta parcial nao a
        traria —, e a API devolve `null` para um dia sem dado. Ambos os casos
        viram `None`, e `None` nunca dispara: um aviso de vento sem valor nao
        diria nada.
        """
        if self.campo is None:
            return None
        valores = daily.get(self.campo)
        if not valores or indice >= len(valores):
            return None
        return valores[indice]

    def dispara(self, daily: dict, indice: int) -> bool:
        if self.limiar is None:
            return daily["weather_code"][indice] in self.codigos
        valor = self.valor(daily, indice)
        return valor is not None and valor >= self.limiar


CATEGORIAS = (
    _Categoria(
        kind="storm",
        label="Tempestade",
        icon="thunderstorms",
        codigos=CODIGOS_TEMPESTADE,
        detalhe=lambda valor: "Tempestade com raios prevista",
    ),
    _Categoria(
        kind="wind",
        label="Vento forte",
        icon="wind",
        campo="wind_gusts_10m_max",
        limiar=LIMIAR_VENTO_KMH,
        detalhe=lambda valor: f"Rajadas de {valor:.0f} km/h",
    ),
    _Categoria(
        kind="rain",
        label="Chuva intensa",
        icon="rain",
        campo="precipitation_sum",
        limiar=LIMIAR_CHUVA_MM,
        detalhe=lambda valor: f"{valor:.1f} mm previstos".replace(".", ","),
    ),
)


def _dias_que_disparam(categoria: _Categoria, daily: dict) -> list[int]:
    return [
        indice
        for indice in range(len(daily["time"]))
        if categoria.dispara(daily, indice)
    ]


def _pior_dia(categoria: _Categoria, daily: dict, indices: Iterable[int]) -> int:
    """O dia que o card representa.

    Para vento e chuva e o de maior valor — e o que a pessoa precisa saber. Para
    tempestade, que nao tem metrica, e o mais proximo: um empate entre dias
    igualmente severos se resolve pelo que chega antes.
    """
    return max(
        indices,
        key=lambda indice: (categoria.valor(daily, indice) or 0, -indice),
    )


def _card(categoria: _Categoria, daily: dict, indices: list[int]) -> CondicaoPrevista:
    indice = _pior_dia(categoria, daily, indices)
    return CondicaoPrevista(
        kind=categoria.kind,
        date=daily["time"][indice],
        label=categoria.label,
        icon=categoria.icon,
        detail=categoria.detalhe(categoria.valor(daily, indice)),
        # Os demais dias da categoria viram uma linha no card, nao cards seus.
        also_days=len(indices) - 1,
    )


def derivar(daily: dict) -> list[CondicaoPrevista]:
    """As condicoes severas de uma semana: no maximo um card por categoria.

    **O dedup por categoria e a parte essencial**, nao um refinamento. Sem ele,
    Wellington dispara cinco dos sete dias com o mesmo aviso de vento, e cinco
    cards identicos sao ruido. Com ele, as seis cidades da amostra ficam entre
    zero e dois cards — exatamente o que o layout comporta.
    """
    cards = []
    for categoria in CATEGORIAS:
        indices = _dias_que_disparam(categoria, daily)
        if indices:
            cards.append(_card(categoria, daily, indices))

    # Por data: o painel conta a semana na ordem em que ela chega. O corte vem
    # depois da ordenacao, entao os dois exibidos sao os mais **proximos**, e
    # nao os mais severos — numa semana em que as tres categorias disparam, a
    # terceira some mesmo que seja a pior. E o que a spec pede ("ordenados por
    # data, no maximo dois exibidos") e ha um nivel de severidade so, sem o que
    # ordenar por gravidade; com o dedup, nenhuma das seis cidades da amostra
    # chegou a tres categorias.
    cards.sort(key=lambda card: card.date)
    return cards[:MAXIMO_DE_CARDS]


def _item_do_dia(categoria: _Categoria, daily: dict, indice: int) -> CondicaoPrevista:
    return CondicaoPrevista(
        kind=categoria.kind,
        date=daily["time"][indice],
        label=categoria.label,
        icon=categoria.icon,
        detail=categoria.detalhe(categoria.valor(daily, indice)),
        # A pagina mostra um item por dia — nao ha outros dias a contar aqui,
        # ao contrario do card do painel.
        also_days=0,
    )


def derivar_por_dia(daily: dict) -> list[CondicaoPrevista]:
    """As condicoes severas de uma semana: **um item por dia que dispara**.

    O contrario do dedup de `derivar()`. La, `also_days` admite que o dado por
    dia existe e o descarta, para caber em dois cards de altura fixa. Aqui nao
    ha layout a proteger: a pagina Condicoes quer a semana de Wellington como
    cinco itens de vento com data e rajada de cada um, nao um card dizendo
    "(+4 dias)".

    Sem teto de quantidade e sem dedup por categoria — um dia que dispara duas
    categorias produz dois itens. Os limiares sao os mesmos de `derivar()`,
    porque um segundo conjunto de constantes faria o mesmo dia ser severo numa
    pagina e calmo na outra.
    """
    itens = [
        _item_do_dia(categoria, daily, indice)
        for categoria in CATEGORIAS
        for indice in _dias_que_disparam(categoria, daily)
    ]
    itens.sort(key=lambda item: item.date)
    return itens
