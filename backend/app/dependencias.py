"""O guard de sessao: quem esta pedindo, resolvido do cookie por `Depends`.

**Por que um modulo proprio, e nao `routers/conta.py`.** `conta_da_sessao`
nasceu la, chamada de um lugar so, e enquanto foi assim o lugar estava certo.
Deixou de estar quando o segundo e o terceiro consumidor apareceram: os planos
do Calendario e os locais salvos precisam do mesmo guard, e importa-lo de
`routers/conta.py` faria dois routers depender de um terceiro router — uma
aresta entre features que nao descreve nenhuma relacao de dominio, so a ordem em
que as coisas foram escritas. Aqui, os tres importam do mesmo lugar e nenhum
importa do outro.

**Por que o relogio continua fora do repositorio.** A expiracao e decidida com o
relogio da aplicacao, que o teste troca. Um repositorio que filtrasse por data
precisaria do proprio relogio, e os casos de expiracao passariam a controlar
dois. Esta era a razao de `conta_da_sessao` nao morar no repositorio, e mudar de
arquivo nao a toca.

**Nao ha middleware, e a ausencia e a decisao.** Um middleware que resolvesse a
sessao tornaria invisivel quais rotas exigem conta: descobrir isso passaria a
exigir ler a configuracao do middleware e cruzar com os prefixos. Com um
`Depends` por rota, uma varredura de `routers/` responde a pergunta, e a rota
que esquece o guard e visivelmente diferente da que o tem.
"""

from fastapi import Cookie, Depends, HTTPException, status

from app import repositorio_do_processo
from app.db.repositorio import Conta, Repositorio
from app.services import sessao as servico_de_sessao

#: A recusa de quem nao tem sessao que valha. **Uma so para os tres casos** —
#: cookie ausente, linha inexistente, linha vencida —, pela mesma razao que
#: `MSG_CREDENCIAIS_INVALIDAS` e uma so para os dois modos de errar a entrada:
#: mensagens diferentes diriam a quem testa identificadores quais existem e
#: quais um dia existiram. Nao menciona cookie, sessao expirada nem e-mail.
MSG_SEM_SESSAO = "Entre para continuar."


def conta_da_sessao(repositorio: Repositorio, id_da_sessao: str | None) -> Conta | None:
    """A conta de quem esta pedindo, ou `None` se nao ha sessao que valha.

    Um so caminho para as tres formas de nao ter sessao — cookie ausente, linha
    inexistente e linha vencida —, porque as tres tem de ser indistinguiveis:
    respostas diferentes diriam a quem testa identificadores quais existem.

    Continua sendo funcao comum, e nao uma dependencia, para que quem ja tem um
    repositorio em maos possa resolver a sessao dentro da **mesma** transacao em
    vez de abrir outra. As duas dependencias abaixo sao a forma `Depends` dela,
    para quem nao tem.

    **A forma `Depends` abre a sua propria transacao**, e isso ainda nao custa
    nada: `/api/quem-sou` so le a conta, e uma transacao e uma transacao. Custara
    quando a primeira rota que exige conta **e** consulta o banco chegar — a
    fatia 05 de `locais-salvos` —, porque o handler abrira a segunda, e a conta
    tera sido lida numa transacao diferente da que le o que ela autoriza. Quem
    implementar essa fatia decide entre um repositorio por requisicao ou receber
    a conta e o repositorio juntos; esta funcao existe justamente para que a
    segunda saida seja possivel sem reescrever o guard.
    """
    if id_da_sessao is None:
        return None

    encontrada = repositorio.sessao(id_da_sessao)
    if encontrada is None:
        return None
    if not servico_de_sessao.esta_valida(encontrada.expira_em, servico_de_sessao.agora()):
        return None

    return repositorio.conta_por_id(encontrada.conta_id)


def conta_opcional(
    # `alias` obrigatorio: sem ele o FastAPI derivaria o nome do cookie do
    # **nome do parametro**, e a constante valeria so na escrita — renomea-la
    # quebraria a leitura em silencio, que e exatamente o que ela existe para
    # impedir.
    sessao: str | None = Cookie(default=None, alias=servico_de_sessao.NOME_DO_COOKIE),
) -> Conta | None:
    """A conta da sessao, ou `None` — **sem recusar**.

    A forma para a rota mista: a que responde a todo mundo e muda o que entrega
    conforme quem pergunta. A pagina Calendario e a primeira do app assim —
    previsao e aptidao sao funcao da cidade e servem a visitante sem conta, e so
    a faixa de planos e da conta.

    Recusar aqui obrigaria o frontend a tratar como falha o caso mais comum que
    existe, a visita anonima, e a pagina publica dependeria de um `401`
    interceptado para renderizar.
    """
    with repositorio_do_processo.atual() as repositorio:
        return conta_da_sessao(repositorio, sessao)


def conta_exigida(conta: Conta | None = Depends(conta_opcional)) -> Conta:
    """A conta da sessao, ou `401`. A forma para a rota que exige conta.

    Construida **sobre** `conta_opcional`, e nao ao lado: as duas resolvem a
    sessao do mesmo jeito e so divergem no que fazem com a ausencia. Duas
    leituras independentes do cookie divergiriam no dia em que uma fosse
    ajustada — e a que ficasse para tras seria a que decide quem entra.

    A recusa nao distingue os tres casos, porque `conta_da_sessao` ja os
    colapsou num `None` antes de chegar aqui: nao ha o que distinguir, e essa e
    a propriedade, nao o efeito colateral.
    """
    if conta is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_SEM_SESSAO
        )

    return conta
