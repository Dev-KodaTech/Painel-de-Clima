/**
 * As seis paginas da barra lateral, como dado.
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
 * Ajustes e a unica pagina que nao e sobre uma cidade, e por isso a unica sem
 * busca no cabecalho: uma busca que aceita o clique e nao mostra resultado tem
 * o mesmo defeito de um botao que nao responde.
 */
export const CAMINHO_SEM_BUSCA = "/ajustes";
