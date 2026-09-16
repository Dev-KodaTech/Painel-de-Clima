"""Configuracao lida do ambiente."""

import os


def cors_origins() -> list[str]:
    """Origens permitidas pelo CORS, de `CORS_ORIGINS` (separadas por virgula).

    Vazio por padrao: em dev o proxy do Vite dispensa CORS, e em producao o
    FastAPI serve o build estatico na mesma origem. A variavel existe para o
    dia em que as origens se separarem.
    """
    raw = os.environ.get("CORS_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


#: A URL do banco em desenvolvimento, igual as credenciais do `compose.yaml`.
#:
#: Ha um padrao — e nao exigencia da variavel — porque quem clona o projeto
#: sobe o container e roda as migracoes sem escrever configuracao nenhuma. Em
#: producao `DATABASE_URL` vem do ambiente e este valor nunca e usado.
URL_DO_BANCO_EM_DEV = "postgresql+psycopg://painel:painel@localhost:5433/painel"


def database_url() -> str:
    """A URL do banco, de `DATABASE_URL`.

    O driver e o `psycopg` 3, declarado no proprio esquema
    (`postgresql+psycopg://`): sem ele o SQLAlchemy tenta o `psycopg2`, que nao
    esta instalado, e o erro fala de um pacote que ninguem pediu.
    """
    return os.environ.get("DATABASE_URL", URL_DO_BANCO_EM_DEV)


#: O ambiente em que o processo roda. So `desenvolvimento` muda alguma coisa.
AMBIENTE_DE_DESENVOLVIMENTO = "desenvolvimento"


def em_desenvolvimento() -> bool:
    """Se o processo roda em desenvolvimento, de `AMBIENTE`.

    O padrao e **producao**, e nao o contrario, porque quem consome isto e a
    flag `Secure` do cookie de sessao: um padrao inseguro seria um deploy que
    esquece a variavel e serve a sessao em claro, e o esquecimento oposto so
    custa a sessao no `http://localhost`.
    """
    return os.environ.get("AMBIENTE", "producao") == AMBIENTE_DE_DESENVOLVIMENTO
