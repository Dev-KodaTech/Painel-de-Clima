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
 * A marcacao de tabela e tambem o que torna a ordenacao anunciavel: `aria-sort`
 * mora no `<th>` da coluna ordenada, e e assim que um leitor de tela diz "por
 * qual criterio a tabela esta ordenada" sem que se invente um aviso.
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
 *
 * ## A ordem e estado deste componente, e nao da pagina
 *
 * Aqui e nao um nivel acima porque o componente so monta quando ha linhas para
 * ordenar: a pagina sai cedo enquanto o painel carrega, falha ou vem sem
 * vizinhas. Guardando o criterio na pagina, ele sobreviveria a esses estados e
 * a tabela voltaria ordenada por um criterio que esteve ativo sem controle na
 * tela. Morando aqui, criterio e controles aparecem e somem juntos — nao ha
 * instante em que um exista sem o outro.
 *
 * E estado local, e nao parametro de URL, por decisao do ADR 0006: a ordem de
 * uma tabela curta como esta nao e o que alguem compartilha, e o que importa no
 * link — a cidade escolhida — ja viaja conforme o ADR 0002. (O ADR fala em
 * "cinco linhas" e sao seis com a cidade escolhida; o numero nao muda o
 * argumento, e corrigi-lo e edicao do ADR, nao deste arquivo.)
 */

import { useState } from "react";
import type { Current, Location, Nearby, Units } from "../../api/types";
import { distancia, temperatura, temperaturaExata } from "../../formato";
import { Painel } from "../Painel";
import { WeatherIcon } from "../WeatherIcon";
import {
  CRITERIOS,
  chaveDaLinha,
  ordenarLinhas,
  type Criterio,
  type Linha,
} from "./linhas";

type Props = {
  location: Location;
  current: Current;
  nearby: Nearby[];
  units: Units;
};

/** Classes de uma celula de cabecalho, repetidas em cinco colunas. */
const CABECALHO = "pb-2.5 text-[11px] font-medium tracking-wide text-ink-3 uppercase";

