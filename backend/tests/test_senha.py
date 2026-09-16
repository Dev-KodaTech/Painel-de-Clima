"""As funcoes puras de senha: gerar o hash e verificar.

Testadas diretamente, e nao so pela costura HTTP, porque sao onde uma falha e
silenciosa: um `verificar` que devolvesse `True` para tudo passaria em todo
teste de cadastro — o cadastro nao verifica senha — e so apareceria no dia em
que alguem entrasse com a senha errada.
"""

from app.services.senha import hash_da_senha, senha_confere


def test_o_hash_nao_e_a_senha():
    """O que vai para o banco nao pode conter a senha."""
    assert "correia-de-bateria" not in hash_da_senha("correia-de-bateria")


def test_a_senha_certa_confere():
    assert senha_confere("correia-de-bateria", hash_da_senha("correia-de-bateria"))


def test_a_senha_errada_nao_confere():
    assert not senha_confere("outra-coisa", hash_da_senha("correia-de-bateria"))


def test_duas_contas_com_a_mesma_senha_tem_hashes_diferentes():
    """O sal e por hash.

    Sem ele, hashes iguais no banco revelariam quais contas compartilham senha
    — e uma tabela pre-computada quebraria todas de uma vez.
    """
    assert hash_da_senha("a-mesma-senha") != hash_da_senha("a-mesma-senha")


def test_um_hash_corrompido_nao_confere_em_vez_de_levantar():
    """Lixo na coluna e recusa, nao `500`.

    A biblioteca levanta para um hash que nao sabe ler; deixar a excecao subir
    transformaria uma linha estragada num erro de servidor na tela de entrada.
    """
    assert not senha_confere("correia-de-bateria", "nao-e-um-hash")
