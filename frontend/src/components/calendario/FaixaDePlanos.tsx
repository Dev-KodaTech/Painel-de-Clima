/**
 * A faixa de planos, ao lado da grade — a metade da pagina que e da conta.
 *
 * ## E a metade mista, e e o que a pagina tem de novo
 *
 * A grade e a aptidao sao funcao da **cidade** e viajam na URL: qualquer
 * pessoa que abra o link ve o mesmo. A faixa e funcao da **conta**, e so o
 * dono a ve. E a primeira pagina do app em que as duas coisas convivem — Locais
 * salvos, que seria a primeira por conta, e inteira da conta (ver o verbete
 * *Pagina* do `CONTEXT.md`).
 *
 * A consequencia pratica e a regra que governa este componente: **a pagina nao
 * pode exigir conta para nada alem dos planos**. Sem conta, a grade e a aptidao
 * funcionam inteiras e aqui entra um convite para entrar — nunca um bloqueio, e
 * nunca uma pagina que se recusa a carregar.
 *
 * ## Onde ela fica, e por que empilha em vez de recolher
 *
 * Ao lado da grade em tela larga, **abaixo dela** em tela estreita. A issue
 * pedia que a faixa nao empurrasse a grade para fora, e das duas saidas
 * possiveis esta e a que nao inventa estado: um painel recolhivel acrescentaria
 * um controle, uma decisao de padrao (aberto ou fechado) e uma coisa a mais
 * para lembrar entre visitas. Empilhar e o que o resto do app ja faz — o grid
 * da Visao geral e a tabela de vizinhas colapsam por breakpoint, e ninguem
 * precisa aprender nada.
 *
 * Quem decide o arranjo e a pagina, que e quem tem as duas colunas; aqui so se
 * sabe desenhar a faixa.
 */

import { useState } from "react";
import { Link } from "react-router";
import type { Atividade, JulgamentoDeAptidao, Plano } from "../../api/types";
import { CAMINHO_ENTRADA, useComCidade } from "../../navegacao";
import { diaEMes, dataPorExtenso } from "../../formato";
import { ANUNCIO, COR_DO_NIVEL, PALAVRA } from "./aptidao";
import { jaPassou, type PlanoCruzado } from "./planos";

type Props = {
  /**
   * Os planos ja cruzados com a grade, ou `null` enquanto nao se sabe.
   *
   * `null` **nao** e lista vazia: um e "ainda nao sei", o outro e "nao ha
   * nenhum", e a faixa diz coisas diferentes nos dois. Colapsa-los mostraria
   * "crie o seu primeiro plano" a quem tem doze.
   */
  cruzados: PlanoCruzado[] | null;
  /** Se ainda se esta consultando quem e o dono. Ver `Convite`. */
  consultandoConta: boolean;
  /** Se ha conta. Sem ela, a faixa vira convite. */
  temConta: boolean;
  /** A falha ao carregar a lista, ja como frase. */
  erro: string | null;
  /** Os rotulos das atividades, do backend — para nomear a do plano. */
  rotulos: JulgamentoDeAptidao[];
  onApagar: (plano: Plano) => void;
  /** O formulario de criacao entra por aqui, montado pela pagina. */
  children?: React.ReactNode;
};

export function FaixaDePlanos({
  cruzados,
  consultandoConta,
  temConta,
  erro,
  rotulos,
  onApagar,
  children,
}: Props) {
  /*
    Enquanto se consulta quem e o dono, a faixa **nao desenha nada** — nem o
    convite, nem a lista.

    E o precedente do `SeloDaConta`, e a razao e a mesma: um "Crie uma conta"
    que aparece e vira uma lista de planos um instante depois e pior que o
    vazio, porque quem tem sessao veria o proprio convite a cada recarga, como
    se tivesse sido deslogado. O espaco nao pula porque a coluna ja tem largura
    propria no layout da pagina.
  */
  if (consultandoConta) return null;

  if (!temConta) return <Convite />;

  return (
    <section
      aria-labelledby="titulo-dos-planos"
      className="flex flex-col gap-3 rounded-card bg-card p-[18px] shadow-card"
    >
      <h2 id="titulo-dos-planos" className="text-sm font-semibold">
        Seus planos
      </h2>

      {children}

      {erro && (
        // `role="alert"`: ao contrario da semana sem dia bom — que e um
        // resultado valido (ADR 0011) —, isto e uma falha de verdade, e a
        // lista que nao apareceu pode ter planos dentro.
        <p role="alert" className="text-[12px] text-ink-2">
          {erro}
        </p>
      )}

      {cruzados === null && !erro && (
        <p role="status" className="text-[12px] text-ink-2">
          Carregando seus planos…
        </p>
      )}

      {cruzados !== null && <Lista cruzados={cruzados} rotulos={rotulos} onApagar={onApagar} />}
    </section>
  );
}

