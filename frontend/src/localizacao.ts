/**
 * A localizacao do navegador, embrulhada numa promessa.
 *
 * `navigator.geolocation` e de callback e distingue os erros por um codigo
 * numerico. Traduzi-lo aqui deixa o componente com tres desfechos nomeados em
 * vez de `code === 1`, e concentra a regra que importa: **negar nao e falha**.
 */

/** Quanto esperar pela coordenada. Alem disso, o aviso discreto. */
export const TIMEOUT_MS = 10_000;

/**
 * O desfecho de um pedido de localizacao.
 *
 * `negada` existe separada de `indisponivel` porque as duas levam a interfaces
 * opostas: negar e escolha do usuario e nao merece mensagem alguma, enquanto
 * o timeout merece um aviso. Um `Error` unico obrigaria quem chama a decidir
 * isso inspecionando texto.
 */
export type Localizacao =
  | { tipo: "coordenada"; latitude: number; longitude: number }
  | { tipo: "negada" }
  | { tipo: "indisponivel" };

/**
 * Se o navegador oferece a API **e pode usa-la**. Caso contrario, o botao nao
 * e renderizado.
 *
 * Nao basta `"geolocation" in navigator`: a API exige contexto seguro, e em
 * HTTP puro a chave existe mas toda chamada falha com `POSITION_UNAVAILABLE`.
 * O botao apareceria e so saberia dizer "nao foi possivel" — pior que a sua
 * ausencia, que e o que a spec pede para este caso.
 *
 * `localhost` conta como seguro, entao o desenvolvimento continua funcionando.
 */
export function temGeolocalizacao(): boolean {
  return (
    typeof navigator !== "undefined" &&
    "geolocation" in navigator &&
    window.isSecureContext
  );
}

/**
 * Se a permissao de localizacao **ja foi concedida** numa visita anterior.
 *
 * Existe para que o painel possa abrir na cidade da pessoa sem disparar
 * pop-up algum: `permissions.query` apenas *consulta* o estado guardado pelo
 * browser, e so quando ele responde `granted` e que `pedirLocalizacao` e
 * chamada. A regra de nunca pedir no carregamento continua inteira.
 *
 * Responde `false` a qualquer duvida — browser sem a API, consulta que lanca,
 * estado `prompt` ou `denied`. O degrau seguinte (a ultima cidade) assume, e o
 * silencio e o comportamento correto.
 */
export async function permissaoConcedida(): Promise<boolean> {
  if (!temGeolocalizacao() || !navigator.permissions?.query) return false;
  try {
    const status = await navigator.permissions.query({ name: "geolocation" });
    return status.state === "granted";
  } catch {
    return false;
  }
}

/**
 * Pede a coordenada ao navegador.
 *
 * Chamado **apenas a partir de um clique**, nunca no carregamento: o pedido
 * automatico no primeiro acesso e negado por reflexo, e o browser lembra a
 * negacao — queima a unica chance.
 *
 * Nunca rejeita: todo desfecho, inclusive a negacao, e um valor. O chamador
 * trata tres casos e nao um `catch` que teria de reclassificar o erro.
 */
export function pedirLocalizacao(): Promise<Localizacao> {
  return new Promise((resolver) => {
    navigator.geolocation.getCurrentPosition(
      (posicao) =>
        resolver({
          tipo: "coordenada",
          latitude: posicao.coords.latitude,
          longitude: posicao.coords.longitude,
        }),
      (erro) =>
        resolver(
          erro.code === erro.PERMISSION_DENIED
            ? { tipo: "negada" }
            : { tipo: "indisponivel" },
        ),
      { timeout: TIMEOUT_MS },
    );
  });
}
