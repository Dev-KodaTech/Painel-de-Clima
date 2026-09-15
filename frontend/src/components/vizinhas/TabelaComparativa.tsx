/**
 * A tabela comparativa: as cidades vizinhas e a cidade escolhida, lado a lado.
 *
 * E o que esta pagina tem de proprio em relacao ao painel da Visao geral. O
 * painel **lista** — cinco temperaturas soltas, uma embaixo da outra, que so se
 * comparam de cabeca. A tabela **compara**: mesmas colunas, mesmo alinhamento,
 * e a cidade escolhida no meio delas como termo de comparacao.
 *
 * ## Uma `<table>` de verdade
 *
 * O painel da Visao geral usa `<ul>`, e esta bem para uma lista. Aqui sao seis
 * linhas por seis colunas de dados comparaveis, que e a definicao de tabela:
 * com marcacao de tabela, um leitor de tela anuncia "Potsdam, distancia 26 km"
 * ao percorrer a celula, porque o cabecalho da coluna viaja junto. Numa lista
 * de `<div>`s, a mesma celula se anuncia "26 km" e nada mais.
 *
 * ## A cidade escolhida e visivelmente distinta
 *
 * Tres marcas somadas, e nao uma: fundo proprio, nome em azul e o rotulo
 * "cidade escolhida" ao lado. A cor sozinha nao serviria — quem nao a distingue
 * ficaria sem a informacao inteira —, e o rotulo em texto e o que sobrevive ao
 * daltonismo e ao leitor de tela.
 *
 * O rotulo e explicito porque a tensao de vocabulario e real: a cidade
 * escolhida esta dentro de uma tabela chamada "cidades vizinhas" e **nao e uma
 * vizinha**. O glossario e claro em que a vizinha existe sempre em relacao a
 * escolhida; apagar a diferenca aqui seria apagar a relacao que ordena a tela.
 */

import type { Current, Location, Nearby, Units } from "../../api/types";
import { distancia, temperatura } from "../../formato";
import { Painel } from "../Painel";
import { WeatherIcon } from "../WeatherIcon";
import { chaveDaLinha, linhasDaTabela, type Linha } from "./linhas";

type Props = {
  location: Location;
  current: Current;
  nearby: Nearby[];
  units: Units;
};

/** Classes de uma celula de cabecalho, repetidas em cinco colunas. */
const CABECALHO = "pb-2.5 text-[11px] font-medium tracking-wide text-ink-3 uppercase";

export function TabelaComparativa({ location, current, nearby, units }: Props) {
  const linhas = linhasDaTabela(location, current, nearby);

  return (
    <Painel titulo="Cidades vizinhas">
      {/* `table-fixed` com larguras declaradas: sem ele, a coluna do nome
          encolhe ou cresce conforme o nome mais longo da cidade escolhida, e a
          tabela muda de forma a cada troca de cidade. */}
      <table className="w-full table-fixed border-collapse text-left">
        <thead>
          <tr className="border-b border-line">
            {/* O icone nao tem rotulo visivel — a coluna e muda, e a descricao
                do tempo ao lado ja e o texto que ele ilustra. O cabecalho
                existe so para o leitor de tela nao anunciar celula sem nome. */}
            <th scope="col" className={`${CABECALHO} w-9`}>
              <span className="sr-only">Tempo</span>
            </th>
            <th scope="col" className={CABECALHO}>
              Cidade
            </th>
            <th scope="col" className={`${CABECALHO} w-20`}>
              Pais
            </th>
            <th scope="col" className={`${CABECALHO} w-28 text-right`}>
              Distancia
            </th>
            {/* `pl-6`: a distancia e alinhada a direita e a condicao a
                esquerda, entao as duas colunas se encostam exatamente onde o
                texto de uma termina e o da outra comeca — "27 kmNublado". O
                respiro precisa estar na celula, nao entre elas: `border-collapse`
                colapsa qualquer espacamento de tabela. */}
            <th scope="col" className={`${CABECALHO} pl-6`}>
              Condicao
            </th>
            <th scope="col" className={`${CABECALHO} w-24 text-right`}>
              Temperatura
            </th>
          </tr>
        </thead>

        <tbody>
          {linhas.map((linha) => (
            <LinhaDaTabela
              key={chaveDaLinha(linha)}
              linha={linha}
              units={units}
            />
          ))}
        </tbody>
      </table>
    </Painel>
  );
}

function LinhaDaTabela({ linha, units }: { linha: Linha; units: Units }) {
  const { ehEscolhida } = linha;

  return (
    <tr
      className={`border-b border-line last:border-0 ${
        ehEscolhida ? "bg-brand-soft" : ""
      }`}
    >
      <td className="py-2.5">
        <WeatherIcon
          icon={linha.icone}
          description={linha.descricao}
          className="size-7 shrink-0"
        />
      </td>

      {/* `scope="row"`: o nome da cidade e o que nomeia a linha inteira, e e
          o que o leitor de tela repete ao anunciar cada celula dela. */}
      <th scope="row" className="py-2.5 pr-2 text-left font-normal">
        {/* `truncate` porque nomes longos existem — "Villingen-Schwenningen" —
            e a coluna tem largura fixa. */}
        <span
          className={`block truncate text-[13px] font-medium ${
            ehEscolhida ? "text-brand-text" : ""
          }`}
        >
          {linha.nome}
        </span>
        {ehEscolhida && (
          <span className="block text-[10px] text-ink-2">cidade escolhida</span>
        )}
      </th>

      <td className="py-2.5 text-[12px] text-ink-2">{linha.country_code}</td>

      <td className="py-2.5 text-right text-[13px] tabular-nums">
        {linha.distancia_km === null ? (
          /* O traco, e nao "0 km" nem celula em branco. O zero seria um dado
             falso; a celula vazia seria indistinguivel de dado faltando. O
             traco diz "nao se aplica", e o `title` diz por que a quem parar
             em cima. */
          <span className="text-ink-3" title="A distancia e medida a partir desta cidade">
            —
          </span>
        ) : (
          distancia(linha.distancia_km, units.distance)
        )}
      </td>

      {/* A descricao ja vem traduzida do backend; o frontend nao conhece a
          tabela WMO. `truncate` pela mesma razao dos nomes. */}
      <td className="truncate py-2.5 pr-2 pl-6 text-[12px] text-ink-2">
        {linha.descricao}
      </td>

      <td className="py-2.5 text-right text-[13px] font-semibold tabular-nums">
        {temperatura(linha.temperatura, units.temperature)}
      </td>
    </tr>
  );
}
