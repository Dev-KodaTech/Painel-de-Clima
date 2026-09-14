/**
 * A primeira fatia do painel: buscar uma cidade e ver o card do dia.
 *
 * Os demais paineis (tendencia horaria, semana, sol, precipitacao, condicoes
 * previstas, cidades proximas) entram nos tickets seguintes, no grid de tres
 * faixas descrito na spec.
 */

import { useEffect, useState } from "react";
import { buscarPainel, mensagemDeErro } from "./api/client";
import type { Cidade, WeatherResponse } from "./api/types";
import { BuscaCidade } from "./components/BuscaCidade";
import { CardDoDia } from "./components/CardDoDia";

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
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-8">
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
            <div className="max-w-md">
              <CardDoDia
                location={estado.painel.location}
                current={estado.painel.current}
                units={estado.painel.units}
              />
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
