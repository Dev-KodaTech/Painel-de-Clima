"""O endpoint da pagina Noticias.

Router proprio, e nao mais uma rota em `weather.py`: **nao ha parametro de
cidade aqui**. Todo endpoint daquele arquivo recebe coordenada e responde
"e aqui?"; este responde a mesma coisa para o pais inteiro (ADR 0009). Junta-los
poria uma rota sem coordenada num modulo cuja assinatura inteira e coordenada,
e o proximo a mexer ali procuraria o parametro que falta.
"""

from fastapi import APIRouter

from app.models import NoticiasResponse, atribuicao_das_noticias
from app.services import noticias

router = APIRouter(prefix="/api")


@router.get("/noticias", response_model=NoticiasResponse)
async def noticias_endpoint() -> NoticiasResponse:
    """As noticias de clima e meio ambiente dos tres veiculos.

    **Sem parametro algum, e sem `503`.** As duas coisas pela mesma razao: com
    tres fornecedores independentes, a indisponibilidade e parcial por padrao
    e vira conteudo da resposta, nao status dela (ADR 0009). Um `503` quando um
    feed cai esconderia as materias dos outros dois; um `503` quando todos caem
    perderia a distincao entre "sem noticias" e "sem resposta", que e
    exatamente o que `status` carrega.

    A atribuicao nomeia **os veiculos que responderam**, e nao os tres fixos:
    creditar quem nao forneceu materia nenhuma seria impreciso do mesmo jeito
    que creditar o INMET sem alerta algum.
    """
    agregado = await noticias.buscar_noticias()

    return NoticiasResponse(
        noticias=agregado.noticias,
        status=agregado.status,
        veiculos_fora_do_ar=agregado.veiculos_fora_do_ar,
        attribution=atribuicao_das_noticias(agregado.veiculos_que_responderam),
    )
