/**
 * O painel: busca de cidade, card do dia, tendencia horaria, previsao da
 * semana, horarios do sol, cidades proximas, precipitacao e condicoes
 * previstas.
 *
 * O grid segue as tres faixas da spec, com proporcoes proprias em vez de doze
 * colunas — um grid de 12 nao reproduz as larguras do design.
 */

import { useEffect, useState } from "react";
import { buscarPainel, mensagemDeErro } from "./api/client";
import type { Cidade, WeatherResponse } from "./api/types";
import { BuscaCidade } from "./components/BuscaCidade";
import { CardDoDia } from "./components/CardDoDia";
import { CardSol } from "./components/CardSol";
import { CidadesProximas } from "./components/CidadesProximas";
import { CondicoesPrevistas } from "./components/CondicoesPrevistas";
import { Precipitacao } from "./components/Precipitacao";
import { PrevisaoSemana } from "./components/PrevisaoSemana";
import { TendenciaTemperatura } from "./components/TendenciaTemperatura";

/**
 * O painel e sempre um destes quatro estados, nunca uma combinacao deles.
 * Um unico estado impede o par invalido "carregando com erro" que tres
 * booleanos independentes permitiriam.
 */
type Estado =
  | { tipo: "vazio" }
  | { tipo: "carregando" }
  | { tipo: "pronto"; painel: WeatherResponse }
  | { tipo: "erro"; mensagem: string };

export default function App() {
  const [cidade, setCidade] = useState<Cidade | null>(null);
  const [estado, setEstado] = useState<Estado>({ tipo: "vazio" });

  useEffect(() => {
    if (!cidade) return;

    const controller = new AbortController();

    buscarPainel(cidade, controller.signal)
      .then((painel) => setEstado({ tipo: "pronto", painel }))
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setEstado({
          tipo: "erro",
          mensagem: mensagemDeErro(falha, "Nao foi possivel carregar o painel."),
        });
      });

    return () => controller.abort();
  }, [cidade]);

  return (
    <div className="min-h-screen">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-4 px-6 py-8">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-sm font-semibold">Painel de Clima</h1>
          <BuscaCidade
            onEscolher={(escolhida) => {
              // O clique e que inicia o carregamento: o efeito so busca.
              setEstado({ tipo: "carregando" });
              setCidade(escolhida);
            }}
          />
        </header>

        <main>
          {estado.tipo === "vazio" && (
            <p className="text-[13px] text-ink-2">
              Busque uma cidade para ver o tempo agora.
            </p>
          )}

          {estado.tipo === "carregando" && (
            <p role="status" className="text-[13px] text-ink-2">
              Carregando o painel…
            </p>
          )}

          {estado.tipo === "erro" && (
            <p role="alert" className="text-[13px] text-ink-2">
              {estado.mensagem}
            </p>
          )}

          {estado.tipo === "pronto" && (
            <div className="flex flex-col gap-4">
              {/* Faixa 1: card do dia e tendencia de temperatura. */}
              <div className="grid grid-cols-[1.05fr_1.5fr] gap-4">
                <CardDoDia
                  location={estado.painel.location}
                  current={estado.painel.current}
                  units={estado.painel.units}
                />
                <TendenciaTemperatura
                  hourly={estado.painel.hourly}
                  observedAt={estado.painel.current.observed_at}
                  units={estado.painel.units}
                />
              </div>

              {/* Faixa 2: previsao da semana, horarios do sol e cidades
                  proximas. */}
              <div className="grid grid-cols-[1.35fr_.75fr_1.1fr] gap-4">
                <PrevisaoSemana
                  daily={estado.painel.daily}
                  units={estado.painel.units}
                />
                <CardSol sun={estado.painel.sun} />
                <CidadesProximas
                  nearby={estado.painel.nearby}
                  units={estado.painel.units}
                />
              </div>

              {/* Faixa 3: precipitacao e condicoes previstas. Ambas leem os
                  mesmos sete dias que a faixa 2 exibe. */}
              <div className="grid grid-cols-[1.2fr_1fr] gap-4">
                <Precipitacao
                  daily={estado.painel.daily}
                  units={estado.painel.units}
                />
                <CondicoesPrevistas alerts={estado.painel.alerts} />
              </div>
            </div>
          )}
        </main>

        {estado.tipo === "pronto" && (
          <footer className="mt-2 text-[11px] text-ink-3">
            {estado.painel.attribution}
          </footer>
        )}
      </div>
    </div>
  );
}