/**
 * O convite para quem nao tem conta, no lugar da faixa.
 *
 * **Diz o que se ganha**, e nao so "entre": um convite que nao nomeia o que ha
 * do outro lado pede um cadastro em troca de nada. As duas frases sao o que a
 * conta acrescenta a esta pagina — guardar planos, e ve-los cruzados com a
 * aptidao —, e nao uma promessa generica sobre o app.
 *
 * **Os links preservam a cidade**, com `useComCidade()`. Sem isso, quem
 * entrasse a partir do Calendario de Belem voltaria para o app sem cidade
 * nenhuma e teria de busca-la de novo — e o cabecalho ja toma exatamente este
 * cuidado nos seus dois links (ver `navegacao.tsx`).
 */
function Convite() {
  const comCidade = useComCidade();

  return (
    <section
      aria-labelledby="titulo-do-convite"
      className="flex flex-col gap-2 rounded-card bg-card p-[18px] shadow-card"
    >
      <h2 id="titulo-do-convite" className="text-sm font-semibold">
        Seus planos
      </h2>
      <p className="text-[12px] leading-relaxed text-ink-2">
        Com uma conta, voce anota o que pretende fazer em cada dia — lavar as
        cortinas na terca, viajar no feriado — e ve, ao lado de cada plano, se o
        tempo daquele dia colabora.
      </p>
      {/* A grade continua ali, e a frase diz isso: sem ela, o convite se leria
          como "entre para usar a pagina", que e falso — a previsao e a aptidao
          sao publicas e nao dependem de conta nenhuma. */}
      <p className="text-[11px] text-ink-3">
        A previsao e a aptidao ao lado sao publicas: voce nao precisa de conta
        para le-las.
      </p>
      <div className="mt-1 flex flex-wrap gap-2">
        <Link
          to={comCidade(CAMINHO_ENTRADA)}
          className="rounded-full bg-brand px-3.5 py-2 text-[12px] font-medium text-white outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-brand/40"
        >
          Entrar
        </Link>
      </div>
    </section>
  );
}

/**
 * A lista, em dois grupos: os que vem e os que ja passaram.
 *
 * O agrupamento e a politica do ADR 0012. **O titulo do grupo e o canal que
 * carrega a distincao** — a opacidade reforca para quem varre a faixa com os
 * olhos, mas nao sobrevive ao leitor de tela nem ao daltonismo, e por isso nao
 * pode estar sozinha.
 *
 * Duas listas e nao uma com separador: sao dois `<ul>` sob dois titulos, o que
 * da a quem navega por leitor de tela a contagem de cada grupo e a chance de
 * pular o passado inteiro.
 */
