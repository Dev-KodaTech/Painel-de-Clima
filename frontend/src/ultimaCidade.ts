/**
 * A ultima cidade que o app carregou.
 *
 * Guardada como o **texto dos parametros de busca**, que e a representacao
 * canonica de uma cidade neste app desde o ADR 0002. Um segundo formato de
 * serializacao seria um segundo lugar para a forma da cidade mudar e alguem
 * esquecer de atualizar.
 *
 * Guarda qualquer cidade que carregou, sem distinguir origem: e a regra mais
 * simples, e ela so e consultada quando nao ha cidade detectada.
 */

import { cidadeDosParametros } from "./cidadeNaUrl";

const CHAVE = "painel-de-clima:ultima-cidade";

/** Guarda. Falha em silencio: aba anonima e armazenamento bloqueado lancam. */
export function lembrar(parametros: URLSearchParams): void {
  try {
    localStorage.setItem(CHAVE, parametros.toString());
  } catch {
    // Sem armazenamento o app funciona igual, so nao reabre onde parou.
  }
}

/**
 * A ultima cidade, ou `null`.
 *
 * O texto guardado passa por `cidadeDosParametros` antes de voltar: o
 * armazenamento sobrevive a mudancas de formato, e um registro de uma versao
 * antiga viraria uma requisicao invalida no carregamento — falha no primeiro
 * instante do app, que e onde ela e mais dificil de entender.
 */
export function ultimaCidade(): URLSearchParams | null {
  let guardado: string | null = null;
  try {
    guardado = localStorage.getItem(CHAVE);
  } catch {
    return null;
  }
  if (!guardado) return null;

  const parametros = new URLSearchParams(guardado);
  return cidadeDosParametros(parametros) ? parametros : null;
}