export function TabelaComparativa({ location, current, nearby, units }: Props) {
  // A distancia e o padrao por ser a ordem em que o backend entrega: quem abre
  // a pagina ve a regiao na ordem geografica, e ordenar por temperatura e a
  // pergunta que se faz depois.
  const [criterio, setCriterio] = useState<Criterio>("distancia");

  const linhas = ordenarLinhas(location, current, nearby, criterio);

  return (
    <Painel titulo="Cidades vizinhas">
      {/* `table-fixed` com larguras declaradas: sem ele, a coluna do nome
          encolhe ou cresce conforme o nome mais longo da cidade escolhida, e a
          tabela muda de forma a cada troca de cidade. */}
      <table className="w-full table-fixed border-collapse text-left">
        {/* A legenda nomeia a tabela para quem chega nela pelo leitor de tela,
            que e o que faz `aria-sort` ter a que se referir. `sr-only` porque
            o `<h2>` do painel ja diz o mesmo a quem enxerga. */}
        <caption className="sr-only">
          Cidades vizinhas e a cidade escolhida, com distancia, condicao e
          temperatura
        </caption>
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
            <CabecalhoOrdenavel
              criterioDaColuna="distancia"
              criterioAtivo={criterio}
              onOrdenar={setCriterio}
              className="w-28"
            />
            {/* `pl-6`: a distancia e alinhada a direita e a condicao a
                esquerda, entao as duas colunas se encostam exatamente onde o
                texto de uma termina e o da outra comeca — "27 kmNublado". O
                respiro precisa estar na celula, nao entre elas: `border-collapse`
                colapsa qualquer espacamento de tabela. */}
            <th scope="col" className={`${CABECALHO} pl-6`}>
              Condicao
            </th>
            <CabecalhoOrdenavel
              criterioDaColuna="temperatura"
              criterioAtivo={criterio}
              onOrdenar={setCriterio}
              className="w-24"
            />
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

/**
 * Um cabecalho de coluna que ordena a tabela pelo seu proprio criterio.
 *
 * ## `aria-sort` no `<th>`, e o botao dentro dele
 *
 * E o par que a especificacao de tabelas preve, e por isso o anuncio sai
 * pronto: o leitor de tela le "Temperatura, coluna ordenada em ordem
 * decrescente" ao chegar na coluna, sem que se escreva a frase. Um aviso em
 * `aria-live` diria o mesmo uma vez e sumiria; `aria-sort` e estado, e continua
 * disponivel a quem percorrer a tabela depois.
 *
 * `aria-sort` so aparece na coluna ativa — a especificacao pede que no maximo
 * uma coluna o tenha, e `none` nas outras nao acrescenta nada ao que a ausencia
 * ja diz.
 *
 * ## Um `<button>` de verdade
 *
 * Nao um `<th>` com `onClick`. O botao vem com foco, Tab, Enter e Espaco de
 * graca; um `<th>` clicavel precisaria de `tabIndex`, `role` e um `onKeyDown`
 * reimplementando as duas teclas — tres chances de errar para chegar onde o
 * elemento nativo ja esta.
 *
 * ## O botao ativo continua focalizavel
 *
 * Desabilita-lo seria a leitura ingenua de "nao ha nada a fazer aqui", e
 * quebrava o teclado: `disabled` tira o elemento da ordem de Tab, entao quem
 * chegava nele pelo Tab e apertava Enter **perdia o foco para o `<body>`** — o
 * proximo Tab recomeçava do topo da pagina. Quem usa teclado era justamente
 * quem pagava por uma decisao tomada pensando no mouse.
 *
 * Fica entao um botao comum cuja reativacao nao faz nada: o `onClick` chama
 * `onOrdenar` com o criterio da coluna, que ja e o ativo, e o estado nao muda.
 * O foco permanece onde estava, e a ordem de Tab nao muda de forma a cada
 * clique. O `aria-disabled` diz a quem ouve o que a cor e o triangulo dizem a
 * quem enxerga — que esta coluna ja e a ordenada — sem tirar ninguem da
 * navegacao.
 *
 * ## A direcao nao se inverte no segundo clique
 *
 * Cada criterio tem uma direcao que responde a sua pergunta — a mais quente
 * primeiro e a mais proxima primeiro —, e a direcao oposta responde a pergunta
 * que ninguem faz nesta tabela ("onde esta mais frio"). Sao dois criterios, nao
 * quatro estados. Ver a spec e o ADR 0006.
 */
function CabecalhoOrdenavel({
  criterioDaColuna,
  criterioAtivo,
  onOrdenar,
  className,
}: {
  criterioDaColuna: Criterio;
  criterioAtivo: Criterio;
  onOrdenar: (criterio: Criterio) => void;
  className: string;
}) {
  const ativo = criterioDaColuna === criterioAtivo;
  // A direcao, o anuncio e o glifo saem todos daqui: e o que impede o
  // `aria-sort` de discordar da ordem que `ordenarLinhas` produziu.
  const { rotulo, anuncio, glifo } = CRITERIOS[criterioDaColuna];

  return (
    <th
      scope="col"
      aria-sort={ativo ? anuncio : undefined}
      className={`${CABECALHO} ${className} pr-1 text-right`}
    >
      <button
        type="button"
        // Reativar o criterio ativo cai aqui e nao muda estado algum. Ver o
        // cabecalho: o botao continua focalizavel de proposito.
        onClick={() => onOrdenar(criterioDaColuna)}
        aria-disabled={ativo || undefined}
        className={`inline-flex items-center gap-1 rounded-inner px-1 py-0.5 uppercase outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand/40 ${
          ativo ? "text-brand-text" : "cursor-pointer hover:text-ink"
        }`}
      >
        {rotulo}
        {/* O triangulo diz **qual** e a direcao a quem enxerga, o mesmo que
            `aria-sort` diz a quem ouve. `aria-hidden` para nao virar "triangulo
            preto apontando para baixo" no meio do anuncio da coluna. */}
        {ativo && (
          <span aria-hidden="true" className="text-[9px]">
            {glifo}
          </span>
        )}
      </button>
    </th>
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

      {/* O `title` traz a temperatura sem arredondar, e existe por causa da
          ordenacao: 18,7 °C e 18,5 °C sao ambos "19 °C" na tela, e ordenadas
          por temperatura essas duas linhas ficam uma sobre a outra parecendo
          fora de ordem. A ordem esta certa — `ordenarLinhas` compara o numero
          do payload, nao o texto —, e o que falta e poder conferir. */}
      <td
        className="py-2.5 text-right text-[13px] font-semibold tabular-nums"
        title={temperaturaExata(linha.temperatura, units.temperature)}
      >
        {temperatura(linha.temperatura, units.temperature)}
      </td>
    </tr>
  );
}
