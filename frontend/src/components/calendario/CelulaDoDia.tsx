/**
 * Uma celula da grade: um dia, dos dois lados da fronteira.
 *
 * ## Por que um componente so para os dois horizontes
 *
 * Espelha a decisao do backend em `DiaDoHorizonte`: **um tipo com campos
 * opcionais, e nao dois modelos numa uniao.** As dezesseis celulas sao a mesma
 * coisa — um dia com data, numeros e um julgamento de quanto se pode confiar
 * nele —, e o que muda entre elas e o que veio preenchido. Dois componentes
 * fariam a grade ramificar antes de desenhar o que e comum, e a fronteira
 * viraria um corte de codigo em vez do que ela e: uma linha na tela.
 *
 * ## A distincao entre os horizontes e estrutural, nao cromatica
 *
 * O horizonte longo nao e "o curto mais apagado". Ele mostra **outra coisa**:
 * onde o curto tem um ceu desenhado, ele tem a probabilidade de chuva; onde o
 * curto afirma, ele qualifica. Por isso a diferenca sobrevive ao daltonismo, ao
 * tema escuro e ao leitor de tela — nao ha cor nenhuma carregando sozinha o
 * peso da distincao. O `aria-label` do dia distante diz "previsao menos
 * precisa" com todas as letras, e nao deixa isso para um cinza que ninguem
 * ouve.
 */

import type { DiaDoHorizonte, Units } from "../../api/types";
import {
  dataPorExtenso,
  diaDoMes,
  probabilidade,
  temperatura,
} from "../../formato";
import { WeatherIcon } from "../WeatherIcon";

/**
 * So a unidade que a celula escreve.
 *
 * `Pick` e nao `Units` inteiro: a grade nao mostra chuva acumulada, vento nem
 * distancia, e pedir os quatro campos obrigaria quem a usa a inventar tres
 * valores que ninguem le — o que e exatamente o que a pagina teria de fazer
 * enquanto o painel ainda carrega.
 */
export type UnidadesDaGrade = Pick<Units, "temperature">;

type Props = {
  dia: DiaDoHorizonte;
  units: UnidadesDaGrade;
  /** O primeiro dia da grade — sempre o dia corrente, que o backend monta. */
  hoje: boolean;
  /** A coluna onde a celula entra; so a primeira da grade precisa dizer. */
  colunaInicial?: number;
  /**
   * O **primeiro** dia do horizonte longo: a celula onde a fronteira cai.
   *
   * Ela ganha um traco a mais na borda esquerda, que e a marca no lugar exato
   * da troca. As demais celulas distantes ja se distinguem pelo tracejado e
   * pela ausencia de fundo, mas nenhuma delas diz **onde** a mudanca comecou —
   * e a grade e de sete colunas, entao a fronteira cai no meio de uma linha na
   * maioria das semanas, onde uma faixa horizontal nao teria como passar.
   */
  abreOHorizonteLongo?: boolean;
};

/**
 * O que um leitor de tela ouve ao chegar na celula.
 *
 * Montado por extenso, e nao deixado para a leitura visual do conteudo: sem
 * isto a celula seria anunciada como "16 22° 14°" — tres numeros sem rotulo,
 * que e exatamente a celula muda que a issue proibe. A data vem inteira
 * ("quarta-feira, 16 de setembro") porque quem navega por teclado chega aqui
 * sem o contexto da coluna que uma pessoa vendo a grade tem.
 *
 * O aviso do horizonte longo entra **na mesma frase**, e nao como um texto
 * solto ao lado: quem ouve a celula precisa ouvir a ressalva junto do numero
 * que ela qualifica.
 */
/**
 * Se o dia chegou **sem numero algum**.
 *
 * Uma so definicao porque dois lugares dependem dela e precisam concordar: o
 * anuncio, que troca a ressalva do horizonte longo por "sem previsao", e o
 * corpo da celula, que imprime "sem dado" no lugar dos graus. Escrita duas
 * vezes, a primeira divergencia produziria uma celula que mostra "sem dado" e
 * anuncia uma maxima, ou o contrario.
 */
function semNumero(dia: DiaDoHorizonte): boolean {
  return dia.high === null && dia.low === null;
}

function anuncio(
  dia: DiaDoHorizonte,
  units: UnidadesDaGrade,
  hoje: boolean,
): string {
  const partes = [hoje ? `Hoje, ${dataPorExtenso(dia.date)}` : dataPorExtenso(dia.date)];

  if (dia.description) partes.push(dia.description);
  if (dia.high !== null) {
    partes.push(`maxima de ${temperatura(dia.high, units.temperature)}`);
  }
  if (dia.low !== null) {
    partes.push(`minima de ${temperatura(dia.low, units.temperature)}`);
  }

  // Uma celula da ponta da grade pode nao ter numero algum: a API devolve as
  // dezesseis datas sempre, mas os valores do ultimo dia as vezes vem nulos
  // (medido em Berlim e no Cairo). O dia continua na grade, e diz o que e.
  //
  // Quando nao ha numero, **a ressalva do horizonte longo nao entra**: "sem
  // previsao disponivel" ja e a unica coisa a dizer, e "previsao menos precisa,
  // sem previsao disponivel" se contradiz na mesma frase — a imprecisao
  // qualifica um numero, e aqui nao ha numero para qualificar.
  if (semNumero(dia)) {
    partes.push("sem previsao disponivel para este dia");
  } else if (dia.horizonte === "longo") {
    if (dia.precipitation_probability_max !== null) {
      partes.push(
        `${probabilidade(dia.precipitation_probability_max)} de chance de chuva`,
      );
    }
    partes.push("previsao menos precisa, de modelo de menor resolucao");
  }

  return partes.join(", ");
}

