/**
 * A moldura comum dos tres paineis de metrica: chuva, umidade e vento.
 *
 * Os tres repetiam a mesma forma — uma faixa de numeros de resumo, um grafico
 * de 160 px sobre os dias da janela, e o resumo em texto para leitor de tela —,
 * e a repeticao nao era so verbosidade: o espacamento da faixa e a altura do
 * grafico precisam concordar entre eles, ou os cartoes desalinham no grid de
 * duas colunas. Centralizados aqui, mudar o espacamento e uma edicao, nao tres.
 *
 * O grafico entra como filho porque e a unica parte que de fato difere: barras
 * para a chuva, area para a umidade, linha para o vento.
 */

import type { ReactNode } from "react";
import { Painel } from "../Painel";
import { AreaDoGrafico } from "./AreaDoGrafico";
import { ResumoEmTexto } from "./ResumoEmTexto";

type Props = {
  titulo: string;
  /** Os numeros de resumo da faixa superior. */
  numeros: ReactNode;
  /** O grafico. Recebe a altura da `AreaDoGrafico`, comum aos tres. */
  children: ReactNode;
  /** A frase que substitui o grafico para quem usa leitor de tela. */
  resumoEmTexto: ReactNode;
};

/** A altura dos graficos de metrica, menor que a do historico, que e o principal. */
const ALTURA = 160;

export function PainelDeMetrica({
  titulo,
  numeros,
  children,
  resumoEmTexto,
}: Props) {
  return (
    <Painel titulo={titulo}>
      <div className="mb-4 flex flex-wrap gap-6">{numeros}</div>
      <AreaDoGrafico altura={ALTURA}>{children}</AreaDoGrafico>
      <ResumoEmTexto>{resumoEmTexto}</ResumoEmTexto>
    </Painel>
  );
}
