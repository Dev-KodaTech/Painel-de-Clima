"""Cadastro, entrada, saida e "quem sou": a conta vista pelo HTTP.

O router e fino de proposito. A politica da senha mora em
`services/conta.py`, o hash em `services/senha.py`, a duracao e o formato do
cookie em `services/sessao.py`, a leitura da sessao em `dependencias.py`, e a
escrita no banco no repositorio. O que sobra aqui e traduzir: corpo da
requisicao para chamada, excecao para status, sessao para cookie.

`conta_da_sessao` morou aqui enquanto o `quem-sou` era seu unico chamador;
mudou-se para `dependencias.py` quando os planos do Calendario e os locais
salvos passaram a precisar dela. O motivo esta registrado la.

**Nenhuma resposta daqui carrega a senha ou o hash** — nem a de erro. `ContaSaida`
tem um campo so, e e o e-mail.
"""

from typing import NoReturn

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app import repositorio_do_processo
from app.db.repositorio import Conta, EmailJaUsado, Repositorio
from app.dependencias import conta_opcional
from app.services import sessao as servico_de_sessao
from app.services.conta import (
    MSG_CREDENCIAIS_INVALIDAS,
    MSG_EMAIL_JA_USADO,
    ContaInvalida,
    credenciais_da_entrada,
    validar_cadastro,
)
from app.services.senha import hash_da_senha, hash_de_descarte, senha_confere

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


class EntradaRequest(BaseModel):
    """O corpo da entrada.

    Os mesmos limites **maximos** do cadastro, e pela mesma razao: barrar o
    corpo absurdo antes de chegar ao Argon2. O que nao aparece aqui e minimo
    algum — a senha curta e recusada como credencial errada, e nao como corpo
    invalido, para que a resposta nao diga se o formato passou na triagem.
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


@router.post("/entrada", response_model=ContaSaida)
def entrada(corpo: EntradaRequest, response: Response) -> ContaSaida:
    """Valida as credenciais e abre uma sessao nova.

    `200`, e nao `201` como o cadastro: entrar nao cria conta, e a sessao que
    ele cria e detalhe de implementacao da mesma resposta — o frontend le o
    e-mail e segue.

    **Uma sessao nova a cada entrada**, sem reaproveitar a anterior. Duas
    entradas sao dois navegadores, e duas linhas e o que permite sair de um
    sem derrubar o outro.

    Os dois modos de falhar — e-mail sem conta, senha errada — saem pelo mesmo
    `_recusar_credenciais`, e e a unica coisa que este endpoint faz questao de
    nao variar.
    """
    email, senha = credenciais_da_entrada(corpo.email, corpo.senha)

    with repositorio_do_processo.atual() as repositorio:
        conta = repositorio.conta_por_email(email)
        if conta is None:
            # Verifica contra um hash de descarte em vez de recusar na hora: a
            # recusa precisa custar o mesmo tempo nos dois casos, senao quem
            # cronometra as respostas descobre quais e-mails tem conta sem
            # nunca ler a mensagem. Ver `hash_de_descarte`.
            senha_confere(senha, hash_de_descarte())
            _recusar_credenciais()

        guardado = repositorio.hash_da_senha(conta.id)
        # `None` aqui e uma conta sem hash, que o schema nao permite. Recusar
        # e o certo mesmo assim: a alternativa seria um `500` que entrega a
        # existencia da conta, e um `if` a menos nao vale isso.
        if guardado is None or not senha_confere(senha, guardado):
            _recusar_credenciais()

        _abrir_sessao(repositorio, conta, response)

    return ContaSaida(email=conta.email)


@router.post("/saida")
def saida(
    response: Response,
    sessao: str | None = Cookie(default=None, alias=servico_de_sessao.NOME_DO_COOKIE),
) -> dict[str, str]:
    """Apaga a linha da sessao e expira o cookie.

    **Apagar a linha e o que faz o logout ser real** — e o ponto inteiro do
    ADR 0005. Sem isso, sair seria o navegador esquecer um papel que continua
    valendo, e o identificador antigo reapresentado a mao voltaria a entrar.

    **`200` sempre**, mesmo sem cookie, com cookie vencido ou com um
    inventado. Nao ha o que apagar e isso nao e falha: quem chega aqui sem
    sessao — segunda aba, clique duplo, cookie ja expirado — queria estar
    fora, e esta. Um `401` faria o frontend tratar como problema o caminho
    mais inofensivo que existe, e distinguiria o identificador que um dia
    existiu do que nunca existiu.

    O cookie e expirado **mesmo quando nao havia sessao**: um cookie que o
    servidor ja nao reconhece continuaria sendo enviado a cada requisicao ate
    vencer sozinho.
    """
    if sessao is not None:
        with repositorio_do_processo.atual() as repositorio:
            # Sem conferir de quem e a sessao, e sem validar a expiracao: quem
            # apresenta o identificador e quem o tem, e apagar uma linha
            # vencida e o mesmo trabalho. `apagar_sessao` apaga **esta** linha,
            # e as outras da mesma conta seguem valendo.
            repositorio.apagar_sessao(sessao)

    # `delete_cookie` com os mesmos `path`, `samesite` e `secure` do carimbo
    # que abriu a sessao: o navegador so substitui um cookie por outro de
    # mesmo nome **e mesmos atributos**, e um `path` diferente deixaria o
    # antigo intacto ao lado do vencido.
    response.delete_cookie(
        key=servico_de_sessao.NOME_DO_COOKIE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=servico_de_sessao.cookie_seguro(),
    )

    return {"detail": "Sessao encerrada."}


def _recusar_credenciais() -> NoReturn:
    """A recusa da entrada — **uma so**, para os dois modos de errar.

    Existe como funcao, e nao como dois `raise` iguais, porque o que o ticket
    pede e que as duas respostas nao divirjam nunca: com dois literais, a
    divergencia seria uma questao de alguem achar que estava ajudando ao
    detalhar um deles.
    """
    raise HTTPException(status_code=401, detail=MSG_CREDENCIAIS_INVALIDAS)


@router.get("/quem-sou", response_model=QuemSouResponse)
def quem_sou(conta: Conta | None = Depends(conta_opcional)) -> QuemSouResponse:
    """A conta da sessao, ou `None`.

    **`200` nos dois casos.** Visitante sem conta e o estado normal de quem
    nunca entrou, e nao uma falha: `401` obrigaria o frontend a tratar como
    erro o caso mais comum que existe, e encheria o console de vermelho em toda
    visita anonima.

    E a razao de o guard opcional existir: este endpoint ja era a rota mista do
    app antes de haver nome para isso, e passar a consumi-lo prova que a
    dependencia entrega o que a leitura a mao entregava.
    """
    return QuemSouResponse(
        conta=None if conta is None else ContaSaida(email=conta.email)
    )


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
