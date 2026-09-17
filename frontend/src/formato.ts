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
 * Abreviacoes para o painel da semana, onde sete nomes inteiros nao caberiam.
 *
 * Exportada por causa da grade do Calendario, que rotula as **colunas** com
 * exatamente estes sete nomes — as colunas da grade sao os dias da semana que
 * `diaDaSemanaCurto` devolve, e nao uma segunda lista que por acaso coincide.
 * Uma copia local ali seria um lugar a mais para discordar desta na primeira
 * vez que alguem acentuasse "Sab".
 */
export const DIAS_CURTOS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"];

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
 * Quantas colunas vazias precedem o primeiro dia numa grade que comeca no
 * domingo.
 *
 * **A primeira aritmetica de calendario do app**, e nao so recorte de texto: a
 * grade do Calendario nao comeca no domingo, comeca hoje, e sem este empurrao
 * o dia 14 cairia na coluna de domingo so por ser o primeiro da lista.
 *
 * O indice do dia da semana ja e o proprio deslocamento — domingo e 0, e um
 * domingo nao precisa de coluna vazia nenhuma —, e por isso esta funcao e fina.
 * Ela existe assim mesmo para nomear o que o numero significa no layout: quem
 * le `gridColumnStart` na celula nao tem como saber que `getUTCDay` era um
 * offset de coluna.
 */
export function colunasVaziasAntesDe(data: string): number {
  return indiceDoDia(data);
}

/**
 * "setembro de 2026" — o cabecalho de um trecho de mes dentro da grade.
 *
 * Os dezesseis dias atravessam o limite do mes quase sempre, e sem esta linha a
 * grade exibiria "28, 29, 30, 1, 2" sem dizer que virou outubro. Com o ano
 * junto porque a virada de dezembro tambem e virada de ano, e ali "janeiro"
 * sozinho seria ambiguo.
 *
 * Recorte de texto, e nao conversao — a regra deste modulo. Nem `Date.UTC` e
 * preciso aqui: mes e ano estao no proprio texto, e so o dia da semana exige
 * aritmetica de calendario.
 */
export function mesEAno(data: string): string {
  const [ano, mes] = data.slice(0, 10).split("-").map(Number);
  return `${MESES[mes - 1]} de ${ano}`;
}

/** O numero do dia no mes: "14" a partir de `2026-09-14`. O rotulo da celula. */
export function diaDoMes(data: string): string {
  return String(Number(data.slice(8, 10)));
}

/**
 * "8 de outubro" — a data em que a fronteira do dia 8 cai.
 *
 * Sem dia da semana e sem ano, ao contrario de `dataPorExtenso`: ela aparece no
 * meio de uma frase corrida ("A partir de 8 de outubro, a previsao vem de outro
 * modelo"), e ali o dia da semana seria ruido.
 */
export function diaEMes(data: string): string {
  const [, mes, dia] = data.slice(0, 10).split("-").map(Number);
  return `${dia} de ${MESES[mes - 1]}`;
}

/**
 * Se duas datas caem no mesmo mes.
 *
 * Comparacao de texto, e nao de `Date`: `"2026-09"` contra `"2026-10"` decide a
 * mesma coisa sem construir data nenhuma — e, de novo, sem dar ao fuso do
 * browser a chance de opinar.
 */
export function mesmoMes(uma: string, outra: string): boolean {
  return uma.slice(0, 7) === outra.slice(0, 7);
}

