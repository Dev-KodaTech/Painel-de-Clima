/**
 * O cabecalho: titulo, data, busca e o cromo do design.
 *
 * Altura fixa de proposito. A busca some em Ajustes e a data so existe depois
 * que uma cidade carrega; sem altura propria, o conteudo abaixo pularia a cada
 * navegacao.
 */

import { useState } from "react";
import type { Cidade } from "../api/types";
import {
  IconeEnvelope,
  IconeLua,
  IconePessoa,
  IconeSino,
  IconeSol,
} from "../icones";
import { aplicarTema, oOutro, temaAtual } from "../tema";
import { BuscaCidade } from "./BuscaCidade";

/**
 * A pilula sol/lua. Um controle de verdade, ao contrario do resto do cromo.
 *
 * Um botao so, e nao um por segmento: a acao e uma — trocar de tema —, e dois
 * botoes dariam ao segmento ativo um clique que nao faz nada. O rotulo diz a
 * **acao**, nao o estado, que e o que um leitor de tela precisa ouvir antes de
 * apertar.
 *
 * O tema e lido do `<html>` na primeira renderizacao. Quem o carimbou foi o
 * script inline do `index.html`, antes do primeiro paint; reler as fontes aqui
 * seria uma segunda copia da regra de precedencia, livre para discordar.
 */
function AlternarTema() {
  const [tema, setTema] = useState(temaAtual);

  function alternar() {
    const proximo = oOutro(tema);
    aplicarTema(proximo);
    setTema(proximo);
  }

  const acao = tema === "claro" ? "Ativar tema escuro" : "Ativar tema claro";
  const ativo = "bg-brand text-white";
  const inativo = "text-ink-2";

  return (
    <button
      type="button"
      onClick={alternar}
      aria-label={acao}
      title={acao}
      className="flex items-center gap-0.5 rounded-full bg-card p-1 shadow-card outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
    >
      <span
        className={`grid size-8 place-items-center rounded-full transition-colors ${
          tema === "claro" ? ativo : inativo
        }`}
      >
        <IconeSol />
      </span>
      <span
        className={`grid size-8 place-items-center rounded-full transition-colors ${
          tema === "escuro" ? ativo : inativo
        }`}
      >
        <IconeLua />
      </span>
    </button>
  );
}

/**
 * Envelope, sino e avatar: o que o design mostra e que nao tem funcionalidade
 * por tras.
 *
 * Nao ha cadastro, e-mail nem notificacao. Vao como **decoracao inerte**, nunca
 * como `<button>`: um botao que aceita o clique e nao responde promete o que
 * nao cumpre, e para um leitor de tela anuncia uma acao inexistente. Dai o
 * `aria-hidden` no bloco — nao ha nada ali para perceber.
 *
 * O toggle sol/lua saiu daqui quando o tema escuro passou a funcionar.
 *
 * O avatar usa silhueta neutra e nenhum nome. O design traz "Winter Potter",
 * que seria um usuario logado ficticio numa aplicacao sem login.
 */
function Cromo() {
  return (
    <div aria-hidden="true" className="flex shrink-0 items-center gap-2">
      <span className="grid size-10 place-items-center rounded-full bg-card text-ink-2 shadow-card">
        <IconeEnvelope />
      </span>
      <span className="grid size-10 place-items-center rounded-full bg-card text-ink-2 shadow-card">
        <IconeSino />
      </span>
      <span className="grid size-10 place-items-center rounded-full bg-card text-ink-3 shadow-card">
        <IconePessoa />
      </span>
    </div>
  );
}

type Props = {
  /**
   * A data de hoje **na cidade consultada**, ou `null` se nenhuma carregou.
   *
   * `null` nao exibe nada. Mostrar a data local do browser enquanto se espera
   * faria a data trocar de significado em silencio: quem esta em Sao Paulo
   * consultando Toquio nao teria como saber qual das duas esta lendo.
   */
  data: string | null;
  /** Ajustes e a unica pagina que nao e sobre uma cidade. */
  mostrarBusca: boolean;
  /** O nome da cidade carregada, para o campo de busca refleti-la. */
  nomeDaCidade: string | null;
  onEscolher: (cidade: Cidade) => void;
};

export function Cabecalho({
  data,
  mostrarBusca,
  nomeDaCidade,
  onEscolher,
}: Props) {
  return (
    <header className="flex h-16 shrink-0 items-center gap-4">
      <div className="w-48 shrink-0">
        <h1 className="text-sm font-semibold">Painel de Clima</h1>
        {data && <p className="mt-0.5 text-[11px] text-ink-2">{data}</p>}
      </div>

      <div className="flex min-w-0 flex-1 justify-center">
        {/*
          O `key` remonta a busca quando a cidade carregada muda, e e assim que
          o campo segue a URL: um link colado ou o botao Voltar carregam um
          painel sem que ninguem tenha digitado, e o campo ficaria vazio ao lado
          de um painel cheio. Remontar tambem fecha o dropdown, que e o que se
          quer nesse momento.
        */}
        {mostrarBusca && (
          <BuscaCidade
            key={nomeDaCidade ?? ""}
            nomeDaCidade={nomeDaCidade}
            onEscolher={onEscolher}
          />
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <AlternarTema />
        <Cromo />
      </div>
    </header>
  );
}
