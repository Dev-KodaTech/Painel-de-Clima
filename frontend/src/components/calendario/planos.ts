/**
 * O cruzamento que justifica a pagina existir: o plano ao lado da aptidao.
 *
 * O plano diz **o que voce quer fazer**; a aptidao daquele dia para aquela
 * atividade diz **se o tempo colabora**. Nenhum dos dois sozinho e a pagina —
 * a faixa sem aptidao seria uma lista de tarefas, e a grade sem planos e o que
 * a fatia 06 ja entregava.
 *
 * ## Por que o cruzamento mora aqui, e nao no backend
 *
 * O `/api/planos` **nao** devolve clima, e isso e regra do verbete *Plano*:
 * clima guardado envelhece, e alguem veria a previsao de anteontem sem saber
 * que e de anteontem. A pagina ja buscou os dezesseis dias para desenhar a
 * grade, entao o cruzamento e um `find` sobre dado fresco que ja esta em maos
 * — e nao uma segunda busca, nem uma coluna no banco.
 *
 * ## A consequencia menos obvia de a pagina ser mista
 *
 * **Trocar de cidade nao mexe nos planos — mas mexe na aptidao ao lado
 * deles.** Os planos sao da conta e nao da cidade: a mesma lista aparece em
 * Sao Paulo e em Belem, porque quem planejou lavar roupa na terca planejou
 * isso uma vez. O que muda e o julgamento: terca serve para lavar roupa em Sao
 * Paulo e nao serve em Belem, e a faixa passa a dizer isso sem que plano algum
 * tenha sido tocado.
 *
 * E o unico lugar do app em que um mesmo dado exibido responde a duas fontes
 * de estado ao mesmo tempo — a conta, que o possui, e a URL, que decide como
 * ele e julgado. Ver o verbete *Pagina* do `CONTEXT.md`.
 */

import type { DiaDoHorizonte, JulgamentoDeAptidao, Plano } from "../../api/types";
import { julgamentoDe } from "./aptidao";

/**
 * Um plano ja cruzado com o dia que a grade carregou.
 *
 * `julgamento` e `null` em **tres** casos que a faixa trata de modos
 * diferentes, e por isso o motivo da ausencia vem junto em `posicao` em vez de
 * ser reconstruido por quem exibe:
 *
 * - o dia ja passou (`passado`);
 * - o dia esta no horizonte longo, alem do dia 8 (`distante`);
 * - o dia esta fora dos dezesseis (`fora_do_horizonte`).
 *
 * Sem `posicao`, a faixa teria de refazer a mesma comparacao de datas para
 * saber qual frase dizer — e as duas contas divergiriam na primeira vez que
 * uma delas ganhasse um caso.
 */
export type PlanoCruzado = {
  plano: Plano;
  /**
   * A aptidao daquele dia para aquela atividade, ou `null`.
   *
   * **So existe no horizonte curto**, que e onde a aptidao existe: o dia 12
   * nao tem julgamento nenhum a dar (ADR 0010), e inventar um "desconhecido"
   * aqui faria a faixa exibir um nivel que o backend nao afirmou.
   */
  julgamento: JulgamentoDeAptidao | null;
  posicao: PosicaoDoPlano;
};

/**
 * Onde o dia do plano cai em relacao a grade carregada.
 *
 * **Quatro estados e nao um booleano**, porque cada um pede uma frase
 * diferente na faixa: "ja passou" nao e "longe demais para julgar", e nenhum
 * dos dois e "fora dos dezesseis dias". Colapsa-los faria a faixa dizer a
 * mesma coisa sobre um plano de ontem e um plano de dezembro.
 */
export type PosicaoDoPlano =
  | "passado"
  | "curto"
  | "distante"
  | "fora_do_horizonte";

