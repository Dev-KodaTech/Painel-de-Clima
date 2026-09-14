# Tokens visuais extraídos do print

Type: prototype
Status: resolved
Blocked by: 04

## Question

Qual a paleta, a tipografia e a escala de espaçamento do print, como config Tailwind?

## Answer

**Protótipo:** https://claude.ai/code/artifact/3d192376-1674-4398-b95d-86459a4713fc — os nove painéis montados com dados reais de Berlim, para comparar lado a lado com o print. Fonte em `../assets/proto-tokens.html`.

### Tokens — bloco `@theme` do Tailwind v4

O [ticket 11](11-scaffold.md) fixou Tailwind **v4**, que é CSS-first: isto vai no `index.css`, **não** num `tailwind.config.js`.

```css
@import "tailwindcss";

@theme {
  --color-page:       #eceef6;  /* fundo lavanda acinzentado da página */
  --color-card:       #ffffff;
  --color-ink:        #1f2430;  /* texto primário, quase-preto azulado */
  --color-ink-2:      #6b7280;  /* secundário */
  --color-ink-3:      #9ca3af;  /* terciário, eixos, placeholders */
  --color-accent:     #f5a524;  /* laranja-âmbar da temperatura grande */
  --color-brand:      #3b6ef5;  /* azul-royal: pílula, dia ativo, barras, linha */
  --color-brand-soft: #e8eefe;  /* fundo do ícone ativo da sidebar */
  --color-line:       #eef0f6;  /* grades e divisórias de tabela */

  --radius-card:  20px;
  --radius-inner: 14px;         /* pílulas de dia, linhas de sunrise, alertas */
  --shadow-card:  0 8px 24px -12px rgb(31 36 48 / .18);

  --font-sans: Poppins, system-ui, sans-serif;
}
```

### Tipografia

**Poppins** — geométrica arredondada, bate com o print; disponível no Google Fonts (HTTP 200 verificado). Pesos 400/500/600/700. Alternativas testadas e igualmente disponíveis: Outfit, Plus Jakarta Sans, Figtree, Nunito, Quicksand.

Escala: títulos de card 14px/600, número grande da temperatura 42–56px/600 com `letter-spacing:-.02em`, corpo 13px, rótulos 10–11px. O print é denso; texto pequeno é característica dele, não acidente.

### Grid

Não são 12 colunas. São **três faixas** de proporções diferentes, num shell de `64px | 1fr` (sidebar fixa + conteúdo):

| Faixa | Colunas | Painéis |
|---|---|---|
| 1 | `1.05fr 1.5fr` | card do dia, Tendência de temperatura |
| 2 | `1.35fr .75fr 1.1fr` | Previsão da semana, Hoje, Cidades próximas |
| 3 | `1.2fr 1fr` | Precipitação, Condições previstas |

Gap uniforme de 16px; padding de card 18px.

### Meteocons confirmado

`@bybas/weather-icons` **2.0.0, licença MIT** no npm — é o pacote dos Meteocons decidido no [ticket 04](04-icones.md). SVG estático e animado, cobre todos os WMO codes. O protótipo usa emoji como placeholder; a implementação mapeia `icon` do payload ([ticket 09](09-payload.md)) para o nome do arquivo.

### Desvios deliberados do print

1. **Painel renomeado** para "Condições previstas" e cada card leva "derivado da previsão" ([ticket 07](07-regra-alertas.md)).
2. **Mapa da Austrália → tabela de cidades** com distância ([tickets 03](03-regioes-proximas.md) e [08](08-criterio-proximidade.md)).
3. **Rodapé de atribuição** que o print não tem — exigência CC-BY 4.0. Coube como faixa fina no fim, sem disputar espaço com os painéis; era a preocupação registrada na névoa.

### O que o protótipo revelou

- **O card de alerta do print não serve para alerta derivado.** Ele mostra "24°" grande com "H:20 L:18" ao lado do aviso — temperatura não diz nada sobre vento ou tempestade. Trocado por categoria + data + valor da métrica que disparou (`64 km/h`).
- **A sidebar tem 7 ícones sem função definida** no print. O protótipo os mantém como decoração; navegação real está fora de escopo (há uma página só).
- **O eixo do gráfico precisa de rótulos esparsos.** 24 marcas não cabem em ~520px; o print mostra 7 (0 AM…7 PM). Protótipo usa 7 a cada 4 horas.

### Fora de escopo

Responsividade abaixo de ~1100px. O print é desktop, e as três faixas têm proporções próprias que precisariam de decisão de empilhamento por faixa. Continua na névoa do mapa.
