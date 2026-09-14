/**
 * O grafico de tendencia: as 24 horas do dia corrente, com a hora atual
 * marcada na curva.
 *
 * SVG desenhado a mao, sem biblioteca de graficos: sao 24 pontos numa unica
 * serie, e um `viewBox` com `preserveAspectRatio` responde ao redimensionamento
 * sem medir o container em runtime.
 *
 * Nenhum timestamp passa por `new Date()`. A posicao de cada ponto vem da hora
 * recortada do texto, que e horario de parede da cidade — converte-lo
 * deslocaria a curva inteira para o fuso de quem olha.
 */

import type { HourlyPoint, Units } from "../api/types";
import { horaComoNumero, horaCurta, temperatura } from "../formato";
import { Painel } from "./Painel";

type Props = {
  hourly: HourlyPoint[];
  /** `current.observed_at`: define qual hora recebe o marcador. */
  observedAt: string;
  units: Units;
};

/**
 * Coordenadas do desenho. O `viewBox` e fixo e a escala vertical vem dos
 * dados; as margens reservam espaco para os rotulos dos dois eixos.
 */
const LARGURA = 560;
const ALTURA = 170;
const MARGEM = { topo: 34, direita: 4, base: 22, esquerda: 34 };

const PISO = ALTURA - MARGEM.base;
const TETO = MARGEM.topo;

/**
 * As marcas do eixo: uma a cada quatro horas.
 *
 * Sete rotulos, nao 24 — 24 nao cabem na largura disponivel. A ultima hora do
 * dia entra so se estiver longe o bastante da marca anterior para nao colidir
 * com ela, o que tambem cobre os dias de mudanca de horario de verao, que tem
 * 23 ou 25 horas em vez de 24.
 */
function horasRotuladas(ultimaHora: number): number[] {
  const marcas = [];
  for (let hora = 0; hora <= ultimaHora; hora += 4) marcas.push(hora);
  if (ultimaHora - marcas[marcas.length - 1] >= 2) marcas.push(ultimaHora);
  return marcas;
}

/**
 * A faixa vertical do grafico, com folga de um grau em cada extremo.
 *
 * Sem a folga, a maxima e a minima do dia encostariam nas bordas; com ela a
 * curva respira. O caso degenerado — um dia de temperatura constante — abriria
 * uma faixa de altura zero e faria toda divisao virar `NaN`, por isso o minimo
 * de dois graus.
 */
function faixa(pontos: HourlyPoint[]): { minimo: number; maximo: number } {
  const valores = pontos.map((ponto) => ponto.temperature);
  const minimo = Math.floor(Math.min(...valores)) - 1;
  const maximo = Math.ceil(Math.max(...valores)) + 1;
  return maximo - minimo < 2 ? { minimo, maximo: minimo + 2 } : { minimo, maximo };
}

