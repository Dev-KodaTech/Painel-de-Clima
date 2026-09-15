/**
 * A cidade escolhida, lida e escrita nos parametros de busca da URL.
 *
 * Ela mora na URL e nao em `useState` — ver
 * `docs/adr/0002-cidade-na-url.md`. Aqui fica a unica traducao entre os dois
 * formatos, para que nenhuma pagina precise saber como os parametros se
 * chamam.
 *
 * Sao seis parametros, e nao tres: `/api/weather` exige `country_code`, e usa
 * `country` e `admin1` para montar o `location` exibido. Carregar menos
 * devolve 422 ou um cabecalho sem procedencia.
 */

import type { CidadeDoPainel } from "./api/types";

/**
 * A cidade dos parametros, ou `null` se nao houver uma.
 *
 * `null` e o estado inicial normal — ninguem buscou ainda —, nao erro. Uma URL
 * pela metade (sem `cc`, digamos) tambem devolve `null`: e indistinguivel de
 * link truncado, e vale mais voltar ao estado inicial que pedir um painel que
 * o backend recusaria.
 */
export function cidadeDosParametros(
  parametros: URLSearchParams,
): CidadeDoPainel | null {
  const latitude = Number(parametros.get("lat"));
  const longitude = Number(parametros.get("lon"));
  const name = parametros.get("name");
  const country_code = parametros.get("cc");

  if (!name || !country_code) return null;
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
  // `Number("")` e 0, que e coordenada valida: a ausencia precisa ser testada
  // no texto, nao no numero.
  if (!parametros.get("lat") || !parametros.get("lon")) return null;

  return {
    latitude,
    longitude,
    name,
    country_code,
    country: parametros.get("country") ?? "",
    admin1: parametros.get("admin1"),
  };
}

/** Os seis parametros que descrevem a cidade, e so eles. */
const DA_CIDADE = ["lat", "lon", "name", "cc", "country", "admin1"] as const;

/** Os parametros de uma cidade, para navegar ate ela. */
export function parametrosDaCidade(cidade: CidadeDoPainel): URLSearchParams {
  const parametros = new URLSearchParams({
    lat: String(cidade.latitude),
    lon: String(cidade.longitude),
    name: cidade.name,
    cc: cidade.country_code,
  });
  if (cidade.country) parametros.set("country", cidade.country);
  if (cidade.admin1) parametros.set("admin1", cidade.admin1);
  return parametros;
}

/**
 * Os parametros atuais com a cidade trocada, **preservando o resto da URL**.
 *
 * Trocar a cidade nao pode apagar o estado da pagina em que se esta: quem
 * escolheu "6 meses" na Tendencia e busca outra cidade quer comparar as duas no
 * mesmo periodo, e nao voltar para sete dias. Substituir os parametros por um
 * conjunto novo — que e o que uma `URLSearchParams` recem-criada faz — apagava
 * a janela junto.
 *
 * Os seis da cidade sao removidos antes, e nao so sobrescritos: a cidade nova
 * pode nao ter `admin1` nem `country`, e sem a limpeza ela herdaria os da
 * anterior — Paris apareceria em "Land Berlin".
 */
export function trocarCidade(
  parametros: URLSearchParams,
  cidade: CidadeDoPainel,
): URLSearchParams {
  const proximos = new URLSearchParams(parametros);
  for (const chave of DA_CIDADE) proximos.delete(chave);
  for (const [chave, valor] of parametrosDaCidade(cidade)) {
    proximos.set(chave, valor);
  }
  return proximos;
}
