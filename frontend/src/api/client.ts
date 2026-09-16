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
  CondicoesResponse,
  Conta,
  Janela,
  QuemSouResponse,
  TrendsResponse,
  WeatherResponse,
} from "./types";

export class ErroDoPainel extends Error {}

/**
 * A falha que **nao veio do servidor**: a requisicao nem chegou la.
 *
 * Subclasse, e nao um campo em `ErroDoPainel`, para que quem so quer a
 * mensagem continue nao sabendo da diferenca — `mensagemDeErro` seguiu
 * inalterada — e quem precisa distinguir use `instanceof`.
 *
 * As telas de conta sao as unicas que precisam: "e-mail ou senha incorretos"
 * pede para corrigir os campos, "sem conexao" pede para tentar de novo, e uma
 * so mensagem para os dois manda a pessoa conferir uma senha que estava certa.
 */
export class ErroDeRede extends ErroDoPainel {}

/**
 * O e-mail do cadastro ja tem conta — o `409` de `/api/cadastro`.
 *
 * Existe para a tela saber **qual campo** esta errado. Sem ela, o cadastro
 * recusado marcava os dois campos como invalidos, e a senha, que nao tem
 * defeito nenhum, mandava quem usa leitor de tela procurar um erro que nao
 * existe. A mensagem continua vindo do backend ("Ja existe uma conta com esse
 * e-mail. Tente entrar."), que e quem sabe o que dizer.
 */
export class EmailJaUsado extends ErroDoPainel {}

/**
 * A mensagem a exibir para uma falha qualquer.
 *
 * Saber que `ErroDoPainel` carrega texto pronto e conhecimento desta camada;
 * os componentes so pedem "o que eu mostro?" e recebem uma frase.
 */
export function mensagemDeErro(falha: unknown, padrao: string): string {
  return falha instanceof ErroDoPainel ? falha.message : padrao;
}

/**
 * A mensagem de quando a requisicao nao chegou ao servidor.
 *
 * Diz "verifique sua conexao" e nao "confira os dados", que e a diferenca que
 * importa numa tela de entrada: os dados podem estar certos. E a mesma frase
 * para toda falha sem resposta, porque o browser nao conta qual foi — DNS,
 * offline e servidor fora do ar chegam todos como o mesmo `TypeError`.
 */
const MSG_DE_REDE =
  "Nao foi possivel falar com o servico. Verifique sua conexao e tente de novo.";

/**
 * A mensagem de uma resposta de erro **sem `detail` legivel**.
 *
 * Distinta de `MSG_DE_REDE`: aqui o servidor respondeu, so nao explicou. Nao
 * manda verificar a conexao, que esta boa.
 */
const MSG_SEM_DETALHE = "O servico respondeu com um erro. Tente de novo.";

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

/**
 * Levanta o erro de uma resposta que nao deu certo.
 *
 * As duas metades do cliente — `pegar` e `enviar` — divergem no que *mandam*
 * (metodo, cabecalho, corpo) e concordam no que fazem com a recusa. Esta
 * funcao e essa concordancia: sem ela, o dia em que o backend mudasse o
 * formato de `detail` pediria a mesma correcao em dois lugares, e um deles
 * seria esquecido.
 */
async function lancarErroDaResposta(response: Response): Promise<never> {
  // O backend manda `detail` com texto pronto para exibir (503 da API
  // externa fora do ar, por exemplo).
  const detalhe = await response
    .json()
    .then((corpo: { detail?: unknown }) => textoDoDetalhe(corpo.detail))
    .catch(() => undefined);

  const mensagem = detalhe ?? MSG_SEM_DETALHE;
  // O `409` do cadastro e o unico status que uma tela precisa distinguir pelo
  // numero: ele diz *qual campo* corrigir. Os outros viram a mesma mensagem.
  throw response.status === 409
    ? new EmailJaUsado(mensagem)
    : new ErroDoPainel(mensagem);
}

async function pegar<T>(caminho: string, sinal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(caminho, { signal: sinal, credentials: "include" });
  } catch (erro) {
    // Um fetch abortado nao e falha: deixa o chamador distingui-lo.
    if (erro instanceof DOMException && erro.name === "AbortError") throw erro;
    throw new ErroDeRede(MSG_DE_REDE);
  }

  if (!response.ok) await lancarErroDaResposta(response);

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

/**
 * As condicoes severas previstas, um item por dia que dispara.
 *
 * Endpoint proprio, buscado na pagina Condicoes (ADR 0003: so uma pagina le,
 * entao vai nela). So a coordenada viaja, como em `buscarHistorico` — nada
 * aqui exibe o nome da cidade.
 */
export async function buscarCondicoes(
  cidade: Pick<CidadeDoPainel, "latitude" | "longitude">,
  sinal?: AbortSignal,
): Promise<CondicoesResponse> {
  const params = new URLSearchParams({
    latitude: String(cidade.latitude),
    longitude: String(cidade.longitude),
  });

  return pegar<CondicoesResponse>(`/api/condicoes?${params}`, sinal);
}

/**
 * Uma escrita: `POST` com corpo JSON.
 *
 * Gemeo de `pegar`, e nao um parametro dele, porque as diferencas nao sao
 * poucas — metodo, cabecalho, corpo — e um `pegar` que aceitasse todas viraria
 * um `fetch` com outro nome. O tratamento da recusa, esse sim, e o mesmo, e
 * por isso mora em `lancarErroDaResposta`, que os dois chamam.
 *
 * `credentials: "include"` aqui e em `pegar` sao os **dois unicos pontos do
 * frontend** que sabem que existe sessao. E o que o ADR 0005 promete: nenhum
 * componente le, escreve ou anexa cookie — o browser o faz sozinho, e o cookie
 * e `HttpOnly`, entao nem seria legivel se alguem tentasse.
 */
async function enviar<T>(caminho: string, corpo?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(caminho, {
      method: "POST",
      credentials: "include",
      headers: corpo === undefined ? undefined : { "Content-Type": "application/json" },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new ErroDeRede(MSG_DE_REDE);
  }

  if (!response.ok) await lancarErroDaResposta(response);

  return (await response.json()) as T;
}

/**
 * Cria a conta e **ja abre a sessao**: cadastrar entra.
 *
 * Nao ha uma chamada de entrada depois desta. Quem acabou de escolher a senha
 * nao deveria ter de digita-la de novo na tela seguinte — e o backend carimba
 * o cookie ja na resposta do cadastro.
 */
export async function cadastrar(email: string, senha: string): Promise<Conta> {
  return enviar<Conta>("/api/cadastro", { email, senha });
}

/** Valida as credenciais e abre uma sessao nova. */
export async function entrar(email: string, senha: string): Promise<Conta> {
  return enviar<Conta>("/api/entrada", { email, senha });
}

/**
 * Apaga a sessao deste navegador.
 *
 * Sem corpo, e sem conta de volta: o backend responde `200` mesmo sem sessao
 * alguma — quem chega aqui sem cookie queria estar fora, e esta.
 */
export async function sair(): Promise<void> {
  await enviar<{ detail: string }>("/api/saida");
}

/**
 * A conta da sessao, ou `null` se nao ha nenhuma.
 *
 * `null` e resposta normal e vem com `200`, nao com `401`: visitante sem conta
 * e o estado mais comum do app, e trata-lo como falha encheria o console de
 * vermelho em toda visita anonima.
 */
export async function quemSou(sinal?: AbortSignal): Promise<Conta | null> {
  const corpo = await pegar<QuemSouResponse>("/api/quem-sou", sinal);
  return corpo.conta;
}
