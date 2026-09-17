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

import type {
  Atividade,
  DiaDoHorizonte,
  JulgamentoDeAptidao,
  Units,
} from "../../api/types";
import {
  dataPorExtenso,
  diaDoMes,
  probabilidade,
  temperatura,
} from "../../formato";
import { WeatherIcon } from "../WeatherIcon";
import {
  ANUNCIO,
  CLASSES,
  COR_DO_NIVEL,
  PALAVRA,
  julgamentoDe,
} from "./aptidao";

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
  /**
   * A atividade que governa a pintura, ou `null` no estado sem escolha.
   *
   * A celula **nao** recebe o julgamento ja escolhido: ela recebe a atividade e
   * procura entre os seus. A alternativa faria a `Grade` percorrer as aptidoes
   * de cada dia antes de renderizar, e o dia sem aptidao (horizonte longo) e o
   * dia com ela passariam pelo mesmo `find` num lugar que nao e o dono do dado.
   */
  atividade: Atividade | null;
  /**
   * Se ha ao menos um plano neste dia.
   *
   * **Booleano e nao contagem**: a marca diz "ha plano aqui", e quem lista e a
   * faixa ao lado. Um numero na celula competiria com a data, a maxima e a
   * minima por um espaco de 104 px e responderia uma pergunta que ninguem faz
   * olhando a grade.
   *
   * Falso tambem para quem nao tem conta — sem planos, nao ha o que marcar — e
   * e por isso que a marca nao precisa saber se ha sessao.
   */
  temPlano?: boolean;
  /** Abre o detalhe deste dia. */
  onAbrir: (dia: DiaDoHorizonte) => void;
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
/**
 * A superficie da celula: cor de fundo **e** de traco, numa decisao so.
 *
 * ## Por que as duas saem juntas
 *
 * Elas conflitam. `border-line` e `bg-card` sao emitidas **depois** das
 * utilitarias de aptidao no CSS gerado — medido no `dist`: posicao 12243 contra
 * 11819 —, entao uma celula que pedisse as duas familias ao mesmo tempo
 * perderia a pintura por ordem de regra, e nao por especificidade. O sintoma
 * seria a grade **sem cor nenhuma**, com os tipos certos, o lint limpo e as
 * classes presentes no CSS. Uma expressao so nao tem como produzir o par em
 * conflito.
 *
 * ## A ordem dos casos, e o que cada um protege
 *
 * 1. **Hoje vence a aptidao.** O dia corrente e o unico ponto fixo da grade, e
 *    trocar o azul por verde o faria desaparecer exatamente quando a grade fica
 *    mais cheia de cor. A celula de hoje diz a sua aptidao pela palavra — o
 *    canal que nunca depende de cor de qualquer modo.
 * 2. **A aptidao vence o fundo de cartao.** E o que a pessoa veio ver quando
 *    escolheu uma atividade.
 * 3. **O horizonte longo nao recebe fundo**, e isso e parte da distincao entre
 *    os dois lados da fronteira — ele ja tem a moldura tracejada.
 */
function superficieDaCelula(
  julgamento: JulgamentoDeAptidao | null,
  hoje: boolean,
  longo: boolean,
): string {
  if (hoje) return "border-line bg-brand text-white";
  if (julgamento) return CLASSES[julgamento.nivel];
  return longo ? "" : "border-line bg-card";
}

function semNumero(dia: DiaDoHorizonte): boolean {
  return dia.high === null && dia.low === null;
}

function anuncio(
  dia: DiaDoHorizonte,
  units: UnidadesDaGrade,
  hoje: boolean,
  julgamento: JulgamentoDeAptidao | null,
  temPlano: boolean,
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

  // A aptidao entra **por ultimo e por extenso**: "dia bom para lavar roupa", e
  // nao o adjetivo solto que a celula imprime. Depois de uma data e dois
  // numeros, "boa" sozinho nao diz boa para que.
  //
  // O motivo da reprovacao **nao** entra aqui, e e a mesma razao pela qual ele
  // nao aparece na celula: sete motivos anunciados em sequencia sao um
  // relatorio. Quem quiser o motivo abre o dia, e o anuncio diz que da.
  if (julgamento) {
    partes.push(
      `${ANUNCIO[julgamento.nivel]} ${julgamento.rotulo.toLowerCase()}`,
    );
  }

  // A marca de plano **tambem** entra na frase, e nao so no ponto desenhado:
  // um ponto e cor e forma, e nenhum dos dois chega a quem ouve a grade. Quem
  // navega por teclado precisa saber que ha plano ali sem abrir o dia.
  //
  // Sem dizer **quantos** nem **quais**: a faixa ao lado lista, e repetir os
  // titulos em dezesseis celulas faria o leitor recitar a lista inteira ao
  // atravessar a grade.
  if (temPlano) partes.push("com plano seu");

  return partes.join(", ");
}

