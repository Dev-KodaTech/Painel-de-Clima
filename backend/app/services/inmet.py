"""Cliente da API externa do INMET.

Unico lugar que conhece o formato deles, no mesmo espirito de
`open_meteo.py`. Duas divergencias sao deliberadas, ambas documentadas no
[ADR 0008](../../../docs/adr/0008-inmet-por-json-e-poligono.md):

1. **Cliente HTTP proprio, HTTP/1.1 forcado**, em vez do `AsyncClient`
   injetado que o resto do backend usa. O servidor anuncia ALPN mas nao
   negocia HTTP/2 de verdade e derruba a conexao com connection reset. Sem
   forcar `http1=True` aqui, a requisicao falha de um jeito que nao aponta
   para a causa. **Nao junte este cliente ao padrao de injecao do
   `open_meteo.py` numa limpeza futura** — a peculiaridade e do fornecedor.
2. **Cache de chave fixa**, nao por coordenada. O feed e nacional (~270 KB) e
   serve todas as cidades do Brasil de uma vez; nao ha coordenada a
   incorporar na chave.
"""

import json

import httpx

from app import cache_do_processo
from app.models import AlertaOficial

ENDPOINT = "https://apiprevmet3.inmet.gov.br/avisos/ativos"

#: A chave fixa do cache: o feed inteiro e uma unica entrada nacional.
CHAVE_DE_CACHE = "inmet:avisos"

TIMEOUT = httpx.Timeout(10.0)


class InmetIndisponivel(Exception):
    """A consulta ao INMET falhou: rede, timeout ou status de erro.

    Nao pode derrubar `/api/condicoes` — as condicoes previstas continuam
    mesmo quando o INMET esta fora do ar (ADR 0008). Quem chama traduz isto
    em `status_dos_alertas = "indisponivel"`, nunca em lista vazia silenciosa.
    """


async def buscar_avisos_ativos() -> list[dict]:
    """Os avisos ativos do INMET, ja deduplicados por `id`.

    **Sem parametro de coordenada**: a API devolve sempre o conjunto nacional
    inteiro, e o filtro geografico e nosso — feito depois, por
    ponto-em-poligono. Por isso a chave de cache e fixa: nao ha "consulta por
    cidade" a distinguir aqui.

    **Dedup de `hoje` + `futuro` por `id`**: o payload separa os avisos em
    duas listas que se sobrepoem — um aviso que comeca hoje e continua amanha
    aparece nas duas. Sem o dedup, ele entraria duas vezes na varredura de
    ponto-em-poligono e poderia virar dois cards identicos na interface.
    """
    return await cache_do_processo.atual().obter(CHAVE_DE_CACHE, _buscar)


async def _buscar() -> list[dict]:
    bruto = await _get(ENDPOINT)

    vistos: set[str] = set()
    avisos: list[dict] = []
    for lista in ("hoje", "futuro"):
        for aviso in bruto.get(lista, []):
            identificador = aviso.get("id")
            if identificador in vistos:
                continue
            vistos.add(identificador)
            avisos.append(aviso)
    return avisos


def poligono_do_aviso(aviso: dict) -> list[tuple[float, float]]:
    """O anel externo do poligono do aviso, como lista de `(lon, lat)`.

    **Duplo parse**: `poligono` chega como uma string dentro do JSON, e essa
    string e ela mesma um GeoJSON serializado — `json.loads` duas vezes, nao
    uma. A ordem dos pares e `[lon, lat]`, a ordem do GeoJSON, e nao `[lat,
    lon]` como o resto do backend usa; inverter aqui faria todo
    ponto-em-poligono errar silenciosamente.

    Todos os avisos observados sao `Polygon`, nunca `MultiPolygon` (ADR
    0008) — so o primeiro anel do primeiro poligono e lido.
    """
    geometria = json.loads(aviso["poligono"])
    coordenadas = geometria["coordinates"]
    anel_externo = coordenadas[0]
    return [(ponto[0], ponto[1]) for ponto in anel_externo]


def ponto_no_poligono(
    latitude: float, longitude: float, anel: list[tuple[float, float]]
) -> bool:
    """Se `(latitude, longitude)` esta dentro do anel, por ray casting.

    Algoritmo classico de contagem de cruzamentos por uma semirreta horizontal
    a partir do ponto: um numero impar de cruzamentos com as arestas do
    poligono significa que o ponto esta dentro. Sem dependencia de geometria
    — o poligono e um anel simples, e o app nao precisa de mais que isto
    (ADR 0008: buracos e `MultiPolygon` nunca apareceram nos avisos reais).
    """
    dentro = False
    n = len(anel)
    x, y = longitude, latitude
    for i in range(n):
        x1, y1 = anel[i]
        x2, y2 = anel[(i + 1) % n]
        cruza_em_y = (y1 > y) != (y2 > y)
        if cruza_em_y:
            x_do_cruzamento = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_do_cruzamento:
                dentro = not dentro
    return dentro


