/**
 * A barra lateral: marca, as seis paginas e o icone de saida.
 *
 * Cada link **preserva os parametros de busca**. Sem isso, trocar de pagina
 * descartaria a cidade escolhida — que e justamente o que mora na URL — e a
 * pagina de destino abriria vazia.
 *
 * Os icones nao tem rotulo de texto: a faixa de 64 px do design nao comporta
 * um, e seis icones mudos sao anonimos para teclado e leitor de tela. Dai o
 * `aria-label` em cada link, com `title` para o tooltip do browser.
 */

import { Link, NavLink, useLocation } from "react-router";
import { IconeSaida } from "../icones";
import { PAGINAS, ehRaiz } from "../navegacao";
import { WeatherIcon } from "./WeatherIcon";

export function BarraLateral() {
  const { search } = useLocation();

  return (
    <nav
      aria-label="Paginas"
      // `sticky` com altura de viewport, e nao altura do conteudo: as paginas
      // ainda vazias deixariam a barra atrofiada em ~80 px.
      className="sticky top-8 flex h-[calc(100vh-4rem)] w-16 flex-col items-center gap-1.5 self-start rounded-card bg-card py-5 shadow-card"
    >
      {/* A marca leva ao inicio, como em qualquer site — e sem destaque de
          ativo, que pertence ao icone de grade. Alguem perdido em /ajustes
          clica nela antes de decifrar qual dos seis icones e o inicio. */}
      <Link
        to={{ pathname: "/", search }}
        aria-label="Painel de Clima, ir para o inicio"
        className="mb-5 rounded-inner outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
      >
        <WeatherIcon icon="partly-cloudy-day" description="" className="size-9" />
      </Link>

      {PAGINAS.map(({ caminho, titulo, Icone }) => (
        <NavLink
          key={caminho}
          to={{ pathname: caminho, search }}
          // A raiz e prefixo de todos os outros caminhos: sem `end` o icone de
          // grade ficaria permanentemente ativo.
          end={ehRaiz(caminho)}
          aria-label={titulo}
          title={titulo}
          className={({ isActive }) =>
            `grid size-10 place-items-center rounded-inner outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand/40 ${
              isActive
                ? "bg-brand-soft text-brand"
                : "text-ink-2 hover:bg-brand-soft/60 hover:text-brand"
            }`
          }
        >
          <Icone />
        </NavLink>
      ))}

      {/*
        Nao ha cadastro ainda, entao sair nao significa nada — decoracao
        inerte, como o cromo do cabecalho. Fica porque segura o lugar: quando o
        cadastro chegar, troca-se este `div` por um `button`, em vez de
        redesenhar o rodape da barra.
      */}
      <div aria-hidden="true" className="mt-auto text-ink-3">
        <IconeSaida />
      </div>
    </nav>
  );
}
