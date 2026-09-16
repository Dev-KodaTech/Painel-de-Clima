/**
 * As linhas da tabela comparativa: a cidade escolhida mais as vizinhas.
 *
 * ## Por que a cidade escolhida nao e uma `Nearby`
 *
 * Seria conveniente empurra-la para dentro da lista de vizinhas e tratar seis
 * linhas iguais. Mas `Nearby.distance_km` e um numero obrigatorio, e a unica
 * distancia que a cidade escolhida poderia levar e `0` — que e exatamente a
 * mentira que o `CONTEXT.md` e o ADR 0006 mandam evitar: distancia de si mesma
 * e tautologia, e um "0 km" na coluna se leria como um dado medido.
 *
 * Dai `Linha.distancia_km` ser `number | null`. O nulo nao e "faltou o dado" —
 * e "esta cidade e a origem de quem as distancias sao medidas". Sendo tipo, a
 * celula vazia deixa de depender de alguem lembrar de tratar o caso: o
 * compilador cobra.
 *
 * A mesma `Linha` carrega `ehEscolhida`, e nao se deduz o destaque de
 * `distancia_km === null`. Sao duas perguntas diferentes — "como formatar esta
 * celula" e "esta linha e a referencia" — e o dia em que uma vizinha chegar sem
 * distancia elas deixariam de coincidir.
 *
 * ## Funcao pura, exportada, com a tabela do lado de fora
 *
 * A spec chama `ordenarLinhas`, no fim deste arquivo, a **unica** costura da
 * entrega: dado um conjunto de vizinhas e um criterio, o que sai e em que
 * ordem. E a unica logica desta pagina que pode estar errada — o resto e
 * marcacao.
 *
 * O frontend deste repo nao tem suite de testes — decisao do ticket 12 do
 * esforco original, que esta pagina nao inverte de carona —, entao a costura
 * fica preparada e nao exercitada: no dia em que o repo decidir testar o
 * frontend, o alvo ja esta aqui, sem componente nem contexto de rota em volta.
 */

import type { Current, Location, Nearby } from "../../api/types";

/**
 * Uma linha da tabela, ja no formato que a tabela desenha.
 *
 * Os campos sao os do payload e nao os da tela: a formatacao (unidade,
 * separador de milhar) e do `formato.ts`, e fazer a ordenacao devolver texto
 * impediria ordenar por temperatura no ticket 03 — "9 °C" ordena depois de
 * "24 °C".
 */
export type Linha = {
  nome: string;
  country_code: string;
  /**
   * A coordenada exata, que **identifica** a linha — nao se exibe.
   *
   * E o unico campo que distingue duas cidades homonimas do mesmo pais com
   * certeza: `distancia_km` vem arredondada ao inteiro, e duas homonimas que
   * caiam no mesmo quilometro teriam a mesma chave. Chegou ao payload no
   * ticket 01, sem arredondamento, para o mapa do ticket 04.
   */
  latitude: number;
  longitude: number;
  /** `null` **so** na cidade escolhida: ver o cabecalho deste arquivo. */
  distancia_km: number | null;
  temperatura: number;
  descricao: string;
  icone: string;
  /** A referencia de quem as distancias sao medidas, nao um resultado. */
  ehEscolhida: boolean;
};

/**
 * A cidade escolhida como linha da tabela.
 *
 * Os dados vem de dois blocos do painel — `location` tem o nome e o pais,
 * `current` tem o clima —, porque o payload nunca precisou descrever a cidade
 * escolhida do jeito que descreve uma vizinha. Juntar os dois aqui e o que
 * torna as seis linhas comparaveis.
 */
function daEscolhida(location: Location, current: Current): Linha {
  return {
    nome: location.name,
    country_code: location.country_code,
    latitude: location.latitude,
    longitude: location.longitude,
    distancia_km: null,
    temperatura: current.temperature,
    descricao: current.description,
    icone: current.icon,
    ehEscolhida: true,
  };
}

