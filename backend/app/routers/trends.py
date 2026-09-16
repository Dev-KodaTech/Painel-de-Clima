"""O endpoint do historico climatologico da pagina Tendencia.

**Separado de `/api/weather` de proposito.** As outras cinco paginas leem o
mesmo `WeatherResponse` pela rota de layout (ver `docs/adr/0002-cidade-na-url.md`),
e um bloco historico dentro dele faria a Visao geral esperar a chamada do
arquivo antes de pintar. O payload do painel tem ~3,5 KB; o historico de 6 meses
com duas series dobra isso, para dado que cinco das seis paginas nunca leem.
"""

from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.models import Janela, TrendsResponse
from app.routers.weather import MSG_INDISPONIVEL
from app.services import historico
from app.services.open_meteo import OpenMeteoIndisponivel

router = APIRouter(prefix="/api")


@router.get("/trends", response_model=TrendsResponse)
async def trends(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    # **`Literal`, e nao `str`**: as tres janelas sao um conjunto fechado, e um
    # valor livre viraria aritmetica de data com entrada arbitraria — `6000d` e
    # uma requisicao de dezesseis anos a API externa. Fora do conjunto e `422`
    # pelo validador, sem codigo nosso, como `CondicaoPrevista.kind` ja e.
    janela: Janela = Query(default="7d"),
) -> TrendsResponse:
    """O historico climatologico de uma coordenada, para uma janela temporal.

    So a coordenada: ao contrario de `/api/weather`, nada aqui exibe o nome da
    cidade — quem o mostra e o cabecalho, que ja o tem. Pedi-lo sem uso seria
    quatro parametros a mais numa URL que nao precisa deles.
    """
    async with httpx.AsyncClient() as client:
        try:
            return await historico.montar(
                client, latitude, longitude, janela, _ultimo_dia_do_arquivo()
            )
        except OpenMeteoIndisponivel as erro:
            raise HTTPException(status_code=503, detail=MSG_INDISPONIVEL) from erro


def _ultimo_dia_do_arquivo() -> date:
    """O dia mais recente que o arquivo aceita como `end_date`.

    **E a data UTC, nao a da cidade consultada**, e a diferenca nao e detalhe:
    a reanalise e publicada num calendario so, e pedir um dia a frente dele nao
    devolve uma serie mais curta — devolve `400`, que aqui viraria um `503` e
    uma pagina de erro.

    Medido: em Wellington (UTC+12) ja e dia 16 enquanto o arquivo so vai ate o
    dia 15, e era exatamente esse pedido que falhava. O custo de ancorar em UTC
    e a cidade adiantada ver a sua janela terminar no dia anterior ao dela por
    algumas horas; o custo de nao ancorar e a pagina nao abrir.
    """
    return datetime.now(timezone.utc).date()
