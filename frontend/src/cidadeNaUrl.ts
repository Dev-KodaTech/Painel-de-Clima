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
