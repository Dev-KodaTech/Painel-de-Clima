# 20: Esqueleto que responde e renderiza

**What to build:** os dois projetos existem, sobem com dois comandos e conversam entre si. A página abre no navegador com a paleta e a tipografia do design já aplicadas, e exibe um dado vindo do backend — provando que o caminho completo está ligado antes de qualquer funcionalidade de clima.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

Referência: [spec](../spec.md), seções "Arquitetura geral" e "Interface".

- [ ] `git init` feito, com `.gitignore` cobrindo `__pycache__/`, `.venv/`, `node_modules/`, `dist/`, `.env`
- [ ] `backend/` sobe com uvicorn e responde num endpoint de saúde
- [ ] `frontend/` sobe com Vite e renderiza uma página
- [ ] O frontend lê o endpoint de saúde **pelo proxy do Vite**, sem CORS em dev
- [ ] Middleware de CORS configurado no backend, lendo origens de variável de ambiente, vazio por padrão
- [ ] Bloco `@theme` do Tailwind v4 no CSS com as 9 cores, 2 raios, sombra e fonte Poppins carregada
- [ ] Não existe `tailwind.config.js` nem `postcss.config.js` (v4 é CSS-first)
- [ ] README ou equivalente com os dois comandos para subir o ambiente
