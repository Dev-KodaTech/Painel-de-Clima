"""Selecao de cidades vizinhas por aneis de raio crescente.

Duas abordagens mais simples foram testadas e descartadas antes desta:

- **"maior cidade num raio fixo, expandindo"** mandou Reykjavik para Londres e
  Honolulu para megalopoles chinesas a 8.000 km — a maior cidade de um raio
  largo nao e vizinha, e so a maior do mundo naquele raio.
- **pontuar por populacao dividida pela distancia** devolveu suburbios do
  proprio municipio: Berlim -> Heiligensee, Teltow.

A escala de aneis e o que trata isolamento: regioes densas nunca saem do
primeiro anel, e so uma cidade sem vizinhas proximas alcanca os aneis largos.
Fronteiras nacionais funcionam **sem caso especial** porque nada aqui olha o
pais — Basileia devolve Mulhouse (FR), Freiburg (DE) e Berna (CH) sozinha.
"""

import math

from app.services.geonames import CidadeLocal

#: Raios dos aneis, em km. Um anel so e consultado se os anteriores nao
#: encheram a lista, e o ultimo (25.000 km) e meia circunferencia da Terra:
#: garante que nenhuma coordenada devolva lista vazia.
ANEIS_KM = (100, 250, 600, 1500, 5000, 25000)

#: Abaixo disto e a propria cidade, nao vizinha. E o que separa Potsdam (27 km,
#: cidade real) de Kreuzberg (2,8 km, bairro de Berlim): o dataset lista bairros
#: como cidades, e sem este corte Berlim devolveria os seus proprios.
RAIO_PROPRIA_CIDADE_KM = 15.0

#: Separacao minima entre duas escolhidas. Sem ela, uma conurbacao ocuparia a
#: tabela inteira com nomes da mesma mancha urbana.
SEPARACAO_MINIMA_KM = 25.0

#: Quantas exibir, no maximo. O design comporta de quatro a cinco linhas, e
#: uma lista pode terminar com quatro quando a quinta seria uma cidade solta
#: (ver `SALTO_MAXIMO`).
QUANTAS = 5

#: Quantas vezes mais distante que a anterior uma vizinha pode estar antes de
#: deixar de ser vizinha.
#:
#: Esgotado o arquipelago, Honolulu alcancava **Los Angeles a 4.120 km** — a
#: maior cidade do anel largo, que e exatamente a "megalopole distante" que o
#: criterio de raio fixo produzia. Uma cidade isolada de verdade nao tem esse
#: perfil: as vizinhas de Papeete estao todas entre 4.094 e 4.569 km (saltos de
#: 1,0x), porque sao uma regiao, ainda que remota. O salto brusco no fim da
#: lista nao e isolamento, e preenchimento.
#:
#: Cinco e o limiar: o maior salto legitimo medido e 6,9x (Reykjavik, que sai
#: da Islandia para as ilhas britanicas) e nao ha caso entre 7x e 9x.
SALTO_MAXIMO = 7.0

#: Raio medio da Terra, em km.
_RAIO_TERRA_KM = 6371.0


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia de grande circulo entre duas coordenadas (haversine).

    A Terra como esfera basta: o erro contra o elipsoide fica abaixo de 0,5%, e
    a tabela exibe a distancia arredondada ao quilometro.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = phi2 - phi1
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * _RAIO_TERRA_KM * math.asin(math.sqrt(a))


def selecionar(
    cidades: list[CidadeLocal],
    latitude: float,
    longitude: float,
    quantas: int = QUANTAS,
) -> list[tuple[CidadeLocal, float]]:
    """As vizinhas de uma coordenada, cada uma com a sua distancia.

    Devolve pares `(cidade, distancia_km)`: a distancia ja foi calculada para
    escolher, e recalcula-la depois abriria espaco para exibir uma diferente da
    que decidiu a escolha.

    A busca e linear sobre as 34 mil cidades — ~40 ms, sem indice espacial.
    """
    candidatas = []
    for cidade in cidades:
        distancia = distancia_km(latitude, longitude, cidade.latitude, cidade.longitude)
        if distancia < RAIO_PROPRIA_CIDADE_KM:
            continue
        candidatas.append((cidade, distancia))

    escolhidas: list[tuple[CidadeLocal, float]] = []
    for raio in ANEIS_KM:
        # Maior populacao primeiro: dentro de um anel, a mais relevante e a
        # maior. A distancia so define *qual anel*, nunca a ordem dentro dele.
        no_anel = sorted(
            (par for par in candidatas if par[1] <= raio),
            key=lambda par: par[0].population,
            reverse=True,
        )

        for cidade, distancia in no_anel:
            if len(escolhidas) >= quantas:
                break
            if _perto_de_alguma(cidade, escolhidas):
                continue
            escolhidas.append((cidade, distancia))

        if len(escolhidas) >= quantas:
            break

    # Por distancia: a tabela e uma comparacao com a regiao em volta, e lida de
    # perto para longe ela mostra a regiao se abrindo.
    return _sem_a_cauda_solta(sorted(escolhidas, key=lambda par: par[1]))


def _sem_a_cauda_solta(
    ordenadas: list[tuple[CidadeLocal, float]],
) -> list[tuple[CidadeLocal, float]]:
    """Corta o fim da lista a partir de um salto de distancia desproporcional.

    Uma vizinha muitas vezes mais distante que a anterior nao e vizinha: e a
    maior cidade que sobrou no anel largo. Cortar da quatro linhas em vez de
    cinco, e quatro linhas honestas e o que o ticket pede.

    So o fim da lista e cortado. Um salto no meio e uma regiao que rareia —
    Honolulu passa de 16 km para 151 km entre ilhas do mesmo arquipelago —, e
    ali as seguintes ainda formam um conjunto.
    """
    for indice in range(len(ordenadas) - 1, 0, -1):
        anterior = ordenadas[indice - 1][1]
        if anterior > 0 and ordenadas[indice][1] / anterior > SALTO_MAXIMO:
            return ordenadas[:indice]
    return ordenadas


def _perto_de_alguma(
    cidade: CidadeLocal, escolhidas: list[tuple[CidadeLocal, float]]
) -> bool:
    """Se `cidade` esta a menos da separacao minima de alguma ja escolhida."""
    return any(
        distancia_km(cidade.latitude, cidade.longitude, ja.latitude, ja.longitude)
        < SEPARACAO_MINIMA_KM
        for ja, _ in escolhidas
    )
