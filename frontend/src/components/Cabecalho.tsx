/**
 * O cabecalho: titulo, data, busca e o cromo do design.
 *
 * Altura fixa de proposito. A busca some em Ajustes e a data so existe depois
 * que uma cidade carrega; sem altura propria, o conteudo abaixo pularia a cada
 * navegacao.
 */

import { useState } from "react";
import { Link } from "react-router";
import type { Cidade } from "../api/types";
import type { EstadoDaConta } from "../estadoDaConta";
import {
  IconeEnvelope,
  IconeLua,
  IconePessoa,
  IconeSino,
  IconeSol,
} from "../icones";
import {
  CAMINHO_CADASTRO,
  CAMINHO_ENTRADA,
  useComCidade,
} from "../navegacao";
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
 * Envelope e sino: o que o design mostra e que nao tem funcionalidade por tras.
 *
 * Nao ha e-mail nem notificacao. Vao como **decoracao inerte**, nunca como
 * `<button>`: um botao que aceita o clique e nao responde promete o que nao
 * cumpre, e para um leitor de tela anuncia uma acao inexistente. Dai o
 * `aria-hidden` no bloco — nao ha nada ali para perceber.
 *
 * O avatar **saiu daqui** quando a conta passou a existir: era a silhueta
 * neutra que segurava o lugar, e quem o ocupa agora e a `Conta` ao lado, que
 * responde ao clique porque tem o que fazer.
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
    </div>
  );
}

/**
 * A conta no cabecalho: quem esta entrado, ou o caminho para entrar.
 *
 * E o que torna as duas telas **alcancaveis de qualquer pagina**, que e o
 * pedido do ticket: o cabecalho esta em todas elas, e os dois links moram
 * nele.
 *
 * Enquanto a consulta nao volta, nao desenha nada. Um "Entrar" que aparece e
 * vira um e-mail um instante depois e pior que o vazio: quem tem sessao veria
 * a propria conta piscar de ausente para presente a cada recarga. O espaco e
 * reservado pela altura fixa do cabecalho, entao nada pula quando o estado
 * chega.
 *
 * Quem esta entrado ve **com qual conta** — o e-mail, nao um generico "minha
 * conta" —, porque duas contas da mesma pessoa sao indistinguiveis sem ele.
 * O `title` repete o e-mail para quando o `max-w` o truncar.
 *
 * `SeloDaConta`, e nao `Conta`: *conta* e o termo do glossario para a
 * identidade, e um componente com esse nome faria a palavra significar duas
 * coisas no mesmo arquivo — o widget e o dono. Os vizinhos seguem a mesma
 * regra, nomeando o papel na interface: `Cromo`, `AlternarTema`.
 */
function SeloDaConta({ conta }: { conta: EstadoDaConta }) {
  const comCidade = useComCidade();

  if (conta.tipo === "consultando") return null;

  if (conta.tipo === "entrada") {
    return (
      <span
        title={conta.conta.email}
        className="flex min-w-0 items-center gap-2 rounded-full bg-card py-1.5 pl-1.5 pr-3.5 shadow-card"
      >
        <span
          aria-hidden="true"
          className="grid size-7 shrink-0 place-items-center rounded-full bg-brand-soft text-brand"
        >
          <IconePessoa className="size-4" />
        </span>
        {/* O e-mail e o rotulo visivel; o prefixo so existe para o leitor de
            tela, que sem ele anunciaria um endereco solto no cabecalho. */}
        <span className="sr-only">Entrado como</span>
        <span className="max-w-[160px] truncate text-[12px]">
          {conta.conta.email}
        </span>
      </span>
    );
  }

  return (
    <span className="flex shrink-0 items-center gap-2">
      <Link
        to={comCidade(CAMINHO_ENTRADA)}
        className="rounded-full bg-card px-3.5 py-2 text-[12px] text-ink-2 shadow-card outline-none transition-colors hover:text-brand focus-visible:ring-2 focus-visible:ring-brand/40"
      >
        Entrar
      </Link>
      <Link
        to={comCidade(CAMINHO_CADASTRO)}
        className="rounded-full bg-brand px-3.5 py-2 text-[12px] font-medium text-white outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-brand/40"
      >
        Criar conta
      </Link>
    </span>
  );
}

type Props = {
  /** Quem esta entrado, para o cabecalho dizer se ha conta e qual. */
  conta: EstadoDaConta;
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
  conta,
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
        <SeloDaConta conta={conta} />
      </div>
    </header>
  );
}
