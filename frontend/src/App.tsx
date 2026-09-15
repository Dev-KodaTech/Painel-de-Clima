/**
 * As rotas.
 *
 * O `Shell` e rota de layout: barra lateral, cabecalho, busca e a requisicao
 * do painel ficam la, e as paginas entram pelo `Outlet`.
 *
 * As cinco paginas ainda nao construidas sao declaradas a partir de `PAGINAS`,
 * a mesma lista que desenha a barra lateral. Cinco arquivos quase identicos
 * seriam cinco lugares para a navegacao e as rotas discordarem — e cada um
 * deles vai ser substituido por uma pagina de verdade, um a um.
 */

import { Route, Routes } from "react-router";
import { Shell } from "./components/Shell";
import { PAGINAS, ehRaiz } from "./navegacao";
import { NaoEncontrada } from "./paginas/NaoEncontrada";
import { PaginaVazia } from "./paginas/PaginaVazia";
import { VisaoGeral } from "./paginas/VisaoGeral";

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<VisaoGeral />} />

        {PAGINAS.filter((pagina) => !ehRaiz(pagina.caminho)).map((pagina) => (
          <Route
            key={pagina.caminho}
            path={pagina.caminho}
            element={<PaginaVazia pagina={pagina} />}
          />
        ))}

        <Route path="*" element={<NaoEncontrada />} />
      </Route>
    </Routes>
  );
}
