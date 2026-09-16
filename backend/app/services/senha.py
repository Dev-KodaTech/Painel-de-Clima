"""O hash da senha e a verificacao dele. Duas funcoes, e nada mais.

**Argon2**, dos dois candidatos da spec, porque e o unico que nao impoe um
limite de tamanho surpreendente: o bcrypt ignora tudo depois do 72o byte, e uma
frase-senha longa passaria a ter sufixo decorativo sem que nada avisasse.

O modulo e **puro** de proposito — recebe texto, devolve texto — e e por isso
que os testes o alcancam direto. Quem guarda o hash e o repositorio; quem
decide se a senha e aceitavel e `app/services/conta.py`. Aqui nao ha banco,
politica nem HTTP.

Nenhuma funcao daqui devolve a senha, e nenhuma a poe em mensagem de excecao:
a unica saida e o hash, e o hash nao contem a senha.
"""

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

#: Uma instancia por processo, com os parametros padrao da biblioteca, que sao
#: os recomendados pela RFC 9106. Nao os ajustamos: escolher custo de memoria e
#: paralelismo a mao e a forma mais comum de enfraquecer o Argon2 sem perceber.
_hasher = PasswordHasher()


def hash_da_senha(senha: str) -> str:
    """O hash a guardar. Duas chamadas com a mesma senha dao hashes diferentes.

    O sal e sorteado por chamada e viaja dentro do proprio hash — e por isso
    que `senha_confere` nao precisa recebe-lo separado.
    """
    return _hasher.hash(senha)


def senha_confere(senha: str, hash_guardado: str) -> bool:
    """Se a senha corresponde ao hash.

    Devolve `False` — em vez de deixar a excecao subir — quando o hash e
    ilegivel: uma linha estragada no banco e recusa de credencial, nao erro de
    servidor na cara de quem esta tentando entrar.
    """
    try:
        return _hasher.verify(hash_guardado, senha)
    except (Argon2Error, ValueError):
        # `VerifyMismatchError` e `InvalidHashError` sao ambas `Argon2Error`;
        # `ValueError` cobre o hash que a biblioteca nem tenta interpretar.
        return False


#: Um hash de senha que nenhuma conta tem, calculado uma vez no import.
#:
#: Existe para a entrada com e-mail inexistente gastar o mesmo tempo que a
#: entrada com senha errada. Sem ele, a recusa por conta inexistente voltaria
#: **sem passar pelo Argon2** e seria dezenas de milissegundos mais rapida que
#: a recusa por senha errada — e a diferenca e mensuravel pela rede. Quem
#: quisesse descobrir quais e-mails tem conta nao precisaria ler a mensagem:
#: bastaria cronometrar as respostas, e as duas mensagens iguais que o ticket
#: pede nao teriam escondido nada.
#:
#: A senha que o gera e irrelevante — o que importa e o **custo** de verifica-la
#: contra ela, que e o mesmo de qualquer outra.
_HASH_DE_DESCARTE = _hasher.hash("nenhuma conta tem esta senha")


def hash_de_descarte() -> str:
    """O hash contra o qual verificar quando nao ha conta.

    O resultado da verificacao e sempre `False` e nao deve ser lido: o que se
    quer dele e o tempo gasto, nao a resposta.
    """
    return _HASH_DE_DESCARTE
