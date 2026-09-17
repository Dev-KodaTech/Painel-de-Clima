/**
 * A grade de dezesseis dias, com a fronteira do dia 8 desenhada.
 *
 * ## Escrita a mao, e isso e uma decisao
 *
 * Nem FullCalendar nem shadcn/ui Calendar — a spec mede o porque, e a decisao
 * **nao deve ser reaberta numa limpeza futura sem ler aquele paragrafo**. Em
 * resumo: o primeiro traz ~200 KB e um CSS proprio brigando com os tokens, e e
 * feito para agenda arrastavel; o segundo e um *date picker*, nao uma grade com
 * conteudo por celula, e traria Radix, CVA e um `components.json` que o repo
 * nao tem. O componente central aqui e "celula de dia que mostra clima e
 * julgamento", que e codigo nosso em qualquer cenario.
 *
 * Sem biblioteca de data: o truque de `Date.UTC` sobre componentes ja fatiados
 * que o `formato.ts` usa basta para as duas contas que esta grade faz — o
 * offset da primeira coluna e o limite de mes.
 *
 * **Os nomes vem das tabelas do `formato.ts`, e nao de `Intl.DateTimeFormat`.**
 * A issue pedia `Intl` para os nomes, e vale registrar por que nao: o
 * `formato.ts` ja mantem `MESES`, `DIAS` e `DIAS_CURTOS` desde o primeiro
 * painel, e os sete rotulos de coluna desta grade sao **exatamente** os que
 * `diaDaSemanaCurto` devolve. Usar `Intl` aqui criaria uma segunda fonte para
 * os mesmos nomes, sujeita ao locale do navegador — "Wed" no lugar de "Qua"
 * para quem estiver com o browser em ingles —, numa interface que e pt-BR
 * inteira. A regra do modulo de formatacao vence a linha da issue.
 *
 * ## A grade comeca hoje, nao no dia 1 do mes
 *
 * E uma grade de dezesseis dias **alinhada por dia da semana**, e nao um mes de
 * calendario com os dias sem previsao vazios. Quem abre a pagina quer os
 * proximos dias; o alinhamento existe para que "a proxima quinta" se ache sem
 * contar, que e a story 3. Dai as celulas vazias aparecerem so **antes** do
 * primeiro dia, e nunca depois do decimo sexto.
 */

import type { DiaDoHorizonte } from "../../api/types";
import {
  DIAS_CURTOS,
  colunasVaziasAntesDe,
  diaEMes,
  mesEAno,
  mesmoMes,
} from "../../formato";
import { CelulaDoDia, type UnidadesDaGrade } from "./CelulaDoDia";

type Props = {
  dias: DiaDoHorizonte[];
  units: UnidadesDaGrade;
};

export function Grade({ dias, units }: Props) {
  if (dias.length === 0) return null;

  const primeiro = dias[0];
  const ultimo = dias[dias.length - 1];

  // O indice onde o horizonte longo comeca, **lido do payload** e nao contado
  // como "o oitavo". O backend declara o horizonte de cada dia justamente para
  // que a fronteira nao seja uma regra de indice que os dois lados precisariam
  // manter iguais: se a Open-Meteo mudar o encadeamento de modelos, o ajuste e
  // la e a grade acompanha sozinha. `-1` quando todos os dias sao curtos, que e
  // o que uma resposta encurtada produziria.
  const inicioDoLongo = dias.findIndex((dia) => dia.horizonte === "longo");

  return (
    <div className="flex flex-col gap-3">
      {/* O periodo por extenso, antes da grade. Os dezesseis dias atravessam o
          limite do mes quase sempre, e sem esta linha a sequencia "29, 30, 1,
          2" nao diria que virou outubro. */}
      <p className="text-[13px] text-ink-2">
        {mesmoMes(primeiro.date, ultimo.date)
          ? mesEAno(primeiro.date)
          : `${mesEAno(primeiro.date)} — ${mesEAno(ultimo.date)}`}
      </p>

      {/* `aria-hidden`: os rotulos de coluna orientam quem ve a grade, e quem a
          ouve ja recebe o dia da semana por extenso no anuncio de cada celula.
          Anunciados, virariam sete palavras soltas antes de dezesseis dias. */}
      <ol
        className="grid grid-cols-7 gap-1 text-center text-[11px] text-ink-3"
        aria-hidden="true"
      >
        {/* Os mesmos sete nomes que `diaDaSemanaCurto` devolve: as colunas da
            grade sao os dias da semana, e nao uma lista paralela. */}
        {DIAS_CURTOS.map((coluna) => (
          <li key={coluna}>{coluna}</li>
        ))}
      </ol>

      <ol className="grid grid-cols-7 gap-1">
        {dias.map((dia, indice) => (
          <CelulaDoDia
            key={dia.date}
            dia={dia}
            units={units}
            hoje={indice === 0}
            // So a primeira celula se posiciona; o fluxo do grid cuida do
            // resto. `+ 1` porque as colunas do CSS Grid contam de 1.
            colunaInicial={
              indice === 0 ? colunasVaziasAntesDe(dia.date) + 1 : undefined
            }
            // A marca da fronteira vai na primeira celula do horizonte longo,
            // que e onde a troca de modelo acontece.
            abreOHorizonteLongo={indice === inicioDoLongo}
          />
        ))}
      </ol>

      {inicioDoLongo !== -1 && <Fronteira data={dias[inicioDoLongo].date} />}
    </div>
  );
}

