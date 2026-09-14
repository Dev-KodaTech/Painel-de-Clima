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
