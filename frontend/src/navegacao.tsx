/**
 * As paginas da barra lateral, como dado — e os dois caminhos de conta, que
 * nao sao paginas da barra.
 *
 * O `CONTEXT.md` conta **oito** paginas; a lista abaixo tem sete. A que falta e
 * Locais salvos, que ainda nao existe — quando entrar, a lista e a contagem
 * voltam a bater. Ate la, "as oito paginas" nos comentarios deste projeto
 * significa o app que o glossario descreve, e nao o tamanho de `PAGINAS`.
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
  IconeJornal,
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
  /**
   * Se a pagina **nao** depende da cidade escolhida.
   *
   * Noticias e a unica: as materias sao nacionais e continuam as mesmas em
   * Sorocaba e em Belem (ADR 0009). Sem esta marca, ela mostraria "Busque uma
   * cidade" para depois exibir uma lista que nunca precisou de cidade alguma.
   *
   * Opcional e ausente por padrao porque a regra do app e a outra: sete das
   * oito paginas sao sobre uma cidade, e a excecao e que se declara.
   */
  semCidade?: boolean;
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
    titulo: "Condicoes",
    oQueVem:
      "Os alertas oficiais do INMET para a cidade escolhida, e um item por dia que dispara uma condicao severa prevista.",
    Icone: IconeLista,
  },
  {
    // Era `/semana`, titulada "Sete dias", e nao ganhou redirect: a pagina
    // nunca passou de um stub que renderizava a propria promessa, e um redirect
    // existe para nao quebrar link compartilhado. Ninguem compartilha o link de
    // uma pagina que nunca mostrou nada. `/semana` cai no `NaoEncontrada`, como
    // qualquer outra rota que nao existe.
    caminho: "/calendario",
    titulo: "Calendario",
    oQueVem:
      "Dezesseis dias numa grade, com uma fronteira no dia 8: ate la, icone, maxima, minima e a aptidao do dia para a atividade escolhida; depois, probabilidade de chuva e menos detalhe, porque a fonte ja e outro modelo. Para quem tem conta, os planos de cada dia ao lado.",
    Icone: IconeCalendario,
  },
  {
    caminho: "/noticias",
    titulo: "Noticias",
    oQueVem:
      "As noticias de clima e meio ambiente da Agencia Brasil, do Observatorio do Clima e da Pesquisa FAPESP, das mais recentes para as mais antigas.",
    Icone: IconeJornal,
    // A unica da barra que nao e sobre a cidade escolhida.
    semCidade: true,
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
 * permanencia visual das oito paginas do app — que ela nao tem. Sao telas que
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
 * lateral ja resolve isto em todos os seus links, pelo mesmo motivo; aqui a
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
 * As paginas sem busca no cabecalho.
 *
 * Eram uma — Ajustes —, e por isso isto era uma constante de um caminho so.
 * Noticias e a segunda, pelo mesmo motivo de fundo: **uma busca que aceita o
 * clique e nao muda nada na tela tem o defeito de um botao que nao responde.**
 *
 * As duas chegam ali por caminhos diferentes, e vale registrar: Ajustes nao
 * tem dado por tras, e Noticias tem — so que nacional (ADR 0009). Do lado de
 * quem usa, o efeito e o mesmo, e e o efeito que decide o cabecalho.
 *
 * Derivado de `PAGINAS` e nao escrito a mao: a pagina que declara `semCidade`
 * ja disse tudo o que era preciso, e uma segunda lista seria um lugar a mais
 * para discordar da primeira.
 */
const CAMINHO_DE_AJUSTES = "/ajustes";

const CAMINHOS_SEM_BUSCA = new Set([
  CAMINHO_DE_AJUSTES,
  ...PAGINAS.filter((pagina) => pagina.semCidade).map((pagina) => pagina.caminho),
]);

/** Se o cabecalho deve esconder a busca de cidade neste caminho. */
export const ehPaginaSemBusca = (caminho: string) =>
  CAMINHOS_SEM_BUSCA.has(caminho);
