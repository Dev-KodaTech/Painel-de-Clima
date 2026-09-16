/**
 * A pagina Cidades vizinhas: a regiao em volta da cidade escolhida.
 *
 * ## O que ela e, e o que ela nao e
 *
 * A navegacao prometia "a lista inteira que o painel da Visao geral trunca", e
 * **essa lista nunca existiu**: o backend produz no maximo cinco vizinhas e o
 * painel ja mostra as cinco. Nao havia nada truncado para revelar. A promessa
 * saiu da navegacao junto com esta pagina — ver ADR 0006.
 *
 * O que a pagina entrega no lugar e outra coisa: uma tabela que **compara**, com
 * as vizinhas e a cidade escolhida lado a lado. O painel responde "quanto faz
 * em cada uma"; a tabela responde "onde esta mais quente aqui em volta", que e
 * a pergunta que cinco numeros empilhados nao respondem.
 *
 * ## A pagina nao busca nada
 *
 * Le `nearby`, `location`, `current` e `units` do painel que o `Shell` ja
 * carregou, pelo contexto do outlet. E a regra do
 * `docs/adr/0003-historico-e-buscado-na-pagina.md` no seu **lado comum**:
 * **dado que varias paginas leem vai no layout; dado que so uma pagina le vai
 * nela.** As vizinhas alimentam o painel da Visao geral e esta pagina, entao
 * ficam onde ja estao. Nenhum endpoint novo, nenhuma requisicao nova — e
 * trocar de pagina nao refaz nada.
 *
 * Quem vier pela Tendencia primeiro pode ler o padrao ao contrario: **a
 * excecao e ela**, nao esta pagina. La a requisicao mora na pagina porque so
 * ela le o historico; aqui nao ha requisicao nenhuma porque duas telas leem as
 * mesmas vizinhas. Os dois lados saem da mesma regra.
 *
 * ## Os cinco estados sao tratados aqui
 *
 * Como na Visao geral e na Tendencia, e pelo mesmo motivo: o `Shell` tratando-os
 * renderizaria a mensagem no lugar da pagina inteira.
 */

import { usePainel } from "../estadoDoPainel";
import { TabelaComparativa } from "../components/vizinhas/TabelaComparativa";

export function CidadesVizinhas() {
  const { estado } = usePainel();

  // Nada, de proposito: o app ainda decide se abre com uma cidade, e a
  // instrucao de buscar uma seria errada por um instante.
  if (estado.tipo === "decidindo") return null;

  if (estado.tipo === "vazio") {
    return (
      <p className="py-6 text-[13px] text-ink-2">
        Busque uma cidade para ver as cidades vizinhas.
      </p>
    );
  }

  if (estado.tipo === "carregando") {
    return (
      <p role="status" className="py-6 text-[13px] text-ink-2">
        Carregando o painel…
      </p>
    );
  }

  if (estado.tipo === "erro") {
    return (
      <p role="alert" className="py-6 text-[13px] text-ink-2">
        {estado.mensagem}
      </p>
    );
  }

  const { painel } = estado;

  // Uma cidade sem nenhuma vizinha e caminho normal, nao falha — e a tabela
  // nao serve para dize-lo: uma tabela com so a cidade escolhida dentro se
  // leria como "a comparacao nao carregou". A frase nomeia a cidade porque e
  // dela que a ausencia fala.
  if (painel.nearby.length === 0) {
    return (
      <p className="py-6 text-[13px] text-ink-2">
        Nao ha cidades vizinhas para comparar com {painel.location.name}.
      </p>
    );
  }

  return (
    <section className="flex flex-col gap-4 py-2">
      {/* A `key` na coordenada da cidade escolhida: trocar de cidade **remonta**
          a tabela, e o criterio de ordenacao volta a distancia.

          Sem ela a tabela sobreviveria a troca com o criterio anterior. Uma
          ordenacao por temperatura e uma pergunta feita sobre *aquela* regiao —
          "onde esta mais quente em volta de Berlim" —, e carrega-la para a
          proxima cidade responderia uma pergunta que ninguem fez, ainda por
          cima num intervalo em que a tabela sai da tela para carregar e volta
          ja ordenada.

          Na coordenada e nao no nome: duas cidades homonimas do mesmo pais sao
          cidades diferentes, e a coordenada e o que as distingue — a mesma
          identidade que `chaveDaLinha` usa nas linhas. */}
      <TabelaComparativa
        key={`${painel.location.latitude},${painel.location.longitude}`}
        location={painel.location}
        current={painel.current}
        nearby={painel.nearby}
        units={painel.units}
      />
    </section>
  );
}