export function CelulaDoDia({
  dia,
  units,
  hoje,
  colunaInicial,
  abreOHorizonteLongo = false,
}: Props) {
  const longo = dia.horizonte === "longo";

  return (
    <li
      // `gridColumnStart` so na primeira celula: dali em diante o fluxo do
      // grid ja poe cada dia na coluna seguinte sozinho. Empurrar todas seria
      // recalcular em dezesseis lugares o que a primeira ja resolveu.
      style={colunaInicial ? { gridColumnStart: colunaInicial } : undefined}
      className={[
        "flex min-h-[104px] flex-col gap-0.5 rounded-inner p-2",
        // A moldura do horizonte longo e tracejada e **sem fundo proprio**: o
        // dia distante fica um degrau atras do cartao em vez de sobre ele.
        //
        // Sao dois sinais somados de proposito — contorno interrompido e
        // ausencia de preenchimento —, e nenhum deles e cor: sobrevivem ao
        // daltonismo e ao tema escuro, que e o que a issue pede. Com so o
        // tracejado sobre `bg-card`, a pagina rodando mostrou as duas metades
        // quase identicas de longe.
        longo ? "border border-dashed border-ink-3/50" : "border border-line",
        // A marca da fronteira, na propria celula em que ela cai: uma borda
        // esquerda solida e mais grossa. E o "entre o dia 7 e o dia 8" que a
        // issue pede, posto onde a troca acontece — uma faixa horizontal nao
        // serviria, porque numa grade de sete colunas a fronteira cai no meio
        // de uma linha na maioria das semanas.
        // Solida, ao contrario do resto da moldura tracejada: a fronteira e o
        // unico traco da celula que afirma algo em vez de qualificar.
        //
        // `[border-left-style:solid]` e nao uma utilitaria: as de borda do
        // Tailwind v4 compilam para `border-left-style: var(--tw-border-style)`,
        // e a variavel ja vale `dashed` por causa do tracejado desta mesma
        // celula — uma classe de estilo por lado nao existe para sobrescreve-la.
        // Verificado no CSS gerado.
        abreOHorizonteLongo
          ? "border-l-2 border-l-ink-2 [border-left-style:solid]"
          : "",
        // Hoje ganha o azul; os demais dias do horizonte curto, o fundo de
        // cartao. O dia distante nao recebe fundo nenhum — e parte da
        // distincao. `hoje` vem primeiro porque o primeiro dia da grade e
        // sempre curto, e as duas regras se sobreporiam nele.
        hoje ? "bg-brand text-white" : longo ? "" : "bg-card",
      ].join(" ")}
    >
      {/*
        O anuncio como texto `sr-only`, e **nao** um `aria-label` no `<li>`.

        `listitem` e um dos papeis em que a ARIA 1.2 proibe nome vindo do autor:
        um `aria-label` ali fica a criterio do motor. O Chrome hoje o computa —
        a arvore de acessibilidade foi lida e o nome estava la —, e e
        exatamente por isso que o atributo enganava: passava na verificacao e
        continuava dependendo de leniencia que a especificacao nao promete.

        Como todo o conteudo visivel da celula e `aria-hidden`, o dia seria
        anunciado como item vazio no leitor que seguisse a regra. O texto real
        nao depende de interpretacao de ninguem.

        `sr-only` e o padrao que `ResumoEmTexto` e a `TabelaComparativa` ja
        usam neste repo, pelo mesmo motivo: a leitura auditiva do conteudo e
        outra da visual, e nao uma etiqueta colada por cima.
      */}
      <span className="sr-only">{anuncio(dia, units, hoje)}</span>

      <div className="flex items-baseline justify-between">
        <span
          className={`text-[13px] font-semibold ${hoje ? "text-white" : ""}`}
          aria-hidden="true"
        >
          {diaDoMes(dia.date)}
        </span>
        {hoje && (
          <span className="text-[10px] font-medium text-white/80" aria-hidden="true">
            hoje
          </span>
        )}
      </div>

      {/* O ceu, so no horizonte curto. A ausencia aqui nao e um `if` de
          layout: no dia distante o `icon` chega `null` do backend, que nao
          envia o que a interface nao deve exibir. */}
      {dia.icon && dia.description && (
        <WeatherIcon
          icon={dia.icon}
          description={dia.description}
          className="size-7"
          // A descricao ja entrou no `aria-label` da celula; repeti-la no
          // `alt` faria o leitor de tela dizer "chuva" duas vezes.
          decorativo
        />
      )}

      <div className="mt-auto" aria-hidden="true">
        {dia.high !== null && (
          <p className={`text-[13px] font-semibold ${hoje ? "text-white" : ""}`}>
            {temperatura(dia.high, units.temperature)}
          </p>
        )}
        {dia.low !== null && (
          <p className={`text-[11px] ${hoje ? "text-white/80" : "text-ink-2"}`}>
            {temperatura(dia.low, units.temperature)}
          </p>
        )}

        {/* No lugar do ceu, a chance de chuva: a unica incerteza que o
            endpoint serve de graca (ADR 0010). A gota nomeia o numero para
            quem le rapido — 40% sozinho nao diz 40% de que. */}
        {longo && dia.precipitation_probability_max !== null && (
          <p className="text-[11px] text-ink-2">
            {probabilidade(dia.precipitation_probability_max)} chuva
          </p>
        )}

        {semNumero(dia) && <p className="text-[11px] text-ink-3">sem dado</p>}
      </div>
    </li>
  );
}
