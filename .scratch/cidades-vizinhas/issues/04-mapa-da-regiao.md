# 04: O mapa da região

**What to build:** a tabela diz "Potsdam, 26 km", e 26 km não diz para que lado.
Nem se as cinco vizinhas estão todas do mesmo lado, nem se a cidade escolhida
está no meio delas ou na beira.

Este ticket entrega o mapa: a cidade escolhida no centro, as vizinhas marcadas em
volta, enquadrado para caber todas. É o que transforma uma distância em posição.

O enquadramento é calculado das coordenadas, nunca um zoom fixo: as vizinhas de
Berlim cabem em dezenas de quilômetros e as de Honolulu em milhares, e um zoom
fixo erraria os dois.

O mapa mostra **onde as cidades ficam**. Não mostra chuva, nuvem nem temperatura
em camadas: a API externa serve dados por coordenada e não serve tiles, e camadas
de radar exigiriam um segundo fornecedor com chave própria — enquanto o glossário
descreve "a API externa" no singular.

**Blocked by:** 01 (as coordenadas precisam chegar ao frontend) e 02 (a página
precisa existir)

**Status:** done

- [x] O mapa aparece na página Cidades vizinhas, com a cidade escolhida no centro
- [x] As cidades vizinhas aparecem marcadas
- [x] O marcador da cidade escolhida é distinto dos das vizinhas
- [x] O enquadramento inicial cabe todas as cidades, sem zoom manual
- [x] O enquadramento funciona tanto numa região densa quanto numa cidade isolada
- [x] Clicar num marcador identifica a cidade
- [x] O mapa pode ser movido e ampliado
- [x] Trocar a cidade escolhida reenquadra o mapa na nova região
- [x] O mapa é destruído ao sair da página, sem deixar instância órfã
- [x] Montar e desmontar duas vezes em desenvolvimento não duplica o mapa nem quebra
- [x] O crédito do OpenStreetMap aparece, como a licença exige
- [x] Os tiles não ficam gritantes no tema escuro
- [x] O mapa é um componente próprio, recebendo cidade escolhida e vizinhas como props
- [x] Sem camadas meteorológicas, sem chave de API, sem conta em serviço de mapas
- [x] O peso que a dependência acrescenta ao bundle foi verificado e registrado

## Comments

**O peso da dependencia.** Medido com `npm run build` antes e depois, no mesmo
commit:

| | antes | depois | delta |
|---|---|---|---|
| JS | 717,92 kB | 868,90 kB | +150,98 kB |
| JS (gzip) | 210,76 kB | 254,94 kB | **+44,18 kB** |
| CSS | 19,01 kB | 34,95 kB | +15,94 kB |
| CSS (gzip) | 4,72 kB | 11,14 kB | **+6,42 kB** |

**+50,60 kB gzip no total** — Leaflet 1.9.4 mais o seu CSS. E a primeira
dependencia de frontend que manipula o DOM fora do React e a primeira que
carrega imagens de terceiro, como a spec antecipou. Nao ha code-splitting no
projeto, entao o peso entra no bundle unico e e pago tambem por quem nunca abre
esta pagina; dividir o bundle e decisao de projeto, nao deste ticket.

**O credito do OpenStreetMap nao foi para o rodape do `Shell`.** A spec fala em
"a mesma linha de rodape que ja credita Open-Meteo e GeoNames", mas esse rodape
vem do backend (`ATRIBUICAO`, em `models.py`) e viaja em **todas** as paginas —
e so esta tem tiles. Creditar o OSM ali poria a licenca em cinco paginas que nao
mostram mapa nenhum. Ficou no controle de atribuicao do proprio Leaflet, dentro
do mapa: aparece e some junto com o que credita, que e o que a licenca pede.

**Os marcadores sao `divIcon`, nao o pino padrao.** O pino padrao do Leaflet
resolve os seus PNGs por caminho relativo ao CSS e **quebra sob bundler** — o
Vite renomeia os arquivos no build. Confirmado no CSS gerado, que traz as regras
de `.leaflet-marker-icon` sem os arquivos correspondentes. Um `divIcon` e HTML
comum: nao passa pelo bundler e ainda herda os tokens de cor do tema.

**Verificacao.** Alem da conferencia manual, os efeitos foram exercitados contra
o Leaflet de verdade em jsdom, num harness descartavel fora do repo (a spec
proibe introduzir suite de testes no frontend). Confirmado: remontar sob
`StrictMode` nao duplica marcador, controle de zoom nem credito e nao deixa DOM
orfao; Berlim enquadra em zoom 8 e Honolulu — 4 vizinhas, 337 km — em zoom 7,
que e o enquadramento adaptativo funcionando; e uma cidade sem vizinhas para no
teto de zoom 11 em vez de cair na rua.

**Fora do escopo, observado:** `tests/test_trends.py::TestUv::test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela`
falha hoje (15/09/2026) por cravar `2026-09-16` como "o dia seguinte". E teste
com data fixa, anterior a este ticket e sem relacao com ele — o backend nao foi
tocado aqui.

**Achados da revisao, aplicados.** A revisao de spec nao encontrou defeito nos
15 criterios. A de padroes encontrou tres, todos corrigidos antes do commit:

1. **`escape` sombreava a funcao global depreciada** de mesmo nome, que faz
   outra coisa (codifica URL). Renomeada para `escaparHtml`.
2. **Um comentario no `index.css` descrevia um aro que a regra nao tinha** —
   "mesmo aro, mesma cor de linha" sobre um bloco que so define fundo e fonte.
   E o defeito que o proprio `TabelaComparativa` argumenta contra a proposito
   de `aria-sort`: afirmar com confianca o que nao e verdade. Reescrito para
   dizer o que a regra de fato faz.
3. **O nome da cidade nao entrava na chave do efeito**, so a coordenada. Uma
   cidade que mudasse de nome sem mudar de lugar manteria o rotulo antigo no
   popup, sem redesenhar. O nome entrou na chave — que aqui e "o que, se mudar,
   precisa ser redesenhado", e nao identidade como em `chaveDaLinha`.

Um quarto, encontrado antes da revisao e confirmado por ela: `cidade ===
escolhida` acertava por identidade — `cidades[0]` *e* a referencia recebida —,
mas marcaria duas cidades como escolhidas se a mesma referencia aparecesse
tambem entre as vizinhas. Passou a ser `indice === 0`.
