/**
 * Icone Meteocons resolvido a partir do campo `icon` do payload.
 *
 * O nome vem pronto do backend — aqui so vira caminho de arquivo. Os SVGs sao
 * importados em bloco (`import.meta.glob` com `eager`), o que faz o Vite
 * resolver as URLs em build e evita concatenar caminho em runtime.
 */

const ARQUIVOS = import.meta.glob<string>(
  "../../node_modules/@bybas/weather-icons/production/fill/all/*.svg",
  { eager: true, query: "?url", import: "default" },
);

const POR_NOME: Record<string, string> = Object.fromEntries(
  Object.entries(ARQUIVOS).map(([caminho, url]) => [
    caminho.split("/").pop()!.replace(".svg", ""),
    url,
  ]),
);

type Props = {
  /** Nome vindo de `current.icon`, ja resolvido pela tabela WMO do backend. */
  icon: string;
  /** Texto vindo de `current.description`: o icone nao inventa o seu proprio. */
  description: string;
  className?: string;
};

export function WeatherIcon({ icon, description, className }: Props) {
  const url = POR_NOME[icon] ?? POR_NOME["not-available"];
  return <img src={url} alt={description} className={className} />;
}
