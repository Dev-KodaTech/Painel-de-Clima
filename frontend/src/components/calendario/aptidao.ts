/**
 * Como cada nivel de aptidao se mostra: a palavra, o anuncio e as classes.
 *
 * ## A palavra vem antes da cor, e nao junto dela
 *
 * A story 11 pede a aptidao **legivel sem enxergar cor**, e o requisito nao se
 * cumpre com um verde mais escuro: quem nao distingue verde de vermelho nao
 * distingue tom nenhum deles, e quem ouve a pagina nao recebe cor alguma. Por
 * isso cada celula pintada imprime a palavra — "boa", "media", "ruim" — e a cor
 * e o **reforco** que permite achar o dia numa olhada, que e a story 10.
 *
 * As duas stories pedem coisas diferentes e as duas sao atendidas: a cor serve
 * a varredura visual, o texto serve a leitura. Nenhuma das duas sozinha.
 *
 * ## As cores moram no `index.css`, e o contraste esta medido la
 *
 * Seis tokens — um preenchimento e uma cor de traco por nivel —, redefinidos no
 * bloco do tema escuro como todo o resto da paleta. **Nao sao constantes
 * daqui**: o tema vive num atributo do `<html>` e o seu estado em React e local
 * do `Cabecalho`, entao uma cor escolhida em JavaScript no render ficaria
 * congelada no tema em que a grade montou. O CSS nao tem esse problema.
 *
 * A medida que justificou cada uma, e o motivo de serem seis e nao tres —
 * o preenchimento sozinho fica em ~1,1:1 contra o cartao e nao distingue a
 * celula pintada da que nao esta —, estao no comentario dos tokens.
 */

import type {
  Atividade,
  DiaDoHorizonte,
  JulgamentoDeAptidao,
  NivelDeAptidao,
} from "../../api/types";

/**
 * O julgamento de um dia para a atividade escolhida, ou `null`.
 *
 * **A unica forma de procurar aptidao num dia**, e por isso mora aqui e nao na
 * celula que a desenha: dois lugares perguntam a mesma coisa — a celula, para
 * saber como se pintar, e a pagina, para saber se **algum** dia da semana serve
 * —, e duas copias do mesmo `find` divergiriam na primeira vez que a regra
 * ganhasse um caso.
 *
 * `null` em dois casos que quem chama trata igual: nenhuma atividade escolhida,
 * e dia do horizonte longo, que vem com a lista vazia (ausencia, e nao um nivel
 * "desconhecido" — ver `DiaDoHorizonte.aptidoes`).
 */
export function julgamentoDe(
  dia: DiaDoHorizonte,
  atividade: Atividade | null,
): JulgamentoDeAptidao | null {
  if (atividade === null) return null;
  return dia.aptidoes.find((j) => j.atividade === atividade) ?? null;
}

/**
 * As tres palavras que a celula imprime.
 *
 * Adjetivos curtos, e nao frases: cabem na celula da grade, que tem 104 px de
 * altura e ja mostra data, ceu, maxima e minima. A frase inteira — o *motivo* —
 * mora no detalhe do dia, que e onde ha espaco para ela (story 12).
 */
export const PALAVRA: Record<NivelDeAptidao, string> = {
  boa: "boa",
  media: "media",
  ruim: "ruim",
};

/**
 * O que o leitor de tela ouve no lugar do adjetivo solto.
 *
 * "boa" sozinho, depois de uma data e dois numeros, nao diz **boa para que** —
 * e a celula muda que a fatia 04 corrigiu, na versao auditiva. A frase so se
 * completa com o rotulo da atividade, que vem do backend; aqui fica a metade
 * que e do nivel.
 */
export const ANUNCIO: Record<NivelDeAptidao, string> = {
  boa: "dia bom para",
  media: "dia mediano para",
  ruim: "dia ruim para",
};

/**
 * As classes de cor do nivel: preenchimento, traco e texto.
 *
 * Escritas por extenso e nao montadas por interpolacao (`bg-aptidao-${nivel}`)
 * porque o Tailwind varre o codigo como **texto**: uma classe montada em tempo
 * de execucao nao aparece na varredura e nao entra no CSS gerado. E o modo de
 * falha classico, e ele nao aparece em teste de tipo — aparece como celula sem
 * cor nenhuma no navegador.
 */
export const CLASSES: Record<NivelDeAptidao, string> = {
  boa: "bg-aptidao-boa-fundo border-aptidao-boa-cor text-aptidao-boa-cor",
  media: "bg-aptidao-media-fundo border-aptidao-media-cor text-aptidao-media-cor",
  ruim: "bg-aptidao-ruim-fundo border-aptidao-ruim-cor text-aptidao-ruim-cor",
};

/**
 * So a cor do nivel, sem o preenchimento. **Dois usos, uma constante.**
 *
 * 1. **O texto secundario de uma celula pintada** — a minima e o "sem dado".
 *    A pintura mudou o fundo sob texto que ja estava la, e os tokens cinzas nao
 *    sobrevivem a ele: medido sobre os tres preenchimentos claros, `ink-2`
 *    (`#6b7280`) da 4,40 / 4,34 / 3,96 e `ink-3` (`#9ca3af`) da 2,31 / 2,28 /
 *    2,08 — todos abaixo do minimo de 4,5:1, o `ink-3` muito abaixo.
 *
 *    **E a mordida do INMET repetida ao contrario.** La o texto branco reprovou
 *    sobre as tres cores de severidade e virou preto fixo; aqui o cinza reprova
 *    sobre os tres preenchimentos. A licao daquela vez — medir o texto contra o
 *    fundo que ele **vai** ter, e nao contra o que ele tinha — e o que produziu
 *    esta constante. A cor do nivel ja foi medida sobre o seu proprio
 *    preenchimento (4,57 / 4,51 / 5,30 no claro; 7,66 / 7,89 / 5,35 no escuro),
 *    entao ela e a saida que ja passa nos dois temas.
 *
 * 2. **O nivel no detalhe do dia**, que lista as quatro aptidoes numa linha
 *    cada sobre o fundo do painel. Pintar quatro faixas inteiras ali faria um
 *    arco-iris onde o que importa e ler quatro julgamentos, entao a cor fica so
 *    no rotulo do nivel — sobre `bg-card`, onde foi medida em 5,02 / 5,02 /
 *    6,47 no claro e 9,45 / 9,87 / 5,96 no escuro.
 *
 * Uma constante e nao duas iguais: os dois usos querem exatamente "a cor deste
 * nivel sem fundo", e duas copias so dariam a chance de divergirem num rename.
 */
export const COR_DO_NIVEL: Record<NivelDeAptidao, string> = {
  boa: "text-aptidao-boa-cor",
  media: "text-aptidao-media-cor",
  ruim: "text-aptidao-ruim-cor",
};
