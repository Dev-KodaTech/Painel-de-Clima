/**
 * As seis paginas da barra lateral, como dado — e os dois caminhos de conta,
 * que nao sao paginas da barra.
 *
 * Uma lista so: a barra lateral desenha os icones a partir dela e o `App`
 * declara as rotas a partir dela. Acrescentar uma pagina e acrescentar uma
 * linha aqui — nao dois arquivos que precisam concordar.
 *
 * Os caminhos sao em portugues: a fronteira de idioma do projeto cai na API,
 * nao na interface, e URL e interface. Nao existe `/painel` — *painel* nomeia
 * um cartao do grid (ver `CONTEXT.md`), e uma rota com esse nome recriaria a
 * ambiguidade que o glossario desfez. Por isso a Visao geral fica na raiz.
 */

import type { ComponentType } from "react";
import { useLocation } from "react-router";
import {
  IconeBarras,
  IconeCalendario,
  IconeEngrenagem,
  IconeGrade,
  IconeLista,
  IconePino,
} from "./icones";

export type Pagina = {
  caminho: string;
  /** Nomeia o icone mudo para leitor de tela e no tooltip do browser. */
  titulo: string;
  /**
   * O que a pagina vai mostrar, exibido enquanto ela esta vazia.
   *
   * Uma pagina que renderiza so o titulo e indistinguivel de rota quebrada; a
   * frase diz, ao mesmo tempo, que a navegacao funciona e o que falta.
   */
  oQueVem: string;
  Icone: ComponentType<{ className?: string }>;
};

export const PAGINAS: Pagina[] = [
  {
    caminho: "/",
    titulo: "Visao geral",
    oQueVem: "O grid de nove paineis da cidade escolhida.",
    Icone: IconeGrade,
  },
  {
    caminho: "/tendencia",
    titulo: "Tendencia",
    oQueVem:
      "O historico climatologico da cidade comparado com o mesmo periodo do ano anterior, mais chuva, umidade, vento e indice UV na janela temporal escolhida.",
    Icone: IconeBarras,
  },
  {
    caminho: "/vizinhas",
    titulo: "Cidades vizinhas",
    oQueVem:
      "As cidades vizinhas e a cidade escolhida numa tabela comparativa, com distancia, condicao e temperatura lado a lado.",
    Icone: IconePino,
  },
  {
    caminho: "/condicoes",
    titulo: "Condicoes previstas",
    oQueVem:
      "As condicoes severas derivadas da previsao, sem o limite de dois cards do painel. Ainda nao construida.",
    Icone: IconeLista,
  },
  {
    caminho: "/semana",
    titulo: "Sete dias",
    oQueVem:
      "A previsao dos sete dias expandida, com mais que icone, maxima e minima. Ainda nao construida.",
    Icone: IconeCalendario,
  },
  {
    caminho: "/ajustes",
    titulo: "Ajustes",
    oQueVem:
      "Preferencias do painel. Ainda nao ha nenhuma — e a unica pagina sem dado por tras.",
    Icone: IconeEngrenagem,
  },
];

/** A raiz e prefixo de todas as outras: sem `end` o icone de grade ficaria
 *  sempre ativo. */
export const ehRaiz = (caminho: string) => caminho === "/";

/**
 * Cadastro e entrada, que **nao** entram em `PAGINAS`.
 *
 * Ficam de fora da lista porque a lista e a barra lateral: os icones sao
 * desenhados a partir dela, e dois icones a mais dariam a conta a mesma
 * permanencia visual das seis paginas do app — que ela nao tem. Sao telas que
 * se visita uma vez, alcancadas pelo cabecalho.
 *
 * Tambem nao tem `oQueVem` nem `Icone`, que sao os campos que so fazem sentido
 * para uma pagina da barra. Constantes, e nao literais espalhados: quatro
 * arquivos apontam para estes dois caminhos.
 */
export const CAMINHO_CADASTRO = "/cadastro";
export const CAMINHO_ENTRADA = "/entrada";

/** Se o caminho e uma das telas de conta. */
export const ehTelaDeConta = (caminho: string) =>
  caminho === CAMINHO_CADASTRO || caminho === CAMINHO_ENTRADA;

/**
 * Um destino que **preserva a cidade escolhida**.
 *
 * A cidade mora nos parametros da URL (ADR 0002), e um `<Link to="/entrada">`
 * seco os descartaria: quem entrasse a partir de um painel carregado voltaria
 * para o app sem cidade nenhuma, e o painel recomecaria do zero. A barra
 * lateral ja resolve isto nos seus seis links, pelo mesmo motivo; aqui a
 * mesma regra vira hook porque quem a usa sao quatro lugares diferentes.
 *
 * Hook, e nao funcao que le `window.location`: o `search` precisa vir do
 * roteador para que trocar de cidade re-renderize quem depende dele. Lido do
 * `window`, o destino de um `<Link>` ja montado continuaria apontando para a
 * cidade que havia quando ele montou.
 */
export function useComCidade(): (pathname: string) => {
  pathname: string;
  search: string;
} {
  const { search } = useLocation();
  return (pathname) => ({ pathname, search });
}

/**
 * Ajustes e a unica pagina que nao e sobre uma cidade, e por isso a unica sem
 * busca no cabecalho: uma busca que aceita o clique e nao mostra resultado tem
 * o mesmo defeito de um botao que nao responde.
 */
export const CAMINHO_SEM_BUSCA = "/ajustes";
