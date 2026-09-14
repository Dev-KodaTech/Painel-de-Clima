# Painel de Clima (Weather Dashboard)

Label: wayfinder:map

## Destination

Um `spec.md` pronto para implementar: um painel de clima com backend FastAPI e frontend React+Tailwind, consumindo Open-Meteo, reproduzindo o layout do print de referência. O mapa termina quando não resta nenhuma decisão a tomar antes de alguém sentar e construir. O build em si fica fora deste mapa.

## Notes

- **Domínio**: clima/meteorologia. Stack: Python FastAPI (backend), React + TailwindCSS (frontend).
- **Greenfield**: o diretório estava vazio quando este mapa foi criado. Não existe "frontend e backend existente" apesar do pedido original dizer isso — o scaffold entra no escopo.
- **Skills por sessão**: `grilling` + `domain-modeling` por padrão; `research` para tickets AFK; `prototype` para tickets de UI.
- **Regra dura**: o frontend nunca chama a Open-Meteo diretamente. Todo dado vem do backend.
- **Sem API key** em qualquer solução. Isso elimina qualquer segunda fonte de dados.
- **Modo**: planejamento. Produzir decisões, não deliverables. O destino é o spec.
- **Referência visual**: o print enviado pelo usuário na abertura do mapa (9 painéis: sidebar, header, card do dia, Temperature Trend, Forecast Summary, Today/sunrise-sunset, Temperature in various regions, Precipitation Levels, Weather Alerts).

## Decisions so far

- [Destino e escopo do esforço](issues/00-destino.md): spec pronto para implementar, não o app construído. Nove decisões de abertura fechadas via grilling (ver o ticket para a lista completa).
- [Campos disponíveis na API Open-Meteo](issues/01-campos-open-meteo.md): todo o print tem dados reais exceto alertas, que não existem na API (confirmado por 3 vias). Geocoding devolve candidatas com admin1/admin2/population para desambiguação. `weather_code` vem só como inteiro; timestamps sem sufixo de fuso.
- [Weather Alerts sem API de alertas](issues/02-alertas-derivados.md): derivar pseudo-alertas do forecast, preservando o layout do print.
- [Mapa regional vs. busca livre](issues/03-regioes-proximas.md): trocar a ilustração da Austrália pela tabela Locations/Temperature com cidades próximas.
- [Fidelidade visual ao print](issues/04-icones.md): Meteocons open-source no lugar dos ícones 3D do kit original.
- [Estados fora do print](issues/05-estados.md): loading, cidade não encontrada, erro de API e desambiguação entram. Dark mode fica fora de escopo.
- [Cache, endpoints e mapeamento WMO](issues/06-contrato-backend.md): cache em memória TTL 10min por coordenada arredondada; dois endpoints (`/api/weather`, `/api/cities`); mapeamento WMO→texto/ícone no backend.
- [Critério de cidades próximas](issues/08-criterio-proximidade.md): a Open-Meteo aceita **multi-coordenada numa só chamada** (peso 1, não N) — o painel de 6 cidades custa 1 requisição. Vizinhas escolhidas localmente de `cities15000` (3,2 MB) por anéis de raio crescente. Reverse geocoding e busca por região **não existem** na API.
- [Regra de derivação dos pseudo-alertas](issues/07-regra-alertas.md): limiar fixo (vento ≥60 km/h, chuva ≥20 mm, `weather_code` 95/96/99) com **dedup por categoria** — no máximo 1 card por tipo, o pior dia. Testado em 6 cidades: 0–2 cards cada. Limiar relativo à cidade foi testado e **rejeitado** (em Wellington esconderia rajadas de 86 km/h). Painel renomeado para não passar por aviso oficial.
- [Forma do payload de /api/weather](issues/09-payload.md): objeto por painel (`location`/`current`/`hourly`/`daily`/`sun`/`alerts`/`nearby`/`units`/`attribution`), **3,5 KB minificado**. Custa **2 chamadas** à Open-Meteo, não 1: pedir tudo numa multi-coordenada traz 168h por vizinha (77% mais banda). Unidades fixas em °C. Exemplo real em `payload-exemplo.json`.
- [Scaffold do projeto](issues/11-scaffold.md): `backend/` + `frontend/` na raiz, sem monorepo. **uv** e **npm** (únicos instalados nesta máquina), Vite 8 + React + **TypeScript**, **Tailwind v4** (config CSS-first via `@theme`, não `tailwind.config.js` — afeta o ticket 10). Proxy do Vite dispensa CORS em dev. `git init` faz parte.
- [Tokens visuais extraídos do print](issues/10-tokens-visuais.md): paleta de 9 cores + raios + sombra como bloco `@theme` do Tailwind v4; **Poppins**; grid de 3 faixas de proporções distintas, não 12 colunas. Protótipo dos 9 painéis publicado. Meteocons confirmado MIT (`@bybas/weather-icons` 2.0.0).
- [Geolocation do navegador](issues/13-geolocation.md): reverse geocoding **local** sobre o `cities15000` já carregado — sem API nem dependência nova. Raio máximo **50 km** (medido: área povoada acerta <5 km, o caso seguinte salta para 95 km). Atrás de botão, nunca no load. Modo novo `?lat=&lon=` em `/api/cities`. Corrigiu índice de coluna errado no ticket 08.
- [Estratégia de teste](issues/12-testes.md): pytest no backend, priorizado pelos **3 bugs reais** desta sessão (chave `results` ausente, índice de coluna errado, limiar sem dedup). Rede mockada com `respx` + 1 teste de contrato fora da suíte padrão. Frontend sem testes unitários — TypeScript cobre a classe de erro que importa.

## Not yet specified

<!-- o que graduou para ticket foi removido daqui; o que resta continua difuso demais para virar pergunta -->

- **Responsividade**: o print é desktop (~1200px+). Como os nove painéis se comportam em tablet e celular não está especificado em lugar nenhum, e só fica decidível depois que o grid existir (ver [Tokens visuais extraídos do print](issues/10-tokens-visuais.md)).
- **Persistência**: última cidade buscada sobrevive a um reload? Favoritos? O print mostra uma busca só, sem histórico.
- **Atualização dos dados**: o painel refaz a busca sozinho enquanto aberto, ou só sob ação do usuário? Interage com o TTL de 10 min do cache.
- **Deploy**: onde isto roda, se é que roda. Fora do destino declarado, mas pode impor restrições retroativas ao scaffold.

## Out of scope

- **Dark mode** ([Estados fora do print](issues/05-estados.md)): o toggle sol/lua do header fica decorativo. Dobraria o trabalho de estilo dos nove painéis e o print só mostra o tema claro.
- **Alertas meteorológicos oficiais**: exigiriam um segundo provedor com API key (NWS/NOAA, Meteoalarm, Weatherbit), contra a restrição de não usar key.
- **Construir o app**: este mapa termina no spec. O build é um esforço seguinte.