/** "40%" — a probabilidade de chuva de um dia distante. */
export function probabilidade(valor: number): string {
  return `${Math.round(valor)}%`;
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
 * "Sex, 16 set" a partir de `2026-09-14`: o dia de um card de condicao, sem
 * ambiguidade na semana.
 *
 * Compartilhada entre `CondicoesPrevistas` (o painel) e `Condicoes` (a
 * pagina): os dois cards datam um dia da mesma forma.
 */
export function diaDoCard(data: string): string {
  return `${diaDaSemanaCurto(data)}, ${dataCurta(data)}`;
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

/**
 * "18,7 °C": a temperatura **sem** arredondar, para o `title` de uma celula.
 *
 * Existe por causa da tabela ordenavel das cidades vizinhas: 18,7 °C e
 * 18,5 °C sao ambos "19 °C" arredondados, e ordenadas por temperatura essas
 * linhas ficam uma sobre a outra parecendo fora de ordem. A ordem esta certa —
 * a ordenacao compara o numero do payload, nao o texto —, e isto e o que
 * permite conferir.
 *
 * Separada de `temperatura` e nao um parametro dela: sao dois usos distintos —
 * um e o numero que se le na tela, o outro e o que se consulta ao duvidar
 * dele —, e o grau redondo continua sendo o que o app mostra em toda parte.
 *
 * A virgula decimal como no resto deste modulo: a interface e pt-BR.
 */
export function temperaturaExata(valor: number, unidade: string): string {
  return `${String(valor).replace(".", ",")}${unidade}`;
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

/**
 * "6,0 mm" / "0 mm": a chuva de um dia, com a unidade vinda do payload.
 *
 * A casa decimal so aparece quando ha chuva. Num dia seco, "0,0 mm" sugere uma
 * precisao que nao existe e polui a coluna de sete dias; "0 mm" e o suficiente.
 */
export function precipitacao(valor: number, unidade: string): string {
  if (valor === 0) return `0 ${unidade}`;
  return `${valor.toFixed(1).replace(".", ",")} ${unidade}`;
}

/**
 * "27 km" / "4.094 km": a distancia de uma cidade vizinha.
 *
 * O separador de milhar importa aqui mais que em qualquer outro numero do
 * painel: as distancias de uma cidade isolada tem quatro digitos, e "4094 km"
 * se le como um numero qualquer enquanto "4.094 km" se le como a distancia
 * grande que e — que e justamente a informacao que torna a comparacao honesta.
 *
 * A unidade vem do payload, como toda unidade exibida.
 */
export function distancia(valor: number, unidade: string): string {
  return `${Math.round(valor).toLocaleString("pt-BR")} ${unidade}`;
}

/**
 * "17 ago — 15 set": o intervalo que a janela temporal cobre.
 *
 * Existe para que a pessoa saiba que "30 dias" termina hoje e nao numa data
 * qualquer. As duas datas vem prontas do payload — o frontend nao recalcula
 * janela —, e aqui so se formatam.
 */
export function intervalo(inicio: string, fim: string): string {
  return `${dataCurta(inicio)} — ${dataCurta(fim)}`;
}

/** "2025" a partir de `2025-09-14`: rotula a serie do ano anterior. */
export function ano(data: string): string {
  return data.slice(0, 4);
}

/**
 * "60,3 mm": a chuva acumulada de uma janela inteira.
 *
 * Distinta de `precipitacao`, que e a chuva de **um dia** e omite a casa
 * decimal no dia seco. Aqui a casa fica sempre: um acumulado de 0,0 mm num mes
 * e uma informacao — significa que nao choveu o mes todo —, nao ruido.
 */
export function acumulado(valor: number, unidade: string): string {
  return `${valor.toFixed(1).replace(".", ",")} ${unidade}`;
}

/** "71%" / "13,5 km/h": um numero de resumo com a unidade vinda do payload. */
export function medida(valor: number, unidade: string, casas = 0): string {
  const numero = valor.toFixed(casas).replace(".", ",");
  // `%` cola no numero; `km/h` pede espaco. A unidade vazia (o indice UV) nao
  // deixa espaco sobrando no fim.
  if (unidade === "") return numero;
  if (unidade === "%") return `${numero}%`;
  return `${numero} ${unidade}`;
}

/**
 * "+2,4 °C" / "−1,1 °C": a diferenca entre os dois periodos.
 *
 * O sinal e explicito nos dois lados: "2,4" sozinho nao diz se este setembro
 * esta mais quente ou mais frio que o passado, que e a pergunta inteira do
 * grafico. O menos e o sinal tipografico (−), nao o hifen.
 */
export function diferenca(valor: number, unidade: string): string {
  const sinal = valor > 0 ? "+" : valor < 0 ? "−" : "";
  return `${sinal}${Math.abs(valor).toFixed(1).replace(".", ",")} ${unidade}`;
}

/**
 * "14 set, 21:52" — quando uma noticia foi publicada.
 *
 * **A unica funcao deste modulo que converte de verdade**, e a excecao merece
 * a explicacao. Todo o resto recorta texto porque os timestamps do painel vem
 * *sem* offset e sao horario de parede da cidade consultada: converte-los os
 * moveria para o fuso de quem olha, que e o defeito que este modulo existe
 * para evitar.
 *
 * Aqui e o oposto. A `publicada_em` chega **com** offset — e os feeds divergem
 * entre `-0300` e `+0000` (ADR 0009) —, e uma noticia nao pertence a cidade
 * nenhuma: ela foi publicada num instante, e o instante se le no fuso de quem
 * esta lendo. Recortar o texto aqui exibiria a hora de Brasilia para uns e a
 * de Londres para outros, conforme o veiculo, o que seria um numero sem
 * significado.
 *
 * **O ano aparece quando nao e o corrente.** Os feeds trazem dezenas de itens
 * e a FAPESP publica devagar: sem isto, uma materia de setembro do ano passado
 * se leria "11 set, 12:03", indistinguivel da desta semana. Omiti-lo no ano
 * corrente — que e a esmagadora maioria — mantem a linha curta onde a
 * ambiguidade nao existe.
 *
 * `agora` e injetado para que o teste do caso "ano anterior" nao dependa da
 * data em que roda.
 *
 * Uma data que o browser nao consiga ler devolve string vazia, e nao "Invalid
 * Date": o backend ja descarta o item sem data, entao isto e so a rede de
 * seguranca de uma linha que nao deve mostrar lixo.
 */
export function publicadaEm(iso: string, agora = new Date()): string {
  const instante = new Date(iso);
  if (Number.isNaN(instante.getTime())) return "";

  const dia = instante.getDate();
  const mes = MESES_CURTOS[instante.getMonth()];
  const hora = String(instante.getHours()).padStart(2, "0");
  const minuto = String(instante.getMinutes()).padStart(2, "0");

  const ano =
    instante.getFullYear() === agora.getFullYear()
      ? ""
      : ` de ${instante.getFullYear()}`;

  return `${dia} ${mes}${ano}, ${hora}:${minuto}`;
}

/**
 * As faixas do indice UV, como a OMS as define.
 *
 * O numero sozinho nao diz nada a quem nao o consulta todo dia: 3 e 8 sao
 * ambos "algum sol" para quem le, e sao "moderado" e "muito alto" para quem
 * sabe. A faixa e o que torna o grafico acionavel.
 */
const FAIXAS_DE_UV = [
  { ate: 2.9, nome: "Baixo" },
  { ate: 5.9, nome: "Moderado" },
  { ate: 7.9, nome: "Alto" },
  { ate: 10.9, nome: "Muito alto" },
] as const;

/** "Moderado" a partir de 4,2. Acima de 11 nao ha teto: e extremo. */
export function faixaDeUv(indice: number): string {
  return FAIXAS_DE_UV.find((faixa) => indice <= faixa.ate)?.nome ?? "Extremo";
}

/**
 * "noroeste (NO)": a direcao dominante do vento, por extenso e abreviada.
 *
 * O rumo abreviado vem do backend, que faz a media **vetorial** — a aritmetica
 * de 350° e 10° daria sul. Aqui so se traduz a sigla para a palavra, porque
 * "noroeste" se le e "NO" se reconhece; mostrar os dois serve a quem le de um
 * jeito e a quem le do outro.
 */
const RUMOS_POR_EXTENSO: Record<string, string> = {
  N: "norte",
  NNE: "norte-nordeste",
  NE: "nordeste",
  ENE: "leste-nordeste",
  E: "leste",
  ESE: "leste-sudeste",
  SE: "sudeste",
  SSE: "sul-sudeste",
  S: "sul",
  SSO: "sul-sudoeste",
  SO: "sudoeste",
  OSO: "oeste-sudoeste",
  O: "oeste",
  ONO: "oeste-noroeste",
  NO: "noroeste",
  NNO: "norte-noroeste",
};

export function rumoPorExtenso(rumo: string): string {
  return RUMOS_POR_EXTENSO[rumo] ?? rumo;
}
