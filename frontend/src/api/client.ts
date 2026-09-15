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
      .then((corpo: { detail?: string }) => corpo.detail)
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
