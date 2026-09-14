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

/** Abreviacoes para o painel da semana, onde sete nomes inteiros nao caberiam. */
const DIAS_CURTOS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"];

const MESES_CURTOS = [
  "jan", "fev", "mar", "abr", "mai", "jun",
  "jul", "ago", "set", "out", "nov", "dez",
];

/**
 * O indice do dia da semana de uma data `AAAA-MM-DD`.
 *
 * A aritmetica de calendario e feita em UTC sobre os componentes ja separados,
 * justamente para que o fuso do browser nao entre na conta: `new Date(texto)`
 * sobre um timestamp sem offset seria lido no fuso do usuario e poderia cair no
 * dia anterior.
 */
function indiceDoDia(data: string): number {
  const [ano, mes, dia] = data.slice(0, 10).split("-").map(Number);
  return new Date(Date.UTC(ano, mes - 1, dia)).getUTCDay();
}

/**
 * "domingo, 14 de setembro" a partir de `2026-09-14T03:00`.
 *
 * O dia da semana usa `Date.UTC` sobre os componentes ja separados: a
 * aritmetica de calendario e feita em UTC justamente para que o fuso do
 * browser nao entre na conta.
 */
export function dataPorExtenso(timestamp: string): string {
  const [, mes, dia] = timestamp.slice(0, 10).split("-").map(Number);
  return `${DIAS[indiceDoDia(timestamp)]}, ${dia} de ${MESES[mes - 1]}`;
}

/** "Dom" a partir de `2026-09-14`: o rotulo de uma coluna da semana. */
export function diaDaSemanaCurto(data: string): string {
  return DIAS_CURTOS[indiceDoDia(data)];
}

/** "14 set" a partir de `2026-09-14`, para datar um dia sem repetir o ano. */
export function dataCurta(data: string): string {
  const [, mes, dia] = data.slice(0, 10).split("-").map(Number);
  return `${dia} ${MESES_CURTOS[mes - 1]}`;
}

/**
 * A hora de um timestamp como numero (0-23), para posicionar no grafico.
 *
 * Recorte de texto, como todo o resto deste modulo: a hora exibida e a da
 * cidade, e uma conversao a moveria para o fuso do usuario.
 */
export function horaComoNumero(timestamp: string): number {
  return Number(timestamp.slice(11, 13));
}

/** "16h" — o rotulo esparso do eixo do grafico, onde "16:00" nao caberia. */
export function horaCurta(hora: number): string {
  return `${hora}h`;
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
