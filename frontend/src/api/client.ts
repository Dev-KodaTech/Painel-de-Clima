/**
 * Acesso ao backend proprio. O frontend nunca fala com a Open-Meteo.
 *
 * Toda falha vira `ErroDoPainel`, com uma mensagem ja legivel para exibir —
 * nenhum componente precisa interpretar status HTTP.
 */

import type {
  Cidade,
  CidadeDoPainel,
  CidadesResponse,
  Janela,
  TrendsResponse,
  WeatherResponse,
} from "./types";

export class ErroDoPainel extends Error {}

/**
 * A mensagem a exibir para uma falha qualquer.
 *
 * Saber que `ErroDoPainel` carrega texto pronto e conhecimento desta camada;
 * os componentes so pedem "o que eu mostro?" e recebem uma frase.
 */
export function mensagemDeErro(falha: unknown, padrao: string): string {
  return falha instanceof ErroDoPainel ? falha.message : padrao;
}

const MSG_GENERICA =
  "Nao foi possivel falar com o servico. Verifique sua conexao e tente de novo.";

/**
 * O texto de um `detail`, que **nem sempre e texto**.
 *
 * Os erros que o backend levanta de proposito mandam uma frase pronta em
 * `detail` — "a API externa esta fora do ar". Mas o 422 nao e levantado por
 * ele: quem o monta e o FastAPI, e ali `detail` e uma **lista de objetos** de
 * validacao (`[{type, loc, msg, ...}]`).
 *
 * Tipar o campo como `string` nao o tornava uma: a lista chegava, era truthy,
 * passava pelo `??` e ia inteira para a tela como
 * `[object Object],[object Object]` — que e o que a pessoa via ao abrir um link
 * com a coordenada corrompida. Dai o parametro ser `unknown`: a forma do
 * `detail` e decidida aqui, olhando o valor, e nao por uma anotacao que o JSON
 * nao e obrigado a respeitar.
 *
 * A lista vira a primeira `msg`, e nao todas concatenadas: duas coordenadas
 * invalidas produzem duas entradas quase identicas, e a segunda nao acrescenta
 * nada a quem le.
 */
function textoDoDetalhe(detalhe: unknown): string | undefined {
  if (typeof detalhe === "string") return detalhe;
  if (Array.isArray(detalhe)) {
    const primeira = detalhe.find(
      (item): item is { msg: string } =>
        typeof (item as { msg?: unknown })?.msg === "string",
    );
    return primeira?.msg;
  }
  return undefined;
}

async function pegar<T>(caminho: string, sinal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(caminho, { signal: sinal });
  } catch (erro) {
    // Um fetch abortado nao e falha: deixa o chamador distingui-lo.
    if (erro instanceof DOMException && erro.name === "AbortError") throw erro;
    throw new ErroDoPainel(MSG_GENERICA);
  }

  if (!response.ok) {
    // O backend manda `detail` com texto pronto para exibir (503 da API
    // externa fora do ar, por exemplo).
    const detalhe = await response
      .json()
      .then((corpo: { detail?: unknown }) => textoDoDetalhe(corpo.detail))
      .catch(() => undefined);
    throw new ErroDoPainel(detalhe ?? MSG_GENERICA);
  }

  return (await response.json()) as T;
}

/** Candidatas para um termo de busca. Lista vazia = cidade nao encontrada. */
export async function buscarCidades(
  q: string,
  sinal?: AbortSignal,
): Promise<Cidade[]> {
  const corpo = await pegar<CidadesResponse>(
    `/api/cities?q=${encodeURIComponent(q)}`,
    sinal,
  );
  return corpo.results;
}

/**
 * A cidade de uma coordenada, ou `null` se nao houver nenhuma perto.
 *
 * `null` e resposta normal, nao falha: acima de 50 km da cidade mais proxima o
 * backend nao sugere nada, e o painel fica no estado inicial. Sugerir Alice
 * Springs a quem esta a 341 km dela seria pior que o silencio.
 */
export async function buscarCidadePorCoordenada(
  latitude: number,
  longitude: number,
  sinal?: AbortSignal,
): Promise<Cidade | null> {
  const params = new URLSearchParams({
    lat: String(latitude),
    lon: String(longitude),
  });
  const corpo = await pegar<CidadesResponse>(`/api/cities?${params}`, sinal);
  return corpo.results[0] ?? null;
}

/** O painel de uma cidade ja escolhida. */
export async function buscarPainel(
  cidade: CidadeDoPainel,
  sinal?: AbortSignal,
): Promise<WeatherResponse> {
  const params = new URLSearchParams({
    latitude: String(cidade.latitude),
    longitude: String(cidade.longitude),
    name: cidade.name,
    country: cidade.country,
    country_code: cidade.country_code,
  });
  if (cidade.admin1) params.set("admin1", cidade.admin1);

  return pegar<WeatherResponse>(`/api/weather?${params}`, sinal);
}

/**
 * O historico climatologico de uma cidade, para uma janela temporal.
 *
 * Endpoint proprio, separado de `/api/weather`: as outras cinco paginas nao
 * leem nada disto, e o custo do arquivo nao deve recair sobre quem so abriu a
 * Visao geral.
 *
 * So a coordenada viaja — nada aqui exibe o nome da cidade, que o cabecalho ja
 * tem do painel.
 */
export async function buscarHistorico(
  cidade: Pick<CidadeDoPainel, "latitude" | "longitude">,
  janela: Janela,
  sinal?: AbortSignal,
): Promise<TrendsResponse> {
  const params = new URLSearchParams({
    latitude: String(cidade.latitude),
    longitude: String(cidade.longitude),
    janela,
  });

  return pegar<TrendsResponse>(`/api/trends?${params}`, sinal);
}
