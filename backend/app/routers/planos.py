"""Criar, listar e apagar planos: a intencao de quem tem conta, vista pelo HTTP.

O router e fino, como o de conta: o que sobra aqui e traduzir corpo em chamada,
ausencia em status e linha em resposta. A persistencia esta no repositorio, e a
regra de quem pode o que esta no guard e na condicao do `DELETE`.

## As tres rotas exigem conta, e e a primeira escrita do app que exige

Todo CRUD anterior e leitura publica — previsao, condicoes, noticias — ou a
propria conta. Plano e do dono (ADR 0004: funcao de quem esta olhando vai no
banco), e por isso as tres passam por `conta_exigida`, que responde `401` sem
distinguir cookie ausente de sessao vencida.

## O que **nao** esta aqui: clima

Nenhuma rota daqui devolve icone, temperatura ou aptidao. O plano guarda
titulo, dia e atividade; quem cruza com a previsao e a pagina, que ja busca o
horizonte para desenhar a grade. Servir clima junto duplicaria a busca e
guardaria a previsao no momento da leitura do plano — que e o que o verbete
*Plano* proibe.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app import repositorio_do_processo
from app.db.repositorio import Conta, Plano
from app.dependencias import conta_exigida
from app.models import Atividade

router = APIRouter(prefix="/api")

#: O teto do titulo, **o mesmo da coluna** `planos.titulo`.
#:
#: Aqui ele produz o `422` com a mensagem do Pydantic; la ele e a rede que vale
#: para quem inserir por outro caminho. Os dois existem pela mesma razao que o
#: e-mail tem limite na rota e na coluna.
MAXIMO_DO_TITULO = 200

#: A recusa de apagar o que nao e seu — **e do que nao existe**.
#:
#: Uma so para os dois casos, e e o requisito: `403` no plano alheio
#: confirmaria que ele existe, e quem testasse identificadores mapearia os
#: planos dos outros sem ler nenhum. A mesma indistinguibilidade que
#: `MSG_CREDENCIAIS_INVALIDAS` e `MSG_SEM_SESSAO` mantem.
MSG_PLANO_NAO_ENCONTRADO = "Plano nao encontrado."


class PlanoRequest(BaseModel):
    """O corpo da criacao de um plano.

    **`dia` e `date` e nao `datetime`**, e o tipo e que recusa a hora: plano nao
    tem hora, e um `datetime` aceito aqui seria truncado em silencio pela coluna
    `Date` — quem mandasse `14:00` acreditaria que ela foi guardada.

    **`atividade` e o `Literal` do dominio**, entao o Pydantic recusa qualquer
    valor fora das quatro sem que este modulo escreva a lista. Um plano de
    atividade que nenhuma regra julga nao teria aptidao para cruzar na faixa.
    """

    titulo: str = Field(max_length=MAXIMO_DO_TITULO)
    dia: date
    atividade: Atividade

    @field_validator("titulo")
    @classmethod
    def _titulo_com_texto(cls, valor: str) -> str:
        """Recusa o titulo em branco e apara as pontas.

        `min_length=1` nao bastaria: `"   "` tem tres caracteres e nenhum
        texto, e a faixa mostraria uma linha que ninguem consegue distinguir
        das outras. Aparar e guardar o que a pessoa quis dizer — o espaco no
        fim e quase sempre acidente de digitacao.
        """
        aparado = valor.strip()
        if not aparado:
            raise ValueError("O titulo do plano nao pode ficar em branco.")
        return aparado


class PlanoSaida(BaseModel):
    """Um plano como a API o devolve.

    **Sem `conta_id`**, pela mesma razao de `ContaSaida` nao ter `id`: o
    frontend nao tem o que fazer com ele — os planos vem da sessao, nunca de um
    identificador que o cliente informe — e publica-lo convidaria alguem a
    manda-lo no corpo.
    """

    id: int
    titulo: str
    dia: date
    atividade: Atividade


@router.post("/planos", response_model=PlanoSaida, status_code=status.HTTP_201_CREATED)
def criar(corpo: PlanoRequest, conta: Conta = Depends(conta_exigida)) -> PlanoSaida:
    """Cria um plano na conta de quem esta pedindo.

    A conta vem **da sessao**, e nao do corpo: e o que torna impossivel criar
    um plano na conta de outra pessoa mesmo conhecendo o identificador dela.

    **Dia no passado e aceito.** A pagina lida com plano de dia passado de
    qualquer forma (story 28), e recusar aqui criaria uma regra que a listagem
    depois contradiz — alguem que registra no sabado o que fez na sexta nao
    esta cometendo um erro.
    """
    with repositorio_do_processo.atual() as repositorio:
        criado = repositorio.criar_plano(
            conta.id, corpo.titulo, corpo.dia, corpo.atividade
        )

    return _saida(criado)


@router.get("/planos", response_model=list[PlanoSaida])
def listar(conta: Conta = Depends(conta_exigida)) -> list[PlanoSaida]:
    """Os planos da conta, ordenados por dia.

    **Lista vazia, e nao `404`**, para a conta sem planos: nenhum plano e o
    estado inicial de todo mundo, e nao a ausencia de um recurso. Quem desenha
    "crie o seu primeiro" e a pagina, a partir da lista vazia.
    """
    with repositorio_do_processo.atual() as repositorio:
        planos = repositorio.planos(conta.id)

    return [_saida(plano) for plano in planos]


def _saida(plano: Plano) -> PlanoSaida:
    """A linha do repositorio como a API a devolve.

    Uma funcao e nao duas construcoes iguais: criar e listar devolvem o **mesmo**
    formato, e escreve-lo duas vezes daria a chance de um campo novo entrar so
    numa das respostas.

    `atividade` sai de `str` (o que o repositorio devolve, porque e o que a
    linha traz) para o `Literal` de `PlanoSaida`. O Pydantic **valida** na
    construcao, e e isso que torna a conversao honesta em vez de uma afirmacao:
    se um dia uma linha trouxer atividade fora das quatro — o que o `CHECK`
    impede —, esta funcao levanta em vez de servi-la.
    """
    return PlanoSaida(
        id=plano.id, titulo=plano.titulo, dia=plano.dia, atividade=plano.atividade
    )


@router.delete("/planos/{plano_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(plano_id: int, conta: Conta = Depends(conta_exigida)) -> None:
    """Apaga o plano, **se for de quem esta pedindo**.

    `404` quando o plano e de outra conta, e o mesmo `404` quando ele nao
    existe: `403` confirmaria a existencia, e quem testasse identificadores
    mapearia os planos alheios sem ler nenhum. A conta entra na condicao do
    `DELETE` no repositorio, e nao num `if` daqui — uma checagem antes da
    escrita deixaria uma janela entre a leitura e o apagamento.

    `204` e nao `200` com corpo: nao ha o que devolver, e a lista que o
    frontend redesenha ele ja tem.
    """
    with repositorio_do_processo.atual() as repositorio:
        if not repositorio.apagar_plano(conta.id, plano_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_PLANO_NAO_ENCONTRADO,
            )
