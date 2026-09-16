/**
 * As rotas.
 *
 * O `Shell` e rota de layout: barra lateral, cabecalho, busca e a requisicao
 * do painel ficam la, e as paginas entram pelo `Outlet`.
 *
 * Cadastro e entrada entram **fora** de `PAGINAS`: nao sao paginas da barra
 * lateral — ver `navegacao.tsx` — e por isso sao declaradas uma a uma, como a
 * Visao geral da raiz ja era.
 *
 * As paginas ainda nao construidas sao declaradas a partir de `PAGINAS`, a
 * mesma lista que desenha a barra lateral. Arquivos quase identicos seriam
 * outros tantos lugares para a navegacao e as rotas discordarem — e cada um
 * deles vai ser substituido por uma pagina de verdade, um a um. A Tendencia foi
 * a primeira; `CONSTRUIDAS` e por onde as proximas entram, sem que a lista de
 * navegacao precise saber quais ja existem.
 */

import type { ComponentType } from "react";
import { Route, Routes } from "react-router";
import { Shell } from "./components/Shell";
import {
  CAMINHO_CADASTRO,
  CAMINHO_ENTRADA,
  PAGINAS,
  ehRaiz,
} from "./navegacao";
import { Cadastro } from "./paginas/Cadastro";
import { CidadesVizinhas } from "./paginas/CidadesVizinhas";
import { Entrada } from "./paginas/Entrada";
import { NaoEncontrada } from "./paginas/NaoEncontrada";
import { PaginaVazia } from "./paginas/PaginaVazia";
import { Tendencia } from "./paginas/Tendencia";
import { VisaoGeral } from "./paginas/VisaoGeral";

/** As paginas que ja tem componente proprio; o resto cai na `PaginaVazia`. */
const CONSTRUIDAS: Record<string, ComponentType> = {
  "/tendencia": Tendencia,
  "/vizinhas": CidadesVizinhas,
};

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<VisaoGeral />} />

        <Route path={CAMINHO_CADASTRO} element={<Cadastro />} />
        <Route path={CAMINHO_ENTRADA} element={<Entrada />} />

        {PAGINAS.filter((pagina) => !ehRaiz(pagina.caminho)).map((pagina) => {
          const Construida = CONSTRUIDAS[pagina.caminho];
          return (
            <Route
              key={pagina.caminho}
              path={pagina.caminho}
              element={
                Construida ? <Construida /> : <PaginaVazia pagina={pagina} />
              }
            />
          );
        })}

        <Route path="*" element={<NaoEncontrada />} />
      </Route>
    </Routes>
  );
}
