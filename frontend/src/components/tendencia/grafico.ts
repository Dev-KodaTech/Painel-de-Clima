import { dataCurta } from "../../formato";

/**
 * O vocabulario compartilhado dos graficos da pagina Tendencia: cores,
 * medidas e formatadores.
 *
 * Separado de `Caixa.tsx` e `ResumoEmTexto.tsx` pelo mesmo motivo que
 * `estadoDoPainel.ts` mora fora do `Shell`: um arquivo que exporta componente e
 * constante ao mesmo tempo quebra o fast refresh do Vite.
 *
 * Esta pagina usa Recharts; os graficos da Visao geral continuam SVG desenhado
 * a mao. **Sao dois vocabularios de grafico no projeto, de proposito** — a
 * pagina de analise precisa de tooltip, eixo duplo e legenda, que os SVGs
 * atuais nao tem e que seriam trabalho manual consideravel. A migracao dos
 * antigos, se for desejada, e ticket proprio.
 *
 * O que o Recharts **nao** traz de graca e mora aqui:
 *
 * - **Nenhum timestamp passa por `new Date()`.** A regra de `formato.ts` vale
 *   igual: os timestamps sao horario de parede da cidade, e o eixo recebe
 *   texto ja formatado por nos, nunca um `Date`.
 * - **Cor por variavel CSS.** Os graficos existentes usam `var(--color-brand)`
 *   e `var(--color-line)`, que e o que faz o tema escuro funcionar sem uma
 *   unica variante `dark:`. Cor literal quebraria o tema escuro nesta pagina e
 *   so nela.
 */

/** As cores dos graficos, todas por variavel — nunca literais. */
export const COR = {
  atual: "var(--color-brand)",
  /** A serie do ano anterior: ambar, para nao se confundir com a atual. */
  anterior: "var(--color-accent)",
  grade: "var(--color-line)",
  eixo: "var(--color-ink-3)",
  cartao: "var(--color-card)",
} as const;

/** O tamanho dos rotulos de eixo, alinhado ao dos SVGs da Visao geral. */
export const FONTE_DO_EIXO = 10;

/**
 * Margem comum dos graficos.
 *
 * `right` folgado de proposito: o ultimo rotulo do eixo horizontal e centrado
 * sobre o ultimo ponto, e com margem curta metade dele cai fora da area
 * desenhavel — "15 set" aparecia como "15 se". A folga cabe a metade de um
 * rotulo de data.
 *
 * `left` em zero, e nao negativo: puxar o eixo para fora ganha alguns pixels de
 * largura e corta o primeiro caractere dos rotulos verticais ("20 °C" virava
 * "0 °C"). O espaco do eixo vem de `width` no proprio `YAxis`.
 */
export const MARGEM = { top: 8, right: 24, bottom: 0, left: 0 };

/**
 * As props comuns dos eixos. Extraidas porque sao varios graficos e o ajuste de
 * um tamanho de fonte nao deve ser uma edicao em cada um.
 */
export const EIXO = {
  stroke: COR.eixo,
  fontSize: FONTE_DO_EIXO,
  tickLine: false,
  axisLine: false,
} as const;

/** O estilo do tooltip, que o Recharts nao herda do CSS da pagina. */
export const TOOLTIP = {
  contentStyle: {
    background: COR.cartao,
    border: `1px solid ${COR.grade}`,
    borderRadius: 12,
    fontSize: 12,
    boxShadow: "0 8px 24px -12px rgb(31 36 48 / 0.28)",
  },
  labelStyle: { color: "var(--color-ink-2)", fontSize: 11, marginBottom: 2 },
  itemStyle: { padding: 0 },
} as const;

/**
 * Um formatador de tooltip que so ve numeros.
 *
 * O Recharts tipa o valor como `ValueType | undefined` — ele nao sabe que as
 * nossas series sao numericas —, e cada grafico teria de repetir a mesma
 * verificacao. Aqui ela existe uma vez: valor que nao e numero vira traco, que
 * e o mesmo que `Numero` mostra para um dado ausente.
 *
 * Ela nao e so cerimonia de tipo: uma serie com `null` no meio (um dia que o
 * arquivo nao mediu) de fato chega aqui como `undefined` quando o cursor para
 * sobre aquele ponto.
 */
export function formatador(
  formatar: (valor: number) => string,
  rotulo: string,
): (valor: unknown) => [string, string] {
  return (valor) => [
    typeof valor === "number" ? formatar(valor) : "—",
    rotulo,
  ];
}

/**
 * As props do eixo de datas, comuns aos quatro graficos da janela.
 *
 * `interval="preserveStartEnd"` e nao um numero calculado: o numero teria de
 * vir da largura disponivel, que o componente nao mede, e um intervalo pensado
 * para o desktop empilhava os rotulos uns sobre os outros em tela estreita
 * ("17 ago22 ago27 ago"). Assim o proprio Recharts descarta a marca que nao
 * cabe e mantem sempre as duas pontas, que sao as que datam a janela.
 *
 * `minTickGap` e a distancia minima entre dois rotulos: com "13 set" em 10 px,
 * 36 px deixa a folga de um espaco entre eles.
 */
export const EIXO_DE_DATAS = {
  ...EIXO,
  interval: "preserveStartEnd",
  minTickGap: 36,
} as const;

/**
 * Um ponto por dia da janela, com o rotulo ja formatado.
 *
 * Os tres paineis de metrica montavam esta mesma lista, mudando so o campo
 * lido. O rotulo sai de `dataCurta` — recorte de texto, nunca `new Date()`,
 * porque a data e a da cidade consultada.
 *
 * `valor` pode ser nulo e a decisao do que fazer com o nulo fica com o
 * chamador: um dia sem chuva medida **teve** zero de chuva e a barra e zero,
 * mas um dia sem umidade medida nao teve 0% de umidade e a curva deve pular o
 * ponto.
 */
export function porDia<T extends { date: string }>(
  serie: T[],
  ler: (dia: T) => number | null,
): { rotulo: string; valor: number | null }[] {
  return serie.map((dia) => ({ rotulo: dataCurta(dia.date), valor: ler(dia) }));
}
