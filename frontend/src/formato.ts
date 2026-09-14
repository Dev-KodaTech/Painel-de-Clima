/**
 * Formatacao de datas, horas e numeros.
 *
 * A spec chama esta a unica logica de frontend que o compilador nao protege:
 * os timestamps chegam **sem offset de fuso** e sao horario de parede da
 * cidade consultada. Passa-los por `new Date(texto)` faria o browser
 * interpreta-los no fuso *do usuario* e deslocar o resultado em horas — por
 * isso eles sao fatiados como texto, nunca convertidos.
 */

const MESES = [
  "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

const DIAS = [
  "domingo", "segunda-feira", "terca-feira", "quarta-feira",
  "quinta-feira", "sexta-feira", "sabado",
];

/**
 * "domingo, 14 de setembro" a partir de `2026-09-14T03:00`.
 *
 * O dia da semana usa `Date.UTC` sobre os componentes ja separados: a
 * aritmetica de calendario e feita em UTC justamente para que o fuso do
 * browser nao entre na conta.
 */
export function dataPorExtenso(timestamp: string): string {
  const [ano, mes, dia] = timestamp.slice(0, 10).split("-").map(Number);
  const diaDaSemana = DIAS[new Date(Date.UTC(ano, mes - 1, dia)).getUTCDay()];
  return `${diaDaSemana}, ${dia} de ${MESES[mes - 1]}`;
}

/** "03:00" a partir de `2026-09-14T03:00`. Recorte, nao conversao. */
export function horaDoDia(timestamp: string): string {
  return timestamp.slice(11, 16);
}

/** Temperatura arredondada ao grau, com o simbolo vindo do payload. */
export function temperatura(valor: number, unidade: string): string {
  return `${Math.round(valor)}${unidade}`;
}

/** "3,4 mi de habitantes" / "170 mil habitantes": distingue candidatas. */
export function populacao(valor: number | null): string | null {
  if (valor === null || valor <= 0) return null;
  if (valor >= 1_000_000) {
    const milhoes = (valor / 1_000_000).toFixed(1).replace(".", ",");
    return `${milhoes} mi hab.`;
  }
  if (valor >= 1_000) return `${Math.round(valor / 1_000)} mil hab.`;
  return `${valor} hab.`;
}

/** "Land Berlin, Alemanha" — o que torna a escolha entre homonimas informada. */
export function procedencia(admin1: string | null, country: string): string {
  return [admin1, country].filter(Boolean).join(", ");
}
