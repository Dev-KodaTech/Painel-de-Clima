"""As funcoes puras de senha: gerar o hash e verificar.

Testadas diretamente, e nao so pela costura HTTP, porque sao onde uma falha e
silenciosa: um `verificar` que devolvesse `True` para tudo passaria em todo
teste de cadastro — o cadastro nao verifica senha — e so apareceria no dia em
que alguem entrasse com a senha errada.
"""

from app.services.senha import hash_da_senha, hash_de_descarte, senha_confere


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


def test_o_hash_de_descarte_nao_confere_com_o_que_alguem_digitaria():
    """Nenhuma conta tem essa senha.

    O caso **nao** afirma que nada confere com ele: a senha que o gerou
    confere, e nao ha como ser de outro jeito — e um hash de verdade de uma
    senha de verdade. O que importa e que ela nao seja adivinhavel, e a
    resposta de `senha_confere` aqui nem e lida pelo endpoint: o que se quer
    do hash de descarte e o **tempo**, nao o veredito. Ver
    `test_o_hash_de_descarte_e_um_hash_de_verdade`.
    """
    assert not senha_confere("correia-de-bateria", hash_de_descarte())
    assert not senha_confere("", hash_de_descarte())


def test_o_hash_de_descarte_e_um_hash_de_verdade():
    """Tem de custar o mesmo que verificar um hash guardado.

    E o ponto inteiro dele: uma string qualquer faria `senha_confere` recusar
    de imediato, sem passar pelo Argon2, e a recusa por conta inexistente
    voltaria mais rapido que a recusa por senha errada — que e a diferenca que
    o hash de descarte existe para apagar.
    """
    assert hash_de_descarte().startswith("$argon2")


def test_o_hash_de_descarte_e_o_mesmo_em_toda_chamada():
    """Calculado uma vez no import, e nao por requisicao.

    Gera-lo a cada chamada dobraria o custo da entrada sem conta — um hash
    para criar, outro para verificar — e a tornaria mais **lenta** que a
    entrada com senha errada, reabrindo a mesma janela pelo outro lado.
    """
    assert hash_de_descarte() is hash_de_descarte()