export function TendenciaTemperatura({ hourly, observedAt, units }: Props) {
  // O backend manda sempre as 24 horas do dia. Sem pontos nao ha curva a
  // desenhar, e insistir levaria a uma escala vazia (`Math.min()` de nada e
  // `Infinity`) que derrubaria o painel inteiro em vez de so este card.
  if (hourly.length === 0) {
    return (
      <Painel titulo="Tendencia de temperatura">
        <p className="text-[13px] text-ink-2">
          Sem dados horarios para esta cidade.
        </p>
      </Painel>
    );
  }

  const { minimo, maximo } = faixa(hourly);

  // A ultima hora do dia, lida dos dados e nao fixada em 23: nos dias de
  // mudanca de horario de verao o dia local tem 23 ou 25 horas, e a curva
  // precisa ocupar a largura inteira de qualquer forma.
  const ultimaHora = horaComoNumero(hourly[hourly.length - 1].time);

  /** A hora do dia no eixo horizontal. */
  const x = (hora: number) =>
    MARGEM.esquerda +
    (hora / ultimaHora) * (LARGURA - MARGEM.esquerda - MARGEM.direita);

  /** Temperatura em altura: o eixo do SVG cresce para baixo, a escala inverte. */
  const y = (valor: number) =>
    PISO - ((valor - minimo) / (maximo - minimo)) * (PISO - TETO);

  const coordenadas = hourly.map((ponto) => ({
    ...ponto,
    x: x(horaComoNumero(ponto.time)),
    y: y(ponto.temperature),
  }));

  const linha = coordenadas.map(({ x, y }) => `${x},${y}`).join(" ");
  // A area sob a curva fecha descendo ate o piso nas duas pontas.
  const area = `${linha} ${coordenadas.at(-1)!.x},${PISO} ${coordenadas[0].x},${PISO}`;

  // A hora atual, se o ponto dela estiver no grafico — o backend manda o dia
  // corrente, mas o marcador nao deve inventar um ponto que nao veio.
  const agora = coordenadas.find(
    (ponto) => horaComoNumero(ponto.time) === horaComoNumero(observedAt),
  );

  // Cinco linhas de grade e cinco rotulos, distribuidos pela faixa.
  const niveis = [0, 0.25, 0.5, 0.75, 1].map((fracao) => {
    const valor = minimo + fracao * (maximo - minimo);
    return { valor, y: y(valor) };
  });

  return (
    <Painel titulo="Tendencia de temperatura">
      <svg
        viewBox={`0 0 ${LARGURA} ${ALTURA}`}
        className="h-40 w-full"
        role="img"
        aria-label={`Temperatura ao longo do dia, de ${temperatura(
          hourly[0].temperature,
          units.temperature,
        )} as 0h a ${temperatura(
          hourly.at(-1)!.temperature,
          units.temperature,
        )} as ${horaCurta(ultimaHora)}`}
      >
        <defs>
          <linearGradient id="tendencia-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-brand)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--color-brand)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {niveis.map(({ valor, y: alturaNivel }) => (
          <g key={valor}>
            <line
              x1={MARGEM.esquerda}
              y1={alturaNivel}
              x2={LARGURA - MARGEM.direita}
              y2={alturaNivel}
              stroke="var(--color-line)"
              strokeWidth="1"
            />
            <text
              x={MARGEM.esquerda - 8}
              y={alturaNivel + 3}
              textAnchor="end"
              fontSize="9"
              fill="var(--color-ink-3)"
            >
              {Math.round(valor)}°
            </text>
          </g>
        ))}

        <polygon points={area} fill="url(#tendencia-area)" />
        <polyline
          points={linha}
          fill="none"
          stroke="var(--color-brand)"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Rotulos esparsos: 24 marcas nao cabem na largura disponivel. */}
        {horasRotuladas(ultimaHora).map((hora) => (
          <text
            key={hora}
            x={x(hora)}
            y={ALTURA - 6}
            textAnchor="middle"
            fontSize="9"
            fill="var(--color-ink-3)"
          >
            {horaCurta(hora)}
          </text>
        ))}

        {agora && (
          <g>
            <line
              x1={agora.x}
              y1={TETO - 4}
              x2={agora.x}
              y2={PISO}
              stroke="var(--color-brand)"
              strokeWidth="1.2"
            />
            <circle
              cx={agora.x}
              cy={agora.y}
              r="4.5"
              fill="var(--color-card)"
              stroke="var(--color-brand)"
              strokeWidth="2.6"
            />
            {/* A pilula do valor atual, ancorada no topo e presa as bordas
                para nao vazar do viewBox nas pontas do dia. */}
            <g
              transform={`translate(${Math.min(
                Math.max(agora.x, MARGEM.esquerda + 26),
                LARGURA - MARGEM.direita - 26,
              )}, 12)`}
            >
              <rect x="-26" y="0" width="52" height="23" rx="8" fill="var(--color-brand)" />
              <text
                y="15.5"
                textAnchor="middle"
                fontSize="11"
                fontWeight="600"
                fill="#fff"
              >
                {temperatura(agora.temperature, units.temperature)}
              </text>
            </g>
          </g>
        )}
      </svg>
    </Painel>
  );
}
