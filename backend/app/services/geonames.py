"""O dataset local de cidades: carga no startup e busca por proximidade.

A API externa nao tem busca por proximidade nem por regiao — procurar por
"California" devolve apenas lugares *chamados* California, nunca Los Angeles.
Por isso a selecao de vizinhas e local, sobre o dump `cities15000` do GeoNames
versionado no repositorio.

O arquivo e lido **comprimido**: sao 3,2 MB no repositorio contra 8,4 MB
expandidos, e o `zipfile` da biblioteca padrao dispensa um passo de build que
falharia offline.
"""

import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

#: O dump versionado. Baixa-lo no build acrescentaria um passo que falha
#: offline, e o arquivo muda poucas vezes por ano.
ARQUIVO = Path(__file__).resolve().parent.parent / "data" / "cities15000.zip"

#: **Indices das colunas**, base zero, verificados no arquivo real de 19 campos.
#:
#: `[7]` e `feature_code` (`PPL`, `PPLA`, `PPLC`); `[6]` e `feature_class`, que
#: vale `'P'` em **todas** as 34.136 linhas. Filtrar por `[6]` devolve zero
#: cidades **em silencio** — nenhuma excecao, apenas um painel vazio.
_ID = 0
_NOME = 1
_LATITUDE = 4
_LONGITUDE = 5
_FEATURE_CODE = 7
_PAIS = 8
_POPULACAO = 14
_FUSO = 17

#: Prefixo dos codigos de lugar povoado. Exclui as duas linhas que nao o sao.
PREFIXO_POVOADO = "PPL"


@dataclass(frozen=True)
class CidadeLocal:
    """Uma cidade do dataset local.

    Distinta de `Cidade` (a candidata do geocoding): esta vem do arquivo, nao
    da API externa. Dai nao ter `admin1` nem `country`, que o dump traz apenas
    como codigos (`16`, `DE`) e nao como nomes exibiveis.

    `id` e `timezone` existem porque a cidade resolvida a partir de uma
    coordenada sai por `/api/cities` como candidata, no mesmo formato do modo
    texto: sem eles o frontend teria dois tipos de candidata para tratar.
    """

    id: int
    name: str
    country_code: str
    latitude: float
    longitude: float
    population: int
    timezone: str


def carregar(caminho: Path = ARQUIVO) -> list[CidadeLocal]:
    """Le o dump e devolve as cidades povoadas.

    Leva ~85 ms e ocupa ~8,8 MB em memoria, o que e barato o bastante para o
    startup e dispensa qualquer indice: a busca linear resolve em dezenas de
    milissegundos nesta escala.

    O dump e TSV **sem cabecalho** e sem aspas — `QUOTE_NONE` e obrigatorio,
    porque nomes com aspas (ha-os) fariam o parser default engolir campos e
    deslocar todas as colunas seguintes.
    """
    with zipfile.ZipFile(caminho) as zip_file:
        nome_interno = zip_file.namelist()[0]
        with zip_file.open(nome_interno) as bruto:
            texto = io.TextIOWrapper(bruto, encoding="utf-8", newline="")
            linhas = csv.reader(texto, delimiter="\t", quoting=csv.QUOTE_NONE)

            return [
                CidadeLocal(
                    id=int(campos[_ID]),
                    name=campos[_NOME],
                    country_code=campos[_PAIS],
                    latitude=float(campos[_LATITUDE]),
                    longitude=float(campos[_LONGITUDE]),
                    # Vem vazia em algumas linhas; ausencia de dado e zero
                    # habitantes, e a selecao por populacao as descarta sozinha.
                    population=int(campos[_POPULACAO] or 0),
                    timezone=campos[_FUSO],
                )
                for campos in linhas
                if campos[_FEATURE_CODE].startswith(PREFIXO_POVOADO)
            ]