#: As cores oficiais do INMET por `id_severidade`, medidas contra o feed real
#: para 6 (Perigo Potencial, amarelo) e 7 (Perigo, laranja). **8 (Grande
#: Perigo) nunca esteve ativo durante a investigacao** — nenhum aviso daquela
#: severidade foi observado ao vivo. O valor abaixo e presumido a partir da
#: progressao de cor do INMET (amarelo -> laranja -> vermelho) e **nao foi
#: confirmado por observacao**. Se um dia a cor real divergir, e aqui que se
#: corrige.
CORES_POR_SEVERIDADE = {
    6: "#FFFE00",  # Perigo Potencial — medido.
    7: "#FF8C00",  # Perigo — medido.
    8: "#FF0000",  # Grande Perigo — presumido, nao observado. Ver docstring.
}

#: A cor de uma severidade que a tabela nao conhece. **O vermelho, nao o
#: amarelo**: uma severidade nova so pode ser mais grave que a maior que
#: conhecemos — a escala do INMET cresce —, e pintar de amarelo o que pode ser
#: um aviso extremo erra para o lado que machuca. Errar para o alarme e
#: recuperavel; errar para a calmaria, numa tela onde se decide sair de casa,
#: nao e.
COR_DE_SEVERIDADE_DESCONHECIDA = "#FF0000"


def para_alerta(aviso: dict) -> AlertaOficial:
    """Converte um aviso bruto do INMET no modelo do payload.

    So os campos que a interface usa entram no modelo — `urgency`,
    `certainty` e afins do CAP nunca chegaram aqui porque a fonte e o JSON
    proprietario, nao o CAP (ADR 0008), e o JSON proprietario nao os traz.
    """
    id_severidade = int(aviso["id_severidade"])
    return AlertaOficial(
        id=str(aviso["id"]),
        tipo=aviso["tipo"],
        severidade=aviso["severidade"],
        id_severidade=id_severidade,
        cor=CORES_POR_SEVERIDADE.get(id_severidade, COR_DE_SEVERIDADE_DESCONHECIDA),
        inicio=aviso["data_inicio"],
        fim=aviso["data_fim"],
        riscos=aviso["riscos"],
        instrucoes=aviso["instrucoes"],
    )


async def alertas_da_coordenada(latitude: float, longitude: float) -> list[AlertaOficial]:
    """Os alertas do INMET cujo poligono cobre a coordenada.

    **So chame isto quando `country_code == "BR"`.** A API nao aceita
    coordenada — devolve sempre o conjunto nacional —, e o filtro geografico
    e nosso; uma coordenada fora do Brasil resultaria em lista vazia
    indistinguivel de "nenhum aviso ativo" (ADR 0008). A distincao entre "sem
    alerta" e "fora de cobertura" e responsabilidade de quem chama, que sabe
    o `country_code` e decide se chama esta funcao.
    """
    avisos = await buscar_avisos_ativos()
    try:
        cobertos = [
            aviso
            for aviso in avisos
            if ponto_no_poligono(latitude, longitude, poligono_do_aviso(aviso))
        ]
        return [para_alerta(aviso) for aviso in cobertos]
    except (KeyError, IndexError, TypeError, ValueError) as erro:
        # O feed e proprietario e **sem versao**: um campo renomeado ou um
        # poligono malformado nao pode virar `500`. Vale a mesma regra da
        # falha de rede — quem chama mostra "nao foi possivel consultar", que
        # e honesto, em vez de uma lista vazia que afirmaria seguranca.
        raise InmetIndisponivel(f"Formato inesperado do feed do INMET: {erro}") from erro


async def _get(url: str) -> dict:
    """Faz a requisicao com HTTP/1.1 forcado e converte falha em `InmetIndisponivel`.

    `ValueError` entra junto de `httpx.HTTPError` porque `response.json()`
    levanta `json.JSONDecodeError` — subclasse de `ValueError`, e **nao** de
    `HTTPError` — quando o corpo vem truncado ou quando um proxy responde
    `200` com uma pagina de erro. Sem ele, a resposta malformada subia como
    `500` em vez de virar "nao foi possivel consultar", que e a degradacao que
    o ADR 0008 exige.
    """
    try:
        async with httpx.AsyncClient(http1=True, http2=False) as client:
            response = await client.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as erro:
        raise InmetIndisponivel(str(erro)) from erro
