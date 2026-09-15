/**
 * A Visao geral: o grid de nove paineis da cidade escolhida.
 *
 * O grid segue as tres faixas da spec, com proporcoes proprias em vez de doze
 * colunas — um grid de 12 nao reproduz as larguras do design.
 *
 * Os quatro estados do painel sao tratados **aqui**, e nao no `Shell`. Se o
 * Shell os tratasse, ele renderizaria "busque uma cidade" no lugar da pagina, e
 * as cinco paginas ainda vazias nunca chegariam a mostrar o que sao.
 */

import { usePainel } from "../estadoDoPainel";
import { CardDoDia } from "../components/CardDoDia";
import { CardSol } from "../components/CardSol";
import { CidadesProximas } from "../components/CidadesProximas";
import { CondicoesPrevistas } from "../components/CondicoesPrevistas";
import { Precipitacao } from "../components/Precipitacao";
import { PrevisaoSemana } from "../components/PrevisaoSemana";
import { TendenciaTemperatura } from "../components/TendenciaTemperatura";

export function VisaoGeral() {
  const { estado } = usePainel();

  // Nada, de proposito: o app ainda esta decidindo se abre com uma cidade, e
  // "Busque uma cidade" seria a instrucao errada por um instante.
  if (estado.tipo === "decidindo") return null;

  if (estado.tipo === "vazio") {
    return (
      <p className="py-6 text-[13px] text-ink-2">
        Busque uma cidade para ver o tempo agora.
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

  return (
    <div className="flex flex-col gap-4">
      {/* Faixa 1: card do dia e tendencia de temperatura. */}
      <div className="grid grid-cols-[1.05fr_1.5fr] gap-4">
        <CardDoDia
          location={painel.location}
          current={painel.current}
          units={painel.units}
        />
        <TendenciaTemperatura
          hourly={painel.hourly}
          observedAt={painel.current.observed_at}
          units={painel.units}
        />
      </div>

      {/* Faixa 2: previsao da semana, horarios do sol e cidades vizinhas. */}
      <div className="grid grid-cols-[1.35fr_.75fr_1.1fr] gap-4">
        <PrevisaoSemana daily={painel.daily} units={painel.units} />
        <CardSol sun={painel.sun} />
        <CidadesProximas nearby={painel.nearby} units={painel.units} />
      </div>

      {/* Faixa 3: precipitacao e condicoes previstas. Ambas leem os mesmos
          sete dias que a faixa 2 exibe. */}
      <div className="grid grid-cols-[1.2fr_1fr] gap-4">
        <Precipitacao daily={painel.daily} units={painel.units} />
        <CondicoesPrevistas alerts={painel.alerts} />
      </div>
    </div>
  );
}