function Lista({
  cruzados,
  rotulos,
  onApagar,
}: {
  cruzados: PlanoCruzado[];
  rotulos: JulgamentoDeAptidao[];
  onApagar: (plano: Plano) => void;
}) {
  const passados = cruzados.filter(jaPassou);
  const proximos = cruzados.filter((cruzado) => !jaPassou(cruzado));

  if (cruzados.length === 0) {
    /*
      Conta sem plano nenhum: **como criar o primeiro**, e nao "nenhum plano".

      A frase diz o gesto — clicar num dia — porque a criacao nao tem botao
      proprio em lugar nenhum da pagina: ela mora no detalhe do dia, e quem
      nunca abriu um dia nao tem como descobrir isso olhando a faixa vazia.
    */
    return (
      <p className="text-[12px] leading-relaxed text-ink-2">
        Voce ainda nao tem planos. Clique num dia da grade e crie o primeiro
        ali — o dia vem do dia que voce escolheu.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {proximos.length > 0 && (
        <ul className="flex flex-col gap-2">
          {proximos.map((cruzado) => (
            <Item
              key={cruzado.plano.id}
              cruzado={cruzado}
              rotulos={rotulos}
              onApagar={onApagar}
            />
          ))}
        </ul>
      )}

      {passados.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-wide text-ink-3">
            Ja passaram
          </h3>
          <ul className="flex flex-col gap-2">
            {passados.map((cruzado) => (
              <Item
                key={cruzado.plano.id}
                cruzado={cruzado}
                rotulos={rotulos}
                onApagar={onApagar}
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Um plano na faixa: titulo, dia, atividade e a aptidao daquele dia.
 *
 * **Os quatro juntos sao o item**, e nao tres mais um enfeite: e o cruzamento
 * que justifica a pagina existir, e um plano sem a aptidao ao lado seria uma
 * lista de tarefas que nao precisa de previsao do tempo para funcionar.
 */
function Item({
  cruzado,
  rotulos,
  onApagar,
}: {
  cruzado: PlanoCruzado;
  rotulos: JulgamentoDeAptidao[];
  onApagar: (plano: Plano) => void;
}) {
  const { plano } = cruzado;
  const passou = jaPassou(cruzado);
  const rotulo = rotuloDaAtividade(plano.atividade, rotulos);

  return (
    <li
      className={`flex flex-col gap-1.5 rounded-inner border p-2.5 ${
        /*
          O esmaecimento do ADR 0012 — **reforco**, nunca o unico sinal: o
          titulo "Ja passaram" acima do grupo e o "ja passou" no anuncio ja
          dizem o mesmo sem depender de cor nem de opacidade.

          **Nao e `opacity`**, e a diferenca foi medida. `opacity-60` no item
          inteiro multiplica todo texto dentro dele contra o fundo, e o
          resultado reprovava fundo: 4,18:1 no titulo, 2,33:1 na linha de data
          e atividade e **1,68:1** na frase da aptidao, no tema claro — o
          ultimo quase invisivel.

          O erro estava em tratar "esmaecido" como uma propriedade do item,
          quando o que o ADR pede e que ele pareca secundario **sem deixar de
          ser legivel**. Um plano de ontem nao e um rascunho: a pessoa o criou,
          e ela precisa conseguir le-lo para decidir apaga-lo.

          O que ficou: fundo levemente recuado e borda apagada — o item inteiro
          um degrau atras —, com o **texto intacto**. E a mesma solucao que a
          celula do horizonte longo ja usa na grade, e pelo mesmo motivo: a
          distincao vive na moldura, nao na tinta do texto.
        */
        passou ? "border-line/50 bg-ink/[0.03]" : "border-line"
      }`}
    >
      {/*
        O anuncio completo, como `sr-only`.

        A issue pede cada plano anunciado com titulo, dia, atividade **e
        aptidao**, e o conteudo visivel abaixo esta espalhado em tres linhas
        que o leitor leria como fragmentos soltos — "Lavar as cortinas", "22 de
        set", "boa". A frase montada e o que torna o item legivel de ouvido, e e
        o mesmo padrao que a celula da grade ja usa.
      */}
      <span className="sr-only">
        {anuncioDoPlano(cruzado, rotulo)}
      </span>

      {/*
        `aria-hidden` no **titulo**, e nunca no `<div>` que o envolve: o botao
        de apagar e irmao dele, e esconder a linha inteira tiraria o controle
        da arvore de acessibilidade junto com o texto. O item ficaria sem
        nenhuma forma de ser apagado por leitor de tela — o requisito de apagar
        sem mouse falha exatamente assim, sem aparecer no compilador nem no
        lint. Foi o que o navegador pegou.

        O que se esconde e so a duplicacao: o titulo ja esta na frase do
        `sr-only` acima. O botao nao esta em frase nenhuma, porque ele nao e
        texto — e a acao.
      */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-medium leading-snug" aria-hidden="true">
          {plano.titulo}
        </p>
        <BotaoApagar plano={plano} onApagar={onApagar} />
      </div>

      <div
        className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-[11px] text-ink-2"
        aria-hidden="true"
      >
        <span>{diaEMes(plano.dia)}</span>
        <span>·</span>
        <span>{rotulo}</span>
      </div>

      <AptidaoDoPlano cruzado={cruzado} />
    </li>
  );
}

/**
 * A aptidao ao lado do plano — ou a razao de nao haver nenhuma.
 *
 * **Os tres casos de ausencia dizem coisas diferentes**, e e por isso que
 * `posicao` existe. Um espaco em branco no lugar da aptidao se leria como
 * falha de carregamento, que e o mesmo defeito que a nota da fronteira do dia
 * 8 existe para evitar na grade.
 */
function AptidaoDoPlano({ cruzado }: { cruzado: PlanoCruzado }) {
  const { julgamento, posicao } = cruzado;

  if (julgamento) {
    return (
      <p
        className={`text-[12px] font-semibold ${COR_DO_NIVEL[julgamento.nivel]}`}
        aria-hidden="true"
      >
        {PALAVRA[julgamento.nivel]}
        {/* O motivo so existe no nivel `ruim`, e aqui ele cabe: a faixa e uma
            coluna, e nao sete celulas de 104 px. E o que transforma "ruim"
            em algo sobre o que decidir. */}
        {julgamento.motivo && (
          <span className="ml-1.5 font-normal text-ink-2">
            {julgamento.motivo.texto}
          </span>
        )}
      </p>
    );
  }

  /*
    `ink-2` e nao `ink-3`, e a diferenca foi **medida no navegador**.

    `ink-3` e a cor de apoio mais clara do tema, e aqui ela reprovava: 2,54:1 no
    claro e 3,57:1 no escuro sobre o fundo do cartao, os dois abaixo de 4,5:1.
    Com `ink-2` sao 4,83:1 e 7,07:1.

    E a mesma mordida que a fatia 06 levou duas vezes — cinza claro sobre um
    fundo que ninguem mediu —, e a licao que ficou dela e a que se aplica aqui:
    **estas frases nao sao decoracao.** Elas sao a unica coisa que o item diz
    sobre o tempo daquele dia, e um texto que explica uma ausencia precisa ser
    tao legivel quanto o que ele substitui.
  */
  return (
    <p className="text-[11px] text-ink-2" aria-hidden="true">
      {FRASE_SEM_APTIDAO[posicao]}
    </p>
  );
}

/**
 * O que a faixa diz quando nao ha aptidao — uma frase por motivo.
 *
 * `curto` nunca chega aqui com `julgamento` nulo na pratica (todo dia do
 * horizonte curto tem as quatro aptidoes), mas o caso existe no tipo e uma
 * frase honesta e melhor que um `?? ""` que produziria o branco que este mapa
 * evita.
 */
const FRASE_SEM_APTIDAO: Record<PlanoCruzado["posicao"], string> = {
  // ADR 0012: a previsao daquele dia ja nao existe, e o app nao a guardou.
  passado: "Sem aptidao: o dia ja passou.",
  distante: "Longe demais para julgar o tempo.",
  fora_do_horizonte: "Fora dos proximos dezesseis dias.",
  curto: "Sem aptidao para este dia.",
};

/**
 * O nome da atividade para exibir, **do backend**.
 *
 * O `rotulo` vem junto de cada julgamento (`JulgamentoDeAptidao.rotulo`), e
 * escrever um mapa de `Atividade` para texto aqui criaria o segundo lugar que
 * precisaria concordar com o backend na hora de renomear uma atividade — que e
 * exatamente o que aquele campo existe para evitar.
 *
 * O `??` cobre o caso em que a grade ainda nao chegou (nao ha rotulo nenhum) ou
 * falhou: a faixa **nao depende da grade para aparecer**, e um plano sem nome
 * de atividade e pior que o identificador cru. Sao requisicoes independentes, e
 * a lista de planos pode chegar primeiro.
 */
function rotuloDaAtividade(
  atividade: Atividade,
  rotulos: JulgamentoDeAptidao[],
): string {
  return rotulos.find((j) => j.atividade === atividade)?.rotulo ?? atividade;
}

/**
 * A frase que o leitor de tela ouve no lugar das tres linhas visiveis.
 *
 * Data **por extenso** e nao "22 de set": quem ouve chega ao item sem o
 * contexto da grade ao lado, e a mesma razao ja valeu para a celula do dia.
 */
function anuncioDoPlano(cruzado: PlanoCruzado, rotulo: string): string {
  const { plano, julgamento, posicao } = cruzado;
  const partes = [plano.titulo, dataPorExtenso(plano.dia), rotulo];

  if (posicao === "passado") partes.push("ja passou");

  partes.push(
    julgamento
      ? `${ANUNCIO[julgamento.nivel]} ${rotulo.toLowerCase()}`
      : FRASE_SEM_APTIDAO[posicao],
  );

  if (julgamento?.motivo) partes.push(julgamento.motivo.texto);

  return partes.join(", ");
}

/**
 * Apagar, com confirmacao — e a confirmacao e **no proprio item**.
 *
 * Nao e `window.confirm`: ele nao herda o tema, nao e estilizavel e desloca o
 * foco para fora do documento. Nao e um segundo dialogo, porque ja ha um na
 * pagina (o detalhe do dia) e empilhar camadas para confirmar uma linha e
 * desproporcional ao que se arrisca.
 *
 * O item vira a sua propria pergunta: "Apagar?" com **Apagar** e **Cancelar**
 * lado a lado. O foco nunca sai do item, entao quem navega por teclado confirma
 * ou desiste sem procurar para onde a pagina o mandou — que e o requisito de
 * apagar sem mouse.
 *
 * `Escape` cancela, pelo mesmo reflexo que o detalhe do dia ja ensina na mesma
 * pagina.
 */
function BotaoApagar({
  plano,
  onApagar,
}: {
  plano: Plano;
  onApagar: (plano: Plano) => void;
}) {
  const [confirmando, setConfirmando] = useState(false);

  if (!confirmando) {
    return (
      <button
        type="button"
        onClick={() => setConfirmando(true)}
        // O rotulo nomeia **qual** plano: "Apagar" sozinho, repetido em doze
        // itens, da ao leitor de tela doze botoes indistinguiveis.
        aria-label={`Apagar o plano ${plano.titulo}`}
        className="shrink-0 rounded-lg px-1.5 py-0.5 text-[11px] text-ink-3 outline-none transition-colors hover:text-ink focus-visible:ring-2 focus-visible:ring-brand/40"
      >
        Apagar
      </button>
    );
  }

  return (
    <span
      className="flex shrink-0 items-center gap-1"
      onKeyDown={(evento) => {
        if (evento.key === "Escape") setConfirmando(false);
      }}
    >
      <span className="text-[11px] text-ink-2">Apagar?</span>
      <button
        type="button"
        // O foco entra na confirmacao assim que ela aparece: sem isto, quem
        // apertou "Apagar" pelo teclado ficaria com o foco num botao que
        // acabou de sair do DOM, e o `Tab` seguinte recomecaria do topo.
        ref={(elemento) => elemento?.focus()}
        onClick={() => onApagar(plano)}
        aria-label={`Confirmar apagar o plano ${plano.titulo}`}
        className="rounded-lg bg-brand px-2 py-0.5 text-[11px] font-medium text-white outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-brand/40"
      >
        Apagar
      </button>
      <button
        type="button"
        onClick={() => setConfirmando(false)}
        aria-label={`Cancelar apagar o plano ${plano.titulo}`}
        className="rounded-lg px-1.5 py-0.5 text-[11px] text-ink-2 outline-none transition-colors hover:text-ink focus-visible:ring-2 focus-visible:ring-brand/40"
      >
        Cancelar
      </button>
    </span>
  );
}
