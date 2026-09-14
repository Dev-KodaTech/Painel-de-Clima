# Scaffold do projeto

Type: grilling
Status: resolved

## Question

Como os dois projetos se organizam no diretório, hoje vazio?

## Answer

Ferramentas verificadas **nesta máquina**, não escolhidas no abstrato: `uv` 0.12.3 e `npm` 11.16.0 presentes; poetry, pipenv, pdm, pnpm, yarn e bun **ausentes**. Python 3.14.3, Node v24.18.1, git 2.55.0.

### Layout

```
/
├── CLAUDE.md, docs/agents/          ← já existem
├── CONTEXT.md, docs/adr/            ← lazily, via /domain-modeling
├── backend/
│   ├── pyproject.toml
│   ├── data/cities15000.txt         ← 8 MB, do ticket 08
│   └── app/
│       ├── main.py                  ← FastAPI + CORS
│       ├── routers/weather.py, cities.py
│       ├── services/open_meteo.py, geocoding.py, nearby.py, alerts.py, cache.py
│       ├── models.py                ← Pydantic do ticket 09
│       └── wmo.py                   ← tabela código→texto/ícone
└── frontend/
    ├── package.json, vite.config.ts, index.html
    └── src/
        ├── main.tsx, App.tsx, index.css   ← @theme do Tailwind v4
        ├── api.ts, types.ts               ← espelha o payload do ticket 09
        └── components/                    ← um por painel
```

Dois diretórios na raiz, **sem monorepo**: nada é compartilhado entre Python e TS além do formato JSON, então workspace só acrescentaria cerimônia.

### Escolhas

| Decisão | Escolha | Razão |
|---|---|---|
| Python | **uv** + `pyproject.toml` | única ferramenta moderna instalada; rápida, lockfile próprio |
| Python mínimo | **3.11** | FastAPI 0.141.1 exige ≥3.10; 3.11 dá `tomllib` e melhor performance |
| Frontend | **Vite 8 + React + TypeScript** | TS porque o payload do [ticket 09](09-payload.md) tem 9 blocos aninhados — tipá-lo é o que impede o frontend de errar campo silenciosamente |
| Gestor JS | **npm** | único instalado |
| Tailwind | **v4.3.3** | atual; v3 já é `v3-lts` |
| HTTP client | **httpx** 0.28.1 | async, casa com FastAPI; uma chamada multi-coordenada + uma de vizinhas |

### Tailwind v4 muda a config — afeta o ticket 10

v4 é **CSS-first**: tokens vão num bloco `@theme` dentro do CSS, não em `tailwind.config.js`. Sem arquivo de config JS, sem `postcss.config.js` (usa o plugin `@tailwindcss/vite`). O [ticket 10](10-tokens-visuais.md) deve produzir um bloco `@theme`, não um objeto JS.

### Dev: proxy do Vite

`vite.config.ts` encaminha `/api` → `http://127.0.0.1:8000`. Dois terminais (`uv run uvicorn app.main:app --reload` e `npm run dev`); nada de `concurrently`, que é dependência a mais para substituir duas abas.

**CORS**: o proxy o dispensa em dev — o browser só vê a origem do Vite. O middleware fica configurado mesmo assim, lendo origens permitidas de variável de ambiente, vazio por padrão. Em produção o FastAPI serve o build estático do Vite na mesma origem, e CORS continua desnecessário. Sem isso, o primeiro deploy quebra com erro de CORS obscuro.

### git

`git init` faz parte do scaffold — o diretório ainda não é repositório, o que **bloqueia `/code-review`**. `.gitignore` cobre `__pycache__/`, `.venv/`, `node_modules/`, `dist/`, `.env`.

**Carregamento**: no **startup** do FastAPI, via `lifespan`. Medido: **85 ms** para parsear 34.134 cidades, **8,8 MB** em memória. A pergunta "startup ou preguiçoso?" se dissolve nesse número — 85 ms não atrasa boot nenhum, e lazy só transferiria o custo para a primeira requisição do usuário. Sem índice espacial: busca linear resolve em 40–55 ms.

**`data/cities15000.txt` (8 MB) fica versionado**: é um arquivo, imutável, e baixá-lo no build acrescenta um passo que falha offline e um ponto de rede no deploy. 8 MB é aceitável; se incomodar, baixar no primeiro boot com cache em disco.

### Fora do escopo desta decisão

Deploy, Docker e CI. O destino é o spec; nada aqui impede contêinerizar depois.
