/**
 * O tema claro/escuro.
 *
 * O tema vive num atributo do `<html>` (`data-tema`), e nao em classe do React:
 * o CSS precisa dele **antes do primeiro paint**, e por isso quem o carimba na
 * primeira vez e um script inline no `index.html`. Este modulo cuida do resto —
 * ler, alternar e guardar.
 */

export type Tema = "claro" | "escuro";

/**
 * A chave do armazenamento.
 *
 * **Duplicada no script inline do `index.html`**, e as duas precisam concordar.
 * E o preco de nao piscar: o script roda antes de qualquer modulo, entao nao
 * tem como importar daqui.
 */
export const CHAVE_TEMA = "painel-de-clima:tema";

function ehTema(valor: unknown): valor is Tema {
  return valor === "claro" || valor === "escuro";
}

/**
 * O tema com que a pagina abriu, lido do `<html>`.
 *
 * Lido do DOM e nao do armazenamento de proposito: o script inline ja resolveu
 * a precedencia (escolha guardada, senao `prefers-color-scheme`), e reler as
 * fontes aqui seria uma segunda implementacao da mesma regra, livre para
 * discordar da primeira.
 */
export function temaAtual(): Tema {
  const carimbado = document.documentElement.dataset.tema;
  return ehTema(carimbado) ? carimbado : "claro";
}

/**
 * Aplica o tema e o guarda.
 *
 * O armazenamento pode lancar — aba anonima, cookies bloqueados. Quando
 * lanca, o tema ainda muda nesta visita; so nao sobrevive a proxima. Falhar o
 * clique inteiro por causa disso seria pior.
 */
export function aplicarTema(tema: Tema): void {
  document.documentElement.dataset.tema = tema;
  try {
    localStorage.setItem(CHAVE_TEMA, tema);
  } catch {
    // Sem armazenamento o tema vale so nesta visita. Nada a avisar.
  }
}

export function oOutro(tema: Tema): Tema {
  return tema === "claro" ? "escuro" : "claro";
}
