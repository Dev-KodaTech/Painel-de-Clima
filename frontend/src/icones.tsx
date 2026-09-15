/**
 * Icones de interface, desenhados inline.
 *
 * Os Meteocons de `@bybas/weather-icons` sao icones de *tempo*, resolvidos a
 * partir do payload — grade, sino e engrenagem nao saem de la. Uma biblioteca
 * de icones inteira para os treze desenhos abaixo seria uma dependencia nova
 * por algumas centenas de bytes de `path`.
 *
 * Todos `aria-hidden`: quem nomeia o controle e o seu `aria-label`, e o icone
 * repetiria o mesmo texto para o leitor de tela. Os do cabecalho nao nomeiam
 * controle nenhum — sao enfeite, e enfeite nao se anuncia.
 */

import type { ReactNode } from "react";

type Props = { className?: string };

/** A moldura comum: 24x24, traco de 1.8, sem preenchimento. */
function Traco({ children, className = "size-[18px]" }: Props & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  );
}

export function IconeGrade(props: Props) {
  return (
    <Traco {...props}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.6" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.6" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.6" />
    </Traco>
  );
}

export function IconeBarras(props: Props) {
  return (
    <Traco {...props}>
      <path d="M4 20V4" />
      <path d="M8 20v-6M12 20v-10M16 20v-4M20 20v-8" />
    </Traco>
  );
}

export function IconePino(props: Props) {
  return (
    <Traco {...props}>
      <path d="M12 21.5s7-6.3 7-11.5a7 7 0 1 0-14 0c0 5.2 7 11.5 7 11.5Z" />
      <circle cx="12" cy="10" r="2.6" />
    </Traco>
  );
}

export function IconeLista(props: Props) {
  return (
    <Traco {...props}>
      <path d="M8.5 6.5h11M8.5 12h11M8.5 17.5h11" />
      <path d="M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01" />
    </Traco>
  );
}

export function IconeCalendario(props: Props) {
  return (
    <Traco {...props}>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2.4" />
      <path d="M3.5 9.8h17M8.3 3v4M15.7 3v4" />
    </Traco>
  );
}

/**
 * A engrenagem.
 *
 * Aro largo com furo no meio e dentes **encostados no aro**. A primeira versao
 * — centro pequeno com raios longos partindo dele — era indistinguivel do sol
 * do cabecalho: o que separa um do outro e o raio destacado do centro, nao o
 * numero de pontas.
 */
export function IconeEngrenagem(props: Props) {
  return (
    <Traco {...props}>
      {/* Aro e dentes no mesmo traco de 2.4: sao uma peca so, e um aro mais
          fino que os dentes leria como sol de raios curtos — justamente a
          confusao que este redesenho existe para desfazer. O furo fica no
          traco fino, que e o que o faz parecer furo e nao terceiro anel. */}
      <circle cx="12" cy="12" r="7" strokeWidth="2.4" />
      <circle cx="12" cy="12" r="2.7" />
      <path
        strokeWidth="2.4"
        d="M12 2.8v2.2M12 19v2.2M21.2 12H19M5 12H2.8M18.51 5.49l-1.56 1.56M7.05 16.95l-1.56 1.56M18.51 18.51l-1.56-1.56M7.05 7.05 5.49 5.49"
      />
    </Traco>
  );
}

export function IconeSaida(props: Props) {
  return (
    <Traco {...props}>
      <path d="M15 3.5h3.5a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H15" />
      <path d="M10 8l-4 4 4 4M6 12h9.5" />
    </Traco>
  );
}

export function IconeSol(props: Props) {
  return (
    <Traco {...props}>
      <circle cx="12" cy="12" r="4.2" />
      <path d="M12 2.6v2.4M12 19v2.4M21.4 12H19M5 12H2.6M18.6 5.4l-1.7 1.7M7.1 16.9l-1.7 1.7M18.6 18.6l-1.7-1.7M7.1 7.1 5.4 5.4" />
    </Traco>
  );
}

export function IconeLua(props: Props) {
  return (
    <Traco {...props}>
      <path d="M20 14.2A8.4 8.4 0 0 1 9.8 4a8.4 8.4 0 1 0 10.2 10.2Z" />
    </Traco>
  );
}

export function IconeEnvelope(props: Props) {
  return (
    <Traco {...props}>
      <rect x="2.8" y="5" width="18.4" height="14" rx="2.6" />
      <path d="m3.6 7.2 7.2 5.1a2 2 0 0 0 2.4 0l7.2-5.1" />
    </Traco>
  );
}

export function IconeSino(props: Props) {
  return (
    <Traco {...props}>
      <path d="M18 9a6 6 0 1 0-12 0c0 5-2 6.5-2 6.5h16S18 14 18 9Z" />
      <path d="M13.7 19a2 2 0 0 1-3.4 0" />
    </Traco>
  );
}

/** Silhueta neutra: nao ha cadastro, e um rosto inventado seria um usuario falso. */
export function IconePessoa(props: Props) {
  return (
    <Traco {...props}>
      <circle cx="12" cy="8.4" r="3.8" />
      <path d="M4.8 20.2a7.2 7.2 0 0 1 14.4 0" />
    </Traco>
  );
}
