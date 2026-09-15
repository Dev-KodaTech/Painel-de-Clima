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
 * A spec chama esta a **unica** costura da entrega: dado um conjunto de
 * vizinhas, o que sai e em que ordem. O frontend deste repo nao tem suite de
 * testes — decisao do ticket 12 do esforco original, que esta pagina nao
 * inverte de carona —, entao a costura fica preparada e nao exercitada: no dia
 * em que o repo decidir testar o frontend, o alvo ja esta aqui, sem componente
 * nem contexto de rota em volta.
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
 * As linhas na ordem de exibicao: a cidade escolhida, depois as vizinhas.
 *
 * A ordem das vizinhas e a que o backend entrega — da mais perto para a mais
 * longe —, e por isso nao ha `sort` aqui: reordenar por `distance_km` daria o
 * mesmo resultado com uma chance a mais de errar.
 *
 * A escolhida vem primeiro por ser a origem. O ticket 03 acrescenta o criterio
 * de ordenacao; a assinatura ja e a que ele precisa, e e por isso que esta
 * funcao existe separada da tabela desde agora.
 */
export function linhasDaTabela(
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
 * A diferenca importa **a partir do ticket 03**: enquanto a ordem e fixa, uma
 * chave repetida so avisa no console; com a tabela reordenavel, e o React
 * reaproveitando a linha errada — a cidade que muda de lugar leva consigo o
 * estado da outra.
 */
export function chaveDaLinha(linha: Linha): string {
  return `${linha.latitude},${linha.longitude}`;
}