/**
 * A explicacao da fronteira, abaixo da grade.
 *
 * ## O risco concreto que este texto existe para cobrir
 *
 * Metade da grade tem menos informacao que a outra. **Sem uma frase dizendo o
 * contrario, isso le como falha de carregamento** — e uma pessoa que conclui
 * que a pagina quebrou nao volta. E a story 7, e e o motivo de este paragrafo
 * nao ser opcional nem estar escondido atras de um tooltip.
 *
 * ## Por que nao nomeia os modelos
 *
 * "ICON" e "ECMWF" nao significam nada para quem abre um app de clima, e a
 * frase precisa funcionar para essa pessoa. O que ela diz e o que muda na
 * pratica: **a fonte troca e a confianca cai.** Nao nomear nao e o mesmo que
 * mentir — a frase nao afirma nada que o ADR 0010 nao meca —, e quem quiser o
 * detalhe tem a atribuicao no rodape e o ADR no repositorio.
 *
 * ## Abaixo da grade, e nao atravessando-a
 *
 * Uma faixa inserida entre a setima e a oitava celula quebraria o fluxo do
 * grid — a linha da semana e de sete dias, e a fronteira cai no meio de uma
 * delas com frequencia. A distincao ja esta desenhada em cada celula distante
 * (moldura tracejada, sem ceu, com a chance de chuva no lugar); esta nota
 * explica o que a grade ja mostra, em vez de ser a unica coisa que o mostra.
 */
function Fronteira({ data }: { data: string }) {
  return (
    <aside className="flex gap-2.5 rounded-inner border border-dashed border-line p-3">
      {/* O mesmo tracejado das celulas distantes, aqui como amostra: liga a
          frase ao que ela explica sem depender de cor. */}
      <span
        className="mt-0.5 h-8 w-1 shrink-0 rounded-full border border-dashed border-line"
        aria-hidden="true"
      />
      <p className="text-[11px] leading-relaxed text-ink-2">
        <strong className="font-semibold text-ink">
          A partir de {diaEMes(data)}, a previsao vem de outro modelo.
        </strong>{" "}
        Esses dias aparecem com menos detalhe de proposito: a fonte muda, a
        confianca cai e o ceu do dia deixa de ser afirmavel. No lugar dele vem a
        chance de chuva.{" "}
        {/*
          "Nao e falha de carregamento", e **nao** "nao falta dado".

          A primeira versao dizia a segunda, e ela se contradizia com a propria
          grade: o ultimo dia da janela as vezes chega sem maxima nem minima
          (medido em Berlim e no Cairo), e a celula ali imprime "sem dado". Ler
          "sem dado" numa celula e "nao falta dado" logo abaixo e receber duas
          afirmacoes opostas — bem no ponto que esta nota existe para resolver.

          O que a frase precisa negar e o *erro de carregamento*, que e o que a
          metade esparsa da grade parece quando nada a explica. Disso ela nao
          abre mao, e isso continua verdade mesmo na celula sem numero.
        */}
        <strong className="font-semibold">Nao e falha de carregamento</strong> —
        e o que a previsao a essa distancia sustenta.
      </p>
    </aside>
  );
}
