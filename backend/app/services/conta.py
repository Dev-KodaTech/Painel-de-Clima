"""As regras da conta: o que e um e-mail, o que e uma senha aceitavel.

Separado de `senha.py`, que so sabe gerar e conferir hash, e de
`routers/conta.py`, que so sabe falar HTTP. O que mora aqui e a **politica**:
quantos caracteres a senha precisa ter, o que conta como e-mail, e como o
e-mail e normalizado antes de ir para o banco.

A mensagem de recusa e parte da politica, e por isso mora junto dela: quem
muda o minimo tem de esbarrar no texto que o anuncia, em vez de deixa-lo
mentindo a um arquivo de distancia.
"""

from __future__ import annotations

import re

#: O minimo da senha. Oito caracteres e o piso das recomendacoes do NIST, que
#: e o que da para exigir sem empurrar quem se cadastra para o post-it.
MINIMO_DA_SENHA = 8

#: O limite superior existe contra um custo, nao contra uma senha ruim: o
#: Argon2 processa o que receber, e um megabyte de "a" viraria segundos de CPU
#: por requisicao.
MAXIMO_DA_SENHA = 256

MSG_SENHA_CURTA = f"A senha precisa ter ao menos {MINIMO_DA_SENHA} caracteres."
MSG_SENHA_LONGA = f"A senha pode ter no maximo {MAXIMO_DA_SENHA} caracteres."
MSG_EMAIL_INVALIDO = "Informe um e-mail valido."
MSG_EMAIL_JA_USADO = "Ja existe uma conta com esse e-mail. Tente entrar."

#: Deliberadamente frouxa. Validar e-mail por expressao regular e uma batalha
#: perdida — a gramatica de verdade aceita aspas, comentarios e IP literal —, e
#: uma regra apertada recusa endereco valido de gente real. O que se quer aqui
#: e barrar o erro de digitacao obvio; quem prova que o e-mail existe e o envio,
#: que esta fora de escopo.
_FORMATO_DO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#: O mesmo limite da coluna `email`. Sem ele, um e-mail mais longo passaria
#: pela validacao e morreria no banco como `500`.
MAXIMO_DO_EMAIL = 320


class ContaInvalida(ValueError):
    """Os dados do cadastro nao servem. A mensagem e para quem se cadastra.

    **Nunca carrega a senha**, nem em parte: a mensagem vai para a resposta e,
    de la, para o log de quem quer que registre respostas de erro.
    """


def normalizar_email(email: str) -> str:
    """O e-mail como ele vai para o banco: sem espaco em volta.

    **Nao** baixa a caixa. A unicidade sem maiusculas e garantida pelo indice
    sobre `lower(email)` e pela busca com `lower()`; guardar o que a pessoa
    digitou preserva `Ana.Silva@exemplo.com` no lugar de um `ana.silva@` que
    ela nunca escreveu.
    """
    return email.strip()


def validar_cadastro(email: str, senha: str) -> str:
    """Valida e devolve o e-mail normalizado. Levanta `ContaInvalida`.

    Devolve o e-mail em vez de so validar para que o chamador nao possa
    esquecer de normalizar depois de validar — o par "valide e entao
    normalize" e onde entra a conta com espaco no fim.
    """
    normalizado = normalizar_email(email)
    if not _FORMATO_DO_EMAIL.match(normalizado) or len(normalizado) > MAXIMO_DO_EMAIL:
        raise ContaInvalida(MSG_EMAIL_INVALIDO)

    # O comprimento da senha e contado em caracteres, que e o que a pessoa
    # digitou e o que a mensagem promete — nao em bytes, que faria "senha de
    # oito letras" recusar oito letras acentuadas.
    if len(senha) < MINIMO_DA_SENHA:
        raise ContaInvalida(MSG_SENHA_CURTA)
    if len(senha) > MAXIMO_DA_SENHA:
        raise ContaInvalida(MSG_SENHA_LONGA)

    return normalizado