export function CelulaDoDia({
  dia,
  units,
  hoje,
  colunaInicial,
  abreOHorizonteLongo = false,
  atividade,
  temPlano = false,
  onAbrir,
}: Props) {
  const longo = dia.horizonte === "longo";
  const julgamento = julgamentoDe(dia, atividade);

  return (
    <li
      // `gridColumnStart` so na primeira celula: dali em diante o fluxo do
      // grid ja poe cada dia na coluna seguinte sozinho. Empurrar todas seria
      // recalcular em dezesseis lugares o que a primeira ja resolveu.
      style={colunaInicial ? { gridColumnStart: colunaInicial } : undefined}
      className="contents"
    >
      {/*
        O dia e um **botao**, e a moldura toda mudou de elemento por causa
        disso: clicar num dia abre o detalhe dele, e um `onClick` no `<li>`
        daria o clique sem dar o foco, o `Enter`, o `Espaco` nem o papel — a
        story 34 pede a grade navegavel sem mouse.

        `contents` no `<li>`: ele continua sendo o item da lista para a
        semantica, e deixa de ser uma caixa no grid para o layout, de modo que
        o botao ocupa a celula diretamente. Sem isso o botao seria um filho
        dentro de um item de grade e a altura minima teria de ser mantida em
        dois lugares.
      */}
      <button
        type="button"
        onClick={() => onAbrir(dia)}
        className={[
          "flex min-h-[104px] flex-col gap-0.5 rounded-inner p-2 text-left outline-none transition-shadow focus-visible:ring-2 focus-visible:ring-brand/50",
        // A moldura do horizonte longo e tracejada e **sem fundo proprio**: o
        // dia distante fica um degrau atras do cartao em vez de sobre ele.
        //
        // Sao dois sinais somados de proposito — contorno interrompido e
        // ausencia de preenchimento —, e nenhum deles e cor: sobrevivem ao
        // daltonismo e ao tema escuro, que e o que a issue pede. Com so o
        // tracejado sobre `bg-card`, a pagina rodando mostrou as duas metades
        // quase identicas de longe.
        longo ? "border border-dashed border-ink-3/50" : "border",
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
        superficieDaCelula(julgamento, hoje, longo),
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
      <span className="sr-only">
        {anuncio(dia, units, hoje, julgamento, temPlano)}
      </span>

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
        {/*
          A marca de plano: um ponto no canto superior, onde nada mais disputa.

          **Nao e cor sozinha**, e nao poderia ser — a celula ja usa cor para a
          aptidao, e um segundo significado cromatico na mesma caixa seria
          ilegivel mesmo para quem enxerga todas. O ponto e uma **forma** que
          aparece ou nao aparece, que e um canal binario e nao uma escala; e o
          anuncio diz "com plano seu" por extenso para quem ouve.

          Herda a cor do texto corrente (`currentColor` via `bg-current`), e
          isso resolve os quatro fundos de uma vez: branco sobre o azul de hoje,
          a cor do nivel sobre a celula pintada, o cinza do texto sobre o cartao.
          Cada um desses ja foi medido contra o seu fundo — escolher uma cor
          fixa aqui exigiria medir um quinto par, e o par pior (cinza sobre
          vermelho) e justamente o que a fatia 06 teve de corrigir.
        */}
        {temPlano && (
          <span
            aria-hidden="true"
            className={`size-1.5 shrink-0 rounded-full ${hoje ? "bg-white" : "bg-current"}`}
          />
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
          <p
            className={`text-[11px] ${
              hoje
                ? "text-white/80"
                : // Na celula pintada a minima usa a cor do nivel, e nao o
                  // cinza: `ink-2` cai para 4,40 / 4,34 / 3,96 sobre os tres
                  // preenchimentos claros, abaixo do minimo de 4,5:1. Ver
                  // `COR_DO_NIVEL`.
                  julgamento
                  ? COR_DO_NIVEL[julgamento.nivel]
                  : "text-ink-2"
            }`}
          >
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

        {/* `ink-3` e o pior caso da pintura — 2,31 / 2,28 / 2,08 sobre os tres
            preenchimentos claros —, entao a celula pintada troca o cinza pela
            cor do nivel aqui tambem. Na pratica o par quase nao acontece (o
            "sem dado" cai na ponta da grade, que e horizonte longo e nao
            pinta), mas "quase nao acontece" nao e uma razao para deixar um
            texto ilegivel esperando o dia em que aconteca. */}
        {semNumero(dia) && (
          <p
            className={`text-[11px] ${
              julgamento && !hoje
                ? COR_DO_NIVEL[julgamento.nivel]
                : "text-ink-3"
            }`}
          >
            sem dado
          </p>
        )}

        {/*
          A aptidao **como palavra**, e nao so como cor de fundo.

          E a story 11, e ela nao se cumpre com um verde mais escuro: quem nao
          distingue verde de vermelho nao distingue tom nenhum deles. A cor
          serve a varredura — achar o dia bom numa olhada, story 10 —, e a
          palavra serve a leitura. As duas stories pedem coisas diferentes, e
          nenhum dos dois canais sozinho atende as duas.

          Na celula de hoje a palavra vem em branco, porque o azul de hoje
          venceu a pintura e a cor do nivel nao tem contraste sobre ele. E o
          caso em que o texto deixa de ser reforco e passa a ser o unico canal —
          que e exatamente por que ele existe.
        */}
        {julgamento && (
          <p
            // `aria-hidden` como o resto do corpo da celula: o anuncio ja diz
            // "dia bom para esporte ao ar livre" por extenso, e sem isto o
            // leitor de tela ouviria a frase inteira e depois "boa" solto. A
            // palavra aqui e o canal **visual** que nao depende de cor; o canal
            // auditivo e o `sr-only` la em cima.
            aria-hidden="true"
            className={`mt-1 text-[11px] font-semibold ${hoje ? "text-white" : ""}`}
          >
            {PALAVRA[julgamento.nivel]}
          </p>
        )}
      </div>
      </button>
    </li>
  );
}