/** Uma cidade vizinha como linha da tabela. */
function daVizinha(vizinha: Nearby): Linha {
  return {
    nome: vizinha.name,
    country_code: vizinha.country_code,
    latitude: vizinha.latitude,
    longitude: vizinha.longitude,
    distancia_km: vizinha.distance_km,
    temperatura: vizinha.temperature,
    descricao: vizinha.description,
    icone: vizinha.icon,
    ehEscolhida: false,
  };
}

/**
 * As linhas antes de ordenar: a cidade escolhida, depois as vizinhas.
 *
 * A ordem aqui e a que o backend entrega — da mais perto para a mais longe —,
 * e por isso nao ha `sort`: e a ordem de origem, e quem a reordena e
 * `ordenarLinhas`. Sendo a ordem de origem, e tambem o desempate de
 * `ordenarLinhas`, que e o que torna a ordenacao estavel.
 *
 * A escolhida vem primeiro por ser a origem de quem as distancias sao medidas.
 *
 * Interna: quem sai deste arquivo e `ordenarLinhas`, que e a costura que a spec
 * nomeia. Esta funcao foi exportada enquanto a tabela ainda nao ordenava e a
 * tabela a chamava direto; exporta-la agora seria oferecer um segundo jeito de
 * montar as mesmas linhas, sem a ordem.
 */
function linhasDaTabela(
  location: Location,
  current: Current,
  nearby: Nearby[],
): Linha[] {
  return [daEscolhida(location, current), ...nearby.map(daVizinha)];
}

/**
 * A chave de uma linha: a sua coordenada.
 *
 * E a identidade de uma cidade, e nao uma aproximacao dela. O painel da Visao
 * geral usa `nome-pais-distancia` porque so tinha isso — a coordenada chegou ao
 * payload no ticket 01 —, e ali a distancia arredondada ao inteiro deixa duas
 * homonimas do mesmo pais colidirem no mesmo quilometro.
 *
 * A diferenca importa agora que a tabela reordena: com ordem fixa, uma chave
 * repetida so avisa no console; reordenando, e o React reaproveitando a linha
 * errada — a cidade que muda de lugar leva consigo o estado da outra.
 */
export function chaveDaLinha(linha: Linha): string {
  return `${linha.latitude},${linha.longitude}`;
}

/**
 * Por qual criterio a tabela esta ordenada.
 *
 * Uniao fechada e nao `string`, como `Janela`: sao os dois criterios que fazem
 * sentido nesta tabela, e um terceiro inventado nao compila.
 */
export type Criterio = "temperatura" | "distancia";

/**
 * Tudo o que distingue um criterio do outro, num lugar so.
 *
 * ## Por que os tres campos moram juntos
 *
 * Cada criterio tem uma **direcao**, e ela aparecia em tres lugares: o sinal da
 * comparacao em `ordenarLinhas`, o valor de `aria-sort` no cabecalho e o
 * triangulo ao lado do rotulo. Tres decisoes sobre a mesma coisa, em dois
 * arquivos, que precisavam concordar por vigilancia — e um `aria-sort`
 * discordando da ordem real e pior que anuncio nenhum, porque afirma com
 * confianca o que nao e verdade.
 *
 * Juntos aqui, a concordancia deixa de ser vigilancia e passa a ser estrutura:
 * a ordem, o anuncio e o glifo saem todos da mesma linha desta tabela.
 *
 * ## `Record<Criterio, ...>` e nao uma lista
 *
 * O compilador cobra uma entrada para **todo** criterio, e a consulta e total —
 * nao devolve `undefined` nem precisa de assercao. Acrescentar um terceiro
 * criterio a uniao quebra a compilacao aqui, que e exatamente onde deve
 * quebrar: no lugar em que se decide o que o criterio novo significa.
 */
export const CRITERIOS: Record<
  Criterio,
  {
    /** O rotulo da coluna que ordena por este criterio. */
    rotulo: string;
    /**
     * `1` para crescente, `-1` para decrescente: o multiplicador da comparacao
     * em `ordenarLinhas`.
     *
     * A distancia cresce — a mais proxima primeiro, que e a ordem em que o
     * backend ja entrega. A temperatura decresce, porque a pergunta que motiva
     * ordenar por temperatura e "onde esta mais quente agora".
     */
    sentido: 1 | -1;
    /** Como um leitor de tela anuncia a coluna ordenada por este criterio. */
    anuncio: "ascending" | "descending";
    /** O mesmo que `anuncio` diz a quem ouve, para quem enxerga. */
    glifo: string;
  }