/**
 * Cruza os planos com os dias da grade.
 *
 * `hoje` vem de fora, e nao de `new Date()` aqui dentro, por duas razoes que
 * apontam para o mesmo lugar: a funcao fica testavel sem relogio falso, e
 * **hoje e o primeiro dia da grade** — a data da cidade consultada, que o
 * backend montou no fuso dela. Lido do relogio do browser, quem esta em Sao
 * Paulo consultando Toquio compararia o plano contra o dia errado. E a mesma
 * regra que o `Cabecalho` ja segue ao nao exibir a data local enquanto o
 * painel nao carrega.
 *
 * A ordem da lista e **preservada como veio** — o backend ja a entrega por dia
 * (`ORDER BY dia, id`), e reordenar aqui seria manter a mesma regra em dois
 * lugares. O agrupamento de passados e visual, e quem o faz e a faixa.
 */
export function cruzarPlanos(
  planos: Plano[],
  dias: DiaDoHorizonte[],
  hoje: string | null,
): PlanoCruzado[] {
  return planos.map((plano) => {
    const dia = dias.find((candidato) => candidato.date === plano.dia) ?? null;

    return {
      plano,
      // O julgamento sai do **mesmo** `julgamentoDe` que pinta a celula da
      // grade, e nao de um `find` proprio: o plano de terca para lavar roupa e
      // a celula de terca pintada de verde precisam dizer a mesma coisa, ou a
      // faixa e a grade se contradizem na mesma tela.
      julgamento: dia ? julgamentoDe(dia, plano.atividade) : null,
      posicao: posicaoDe(plano.dia, dia, hoje),
    };
  });
}

/**
 * Onde um dia cai, decidido pela data e nao pela presenca na grade.
 *
 * A ordem dos casos importa: **passado vence tudo**. Um plano de ontem nao
 * esta na grade (ela comeca hoje), entao sem este caso primeiro ele cairia em
 * `fora_do_horizonte` e a faixa diria "fora dos proximos dezesseis dias" sobre
 * um dia que ja aconteceu — verdadeiro e inutil.
 *
 * A comparacao e de **string**, e e deliberada: as duas datas sao `AAAA-MM-DD`
 * e nesse formato a ordem lexicografica e a cronologica. E a regra do
 * `formato.ts` — datas do payload sao hora de parede da cidade, fatiadas como
 * texto e nunca parseadas —, e ela evita exatamente o erro que um `new Date()`
 * introduziria aqui: `new Date("2026-09-22")` e meia-noite **UTC**, que em Sao
 * Paulo e o dia 21 as 21h.
 */
function posicaoDe(
  diaDoPlano: string,
  naGrade: DiaDoHorizonte | null,
  hoje: string | null,
): PosicaoDoPlano {
  if (hoje !== null && diaDoPlano < hoje) return "passado";
  if (naGrade === null) return "fora_do_horizonte";
  return naGrade.horizonte === "longo" ? "distante" : "curto";
}

/**
 * Os planos de um dia — o que a grade precisa para marcar a celula.
 *
 * Um `Set` de datas, e nao uma busca por celula: a grade tem dezesseis celulas
 * e a conta pode ter dezenas de planos, e um `find` por celula percorreria a
 * lista dezesseis vezes para responder uma pergunta que um conjunto responde
 * de uma. **Datas e nao contagem**: a marca na celula diz "ha plano aqui", e
 * nao quantos — a faixa ao lado e que lista.
 */
export function diasComPlano(planos: Plano[]): Set<string> {
  return new Set(planos.map((plano) => plano.dia));
}

/**
 * Se o plano ja passou, para a faixa agrupa-lo separadamente.
 *
 * Existe como funcao nomeada, e nao como `posicao === "passado"` espalhado,
 * porque a faixa faz a pergunta em tres pontos — ao separar os dois grupos
 * (duas vezes, uma por grupo) e ao decidir se o item se esmaece. Um literal
 * repetido em tres lugares e o que sobrevive a um rename de `posicao` sem
 * quebrar a compilacao, e ai um dos tres passa a mentir em silencio.
 *
 * Quem **nao** a chama e a exibicao de aptidao: la o que decide e `julgamento`
 * ser nulo, e a frase da ausencia sai de `posicao` — o passado e so um dos
 * tres motivos de nao haver julgamento, e trata-lo a parte duplicaria a regra.
 */
export function jaPassou(cruzado: PlanoCruzado): boolean {
  return cruzado.posicao === "passado";
}
