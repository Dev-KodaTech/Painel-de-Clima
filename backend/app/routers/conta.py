"""Cadastro e "quem sou": a conta vista pelo HTTP.

O router e fino de proposito. A politica da senha mora em
`services/conta.py`, o hash em `services/senha.py`, a duracao e o formato do
cookie em `services/sessao.py`, e a escrita no banco no repositorio. O que
sobra aqui e traduzir: corpo da requisicao para chamada, excecao para status,
sessao para cookie.

**Nenhuma resposta daqui carrega a senha ou o hash** — nem a de erro. `ContaSaida`
tem um campo so, e e o e-mail.
"""

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, Field

from app import repositorio_do_processo
from app.db.repositorio import Conta, EmailJaUsado, Repositorio
from app.services import sessao as servico_de_sessao
from app.services.conta import MSG_EMAIL_JA_USADO, ContaInvalida, validar_cadastro
from app.services.senha import hash_da_senha

router = APIRouter(prefix="/api")


class CadastroRequest(BaseModel):
    """O corpo do cadastro.

    Os limites de tamanho sao **maximos**, e nao o minimo da senha: o minimo e
    politica, e recusa-lo aqui devolveria o `422` generico do Pydantic em vez
    da mensagem que diz o requisito. O que o Pydantic barra e o corpo absurdo,
    antes de chegar ao Argon2.
    """

    email: str = Field(max_length=1000)
    senha: str = Field(max_length=10_000)


class ContaSaida(BaseModel):
    """A conta como a API a devolve: o e-mail, e nada mais.

    Sem `id`: o frontend nao tem o que fazer com ele — os locais salvos vem da
    sessao, nunca de um identificador que o cliente informe — e publica-lo
    convidaria alguem a mandar um na URL.
    """

    email: str


class QuemSouResponse(BaseModel):
    """Quem esta pedindo, ou `None`.

    O envelope com um campo, em vez de devolver a conta nua ou `204`, existe
    para que "nao ha sessao" seja um **valor** que o frontend le, e nao um
    status que ele precise tratar como falha.
    """

    conta: ContaSaida | None


@router.post("/cadastro", response_model=ContaSaida, status_code=status.HTTP_201_CREATED)
def cadastro(corpo: CadastroRequest, response: Response) -> ContaSaida:
    """Cria a conta e **ja abre a sessao**.

    Cadastrar entra: quem acabou de provar que sabe a senha nao deveria ter de
    digita-la de novo na tela seguinte.

    As duas escritas — a conta e a sessao — acontecem na mesma transacao, que e
    a requisicao inteira: uma conta criada sem sessao deixaria alguem cadastrado
    e de fora.
    """
    try:
        email = validar_cadastro(corpo.email, corpo.senha)
    except ContaInvalida as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    # O hash **fora** da transacao seria melhor para o banco — o Argon2 leva
    # dezenas de milissegundos —, mas prende a conta a um hash calculado antes
    # de saber se o e-mail esta livre. Como o custo e por cadastro e o cadastro
    # e raro, a ordem obvia ganha.
    with repositorio_do_processo.atual() as repositorio:
        try:
            conta = repositorio.criar_conta(email, hash_da_senha(corpo.senha))
        except EmailJaUsado as erro:
            # `409`, e nao `422`: o corpo esta bem formado, e o conflito e com
            # o estado do servidor. E a distincao que deixa o frontend mostrar
            # "tente entrar" em vez de "corrija o campo".
            raise HTTPException(status_code=409, detail=MSG_EMAIL_JA_USADO) from erro

        _abrir_sessao(repositorio, conta, response)

    return ContaSaida(email=conta.email)


@router.get("/quem-sou", response_model=QuemSouResponse)
def quem_sou(
    # `alias` obrigatorio: sem ele o FastAPI derivaria o nome do cookie do
    # **nome do parametro**, e a constante valeria so na escrita — renomea-la
    # quebraria a leitura em silencio, que e exatamente o que ela existe para
    # impedir.
    sessao: str | None = Cookie(default=None, alias=servico_de_sessao.NOME_DO_COOKIE),
) -> QuemSouResponse:
    """A conta da sessao, ou `None`.

    **`200` nos dois casos.** Visitante sem conta e o estado normal de quem
    nunca entrou, e nao uma falha: `401` obrigaria o frontend a tratar como
    erro o caso mais comum que existe, e encheria o console de vermelho em toda
    visita anonima.
    """
    with repositorio_do_processo.atual() as repositorio:
        conta = conta_da_sessao(repositorio, sessao)

    return QuemSouResponse(
        conta=None if conta is None else ContaSaida(email=conta.email)
    )


def conta_da_sessao(repositorio: Repositorio, id_da_sessao: str | None) -> Conta | None:
    """A conta de quem esta pedindo, ou `None` se nao ha sessao que valha.

    Um so caminho para as tres formas de nao ter sessao — cookie ausente, linha
    inexistente e linha vencida —, porque as tres tem de ser indistinguiveis:
    respostas diferentes diriam a quem testa identificadores quais existem.

    Vive no router, e nao no repositorio, porque a expiracao e decidida com o
    relogio da aplicacao; um repositorio que filtrasse por data precisaria de um
    relogio proprio, e os testes de expiracao passariam a controlar dois.
    """
    if id_da_sessao is None:
        return None

    encontrada = repositorio.sessao(id_da_sessao)
    if encontrada is None:
        return None
    if not servico_de_sessao.esta_valida(encontrada.expira_em, servico_de_sessao.agora()):
        return None

    return repositorio.conta_por_id(encontrada.conta_id)


def _abrir_sessao(repositorio: Repositorio, conta: Conta, response: Response) -> None:
    """Cria a linha da sessao e carimba o cookie na resposta.

    Uma funcao so para as duas metades porque elas nao podem se separar: uma
    linha sem cookie e uma sessao que ninguem apresenta, e um cookie sem linha e
    um que sera recusado na requisicao seguinte.

    `httponly` e o ponto inteiro do ADR 0005 — o cookie nao e legivel por
    script nenhum da pagina, nem pelo nosso. `samesite="lax"` permite que a
    navegacao normal para o app leve a sessao junto, e barra o envio em
    requisicao de terceiro. `secure` sai so em desenvolvimento, onde o
    `http://localhost` nao aceitaria o cookie de volta.
    """
    instante = servico_de_sessao.agora()
    expira = servico_de_sessao.expira_em(instante)
    aberta = repositorio.criar_sessao(
        servico_de_sessao.novo_identificador(), conta.id, expira
    )

    response.set_cookie(
        key=servico_de_sessao.NOME_DO_COOKIE,
        value=aberta.id,
        # `max_age` em vez de `expires`: conta a partir de agora, e nao depende
        # de o relogio do navegador concordar com o do servidor.
        max_age=int(servico_de_sessao.DURACAO.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=servico_de_sessao.cookie_seguro(),
        path="/",
    )
