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
  /**
   * O icone e **redundante** onde esta, e o leitor de tela deve pula-lo.
   *
   * Existe por causa da celula da grade do Calendario, que ja anuncia a
   * descricao no `aria-label` do dia inteiro — com o `alt` preenchido, quem
   * ouve a celula ouviria "chuva" duas vezes na mesma frase.
   *
   * `alt=""` e nao `aria-hidden`: e o que marca uma imagem como decorativa sem
   * tira-la da arvore de acessibilidade por outro caminho. E e um parametro, e
   * nao a omissao de `description`, porque o icone continua precisando saber o
   * que desenha — o que muda e so quem o anuncia.
   */
  decorativo?: boolean;
};

export function WeatherIcon({
  icon,
  description,
  className,
  decorativo = false,
}: Props) {
  const url = POR_NOME[icon] ?? POR_NOME["not-available"];
  return (
    <img src={url} alt={decorativo ? "" : description} className={className} />
  );
}