> = {
  distancia: {
    rotulo: "Distancia",
    sentido: 1,
    anuncio: "ascending",
    glifo: "▲",
  },
  temperatura: {
    rotulo: "Temperatura",
    sentido: -1,
    anuncio: "descending",
    glifo: "▼",
  },
};

/**
 * As linhas na ordem de exibicao, segundo o criterio escolhido.
 *
 * ## Por que a cidade escolhida muda de papel conforme o criterio
 *
 * Por **distancia** ela fica em primeiro, fora da comparacao: e a origem de
 * quem as distancias sao medidas, e `distancia_km` e `null` nela — nao ha
 * numero para ordenar. Ordenar o nulo como zero a poria em primeiro pelo motivo
 * errado, dizendo "a mais proxima" onde o certo e "o ponto de partida".
 *
 * Por **temperatura** ela entra na comparacao como qualquer outra linha, e e
 * esse o resultado interessante: descobrir que a cidade escolhida e a mais fria
 * das seis so tem sentido se ela estiver na fila. Fixa-la no topo aqui
 * responderia a pergunta errada — "onde esta mais quente" deixaria de fora
 * justamente a cidade de quem pergunta.
 *
 * ## A direcao nao se decide aqui
 *
 * O sentido de cada criterio — a temperatura decrescente, a distancia
 * crescente — vem de `CRITERIOS`, junto com o anuncio e o glifo que dizem o
 * mesmo na tela. Ver ali por que os tres moram juntos.
 *
 * ## O desempate e explicito
 *
 * Duas cidades a 18 °C empatam, e sem desempate a ordem delas ficaria por
 * conta do algoritmo de ordenacao. O `sort` do JavaScript e estavel por
 * especificacao, mas depender disso deixaria a garantia num detalhe que nao se
 * le aqui — e a garantia que o ticket pede e justamente que a mesma entrada
 * produza sempre a mesma ordem. O indice de origem resolve na propria funcao:
 * empatou, vence quem ja vinha antes, que e a ordem da distancia vinda do
 * backend.
 */
export function ordenarLinhas(
  location: Location,
  current: Current,
  nearby: Nearby[],
  criterio: Criterio,
): Linha[] {
  const linhas = linhasDaTabela(location, current, nearby);

  // O indice de origem viaja junto porque `sort` ordena no lugar e apaga a
  // ordem anterior no meio da comparacao: consultar `linhas.indexOf` la dentro
  // leria o arranjo ja meio reordenado.
  const comOrigem = linhas.map((linha, origem) => ({ linha, origem }));

  const { sentido } = CRITERIOS[criterio];

  comOrigem.sort((a, b) => {
    if (criterio === "temperatura") {
      const porTemperatura =
        sentido * (a.linha.temperatura - b.linha.temperatura);
      if (porTemperatura !== 0) return porTemperatura;
    } else {
      // A escolhida antes de qualquer vizinha, por ser a origem — e fora do
      // `sentido`, que governa a comparacao entre vizinhas e nao o lugar da
      // referencia. Comparar duas escolhidas nao acontece: ha exatamente uma.
      if (a.linha.ehEscolhida !== b.linha.ehEscolhida) {
        return a.linha.ehEscolhida ? -1 : 1;
      }
      // Aqui nenhuma das duas e a escolhida, entao nenhum `distancia_km` e
      // nulo. O `?? 0` existe para o compilador e nao para o caso: o tipo
      // permite o nulo, a ramificacao acima ja o excluiu.
      const porDistancia =
        sentido * ((a.linha.distancia_km ?? 0) - (b.linha.distancia_km ?? 0));
      if (porDistancia !== 0) return porDistancia;
    }

    return a.origem - b.origem;
  });

  return comOrigem.map(({ linha }) => linha);
}
