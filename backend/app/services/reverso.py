"""Reverse geocoding: uma coordenada em cidade, sobre o dataset local.

A API externa **nao tem reverse geocoding** — `/v1/reverse` devolve 404 e
`/v1/search` exige `name`. Mas o `cities15000` ja esta carregado para a tabela
de vizinhas, e a mesma busca haversine da a cidade mais proxima de uma
coordenada: nenhum download, dependencia ou requisicao a mais.

Mora separado de `vizinhas` porque a pergunta e outra. Vizinhas seleciona um
*conjunto* por relevancia, com aneis, populacao e separacao minima; aqui a
resposta e uma so, decidida por distancia pura, e nao ha o que ponderar.
"""

from app.services.geonames import CidadeLocal
from app.services.vizinhas import distancia_km

#: Acima disto, **nada** e sugerido.
#:
#: Medido em 12 coordenadas de densidade oposta, ha um corte natural e nenhum
#: meio-termo: toda area povoada acerta abaixo de 5 km (Berlim 0,0; Toquio 0,1;
#: Londres 2,2; Fairbanks 4,3) e o caso seguinte ja salta para 95 km
#: (Amazonia), depois 149 (Atacama), 341 (interior da Australia) e 1.043
#: (Pacifico). Qualquer valor entre 10 e 90 km produz resultado identico
#: nesses casos — o limiar nao e sensivel.
#:
#: Sugerir Alice Springs a quem esta a 341 km dela e pior que o silencio: o
#: painel cai no estado inicial, com o campo de busca vazio.
RAIO_MAXIMO_KM = 50

#: A folga dentro da qual duas cidades estao **empatadas** em distancia, e a
#: populacao decide.
#:
#: O dump lista distritos como cidades, e no centro de uma metropole eles
#: empatam com ela: `Se` (23.832 hab.) e `Sao Paulo` (12,4 milhoes) estao
#: ambos a 0,4 km do centro, e a distancia pura escolheria entre os dois por
#: ruido de arredondamento — o cabecalho do painel leria "Se".
#:
#: E deliberadamente pequeno. "A maior cidade num raio" e o criterio de raio
#: fixo que o ticket 08 descartou; aqui a populacao so desempata o que a
#: distancia ja nao distingue. A 2 km, Hounslow continua Hounslow e nao vira
#: Londres, que esta a 17 km.
EMPATE_KM = 1.0


def mais_proxima(
    cidades: list[CidadeLocal], latitude: float, longitude: float
) -> tuple[CidadeLocal, float] | None:
    """A cidade mais proxima da coordenada, ou `None` se passar do raio.

    Devolve o par `(cidade, distancia_km)` pelo mesmo motivo que `selecionar`:
    a distancia ja foi calculada para decidir, e quem chama nao deve
    recalcula-la.

    Entre as que empatam em distancia, a mais populosa: veja `EMPATE_KM`.

    `None` e resposta normal, nao erro — e o caso de quem esta longe de
    qualquer cidade cadastrada.
    """
    com_distancia = [
        (cidade, distancia_km(latitude, longitude, cidade.latitude, cidade.longitude))
        for cidade in cidades
    ]
    if not com_distancia:
        return None

    menor = min(distancia for _, distancia in com_distancia)
    if menor > RAIO_MAXIMO_KM:
        return None

    # O empate e medido contra a **menor distancia**, nao contra a anterior:
    # encadear a folga faria uma fila de cidades a 1 km uma da outra alcancar
    # qualquer lugar.
    empatadas = [par for par in com_distancia if par[1] <= menor + EMPATE_KM]
    return max(empatadas, key=lambda par: par[0].population)
