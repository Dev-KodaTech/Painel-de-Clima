"""O banco: o schema, a transacao e os repositorios injetados.

- `schema.py` — as tres tabelas, e so elas.
- `repositorio.py` — o acesso: a interface e as duas implementacoes.
- `transacao.py` — o `engine` e a unidade de trabalho do SQLAlchemy.

O ponto de **injecao** nao mora aqui: e `app/repositorio_do_processo.py`, ao
lado de `cache_do_processo.py`, porque e estado do processo e nao logica de
banco.
"""
