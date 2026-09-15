/**
 * Campo de busca com dropdown de desambiguacao.
 *
 * Cada candidata exibe estado e pais porque a busca do geocoding e fuzzy
 * ("Springfield" tambem traz "Palmyra") e ha homonimas legitimas: sem essa
 * procedencia a escolha seria as cegas.
 */

import { useEffect, useId, useRef, useState } from "react";
import {
  buscarCidadePorCoordenada,
  buscarCidades,
  mensagemDeErro,
} from "../api/client";
import type { Cidade } from "../api/types";
import { populacao, procedencia } from "../formato";
import { pedirLocalizacao, temGeolocalizacao } from "../localizacao";

/** Espera antes de consultar, para nao disparar a cada tecla digitada. */
const ESPERA_MS = 300;

/**
 * O alvo do botao de localizacao, desenhado inline.
 *
 * Os Meteocons do payload sao icones de tempo; este e de interface, e nao sai
 * de la. `aria-hidden` porque quem nomeia o botao e o seu `aria-label` — o
 * icone repetiria o mesmo texto para o leitor de tela.
 */
function Alvo({ animado }: { animado: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={`size-[18px] ${animado ? "animate-pulse" : ""}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    >
      <circle cx="12" cy="12" r="7" />
      <circle cx="12" cy="12" r="2.4" fill="currentColor" stroke="none" />
      <path d="M12 1.8v3M12 19.2v3M22.2 12h-3M4.8 12h-3" />
    </svg>
  );
}

type Props = {
  /**
   * O nome da cidade atualmente carregada, ou `null` se nenhuma.
   *
   * Existe porque a cidade mora na URL: um link colado ou o botao Voltar
   * carregam um painel sem que ninguem tenha digitado nada, e o campo ficaria
   * vazio ao lado de um painel cheio.
   */
  nomeDaCidade: string | null;
  onEscolher: (cidade: Cidade) => void;
};

/**
 * O resultado da busca em curso. `null` enquanto o termo e curto demais para
 * consultar; um unico estado evita a combinacao invalida "buscando com erro".
 */
type Resultado =
  | { tipo: "buscando" }
  | { tipo: "candidatas"; cidades: Cidade[] }
  | { tipo: "erro"; mensagem: string };

/**
 * O botao de localizacao, que so tem tres estados visiveis.
 *
 * Nao ha estado para "negada": negar e escolha do usuario, e a interface volta
 * ao repouso sem mensagem alguma — insistir seria importunar quem ja disse
 * nao. Nem para "nenhuma cidade perto": o campo fica vazio, que e o estado
 * inicial normal.
 */
type Localizando =
  | { tipo: "repouso" }
  | { tipo: "buscando" }
  | { tipo: "aviso"; mensagem: string };

export function BuscaCidade({ nomeDaCidade, onEscolher }: Props) {
  // Valor **inicial**, nao sincronizado: o `Cabecalho` remonta este componente
  // quando a cidade carregada muda (ver o `key` la). Remontar e o que faz o
  // campo seguir a URL sem um efeito que sobrescreva o que se esta digitando.
  const [termo, setTermo] = useState(nomeDaCidade ?? "");
  /**
   * O que de fato se consulta — separado do texto exibido no campo.
   *
   * Sao coisas diferentes: o campo tambem e preenchido por *escolher* uma
   * candidata e por uma cidade que veio da URL, e nenhum dos dois casos deve
   * abrir o dropdown. Com um estado so, escolher "Berlin" reabria a lista de
   * candidatas 300 ms depois, porque o texto novo disparava busca nova.
   */
  const [consulta, setConsulta] = useState("");
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [localizando, setLocalizando] = useState<Localizando>({
    tipo: "repouso",
  });
  const containerRef = useRef<HTMLDivElement>(null);
  const listaId = useId();

  // Lido uma vez: a presenca da API nao muda durante a sessao, e chama-la a
  // cada render nao diria nada novo.
  const [mostraBotao] = useState(temGeolocalizacao);

  useEffect(() => {
    const q = consulta.trim();
    // Menos de duas letras nao vale uma requisicao: a busca e fuzzy e
    // devolveria ruido.
    if (q.length < 2) return;

    const controller = new AbortController();
    const timer = setTimeout(() => {
      buscarCidades(q, controller.signal)
        .then((cidades) => setResultado({ tipo: "candidatas", cidades }))
        .catch((falha: unknown) => {
          if (controller.signal.aborted) return;
          setResultado({
            tipo: "erro",
            mensagem: mensagemDeErro(falha, "Falha na busca."),
          });
        });
    }, ESPERA_MS);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [consulta]);

  /** Digitar e o evento que abre a busca; o efeito apenas a resolve. */
  function digitar(texto: string) {
    setTermo(texto);
    setConsulta(texto);
    setResultado(texto.trim().length < 2 ? null : { tipo: "buscando" });
    // Digitar dispensa o aviso de localizacao: ele existe para dizer "use a
    // busca", e quem esta digitando ja o fez. Sem isto o aviso ficaria para
    // sempre, sobreposto ao dropdown de candidatas — os dois ocupam o mesmo
    // lugar sob o campo.
    setLocalizando({ tipo: "repouso" });
  }

  // Clicar fora fecha o dropdown sem apagar o que foi digitado.
  useEffect(() => {
    function aoClicarFora(evento: MouseEvent) {
      if (!containerRef.current?.contains(evento.target as Node)) {
        setResultado(null);
      }
    }
    document.addEventListener("mousedown", aoClicarFora);
    return () => document.removeEventListener("mousedown", aoClicarFora);
  }, []);

  function escolher(cidade: Cidade) {
    onEscolher(cidade);
    setTermo(cidade.name);
    // Escolher encerra a busca: sem zerar a consulta, o nome recem-escrito no
    // campo seria consultado de novo e o dropdown reabriria sozinho.
    setConsulta("");
    setResultado(null);
  }

  /**
   * Resolve a localizacao do navegador em cidade e carrega o painel direto.
   *
   * Sem pedir confirmacao: o usuario ja pediu ao clicar, e o nome fica visivel
   * no campo de busca para correcao. Uma segunda confirmacao seria friccao sem
   * proposito.
   *
   * A permissao e pedida **aqui**, no clique, e nunca no carregamento.
   */
  async function usarMinhaLocalizacao() {
    setLocalizando({ tipo: "buscando" });
    setResultado(null);

    const localizacao = await pedirLocalizacao();

    // Negar e escolha do usuario: volta ao repouso, sem mensagem.
    if (localizacao.tipo === "negada") {
      setLocalizando({ tipo: "repouso" });
      return;
    }

    if (localizacao.tipo === "indisponivel") {
      setLocalizando({
        tipo: "aviso",
        mensagem: "Nao foi possivel obter sua localizacao.",
      });
      return;
    }

    try {
      const cidade = await buscarCidadePorCoordenada(
        localizacao.latitude,
        localizacao.longitude,
      );
      // A mais de 50 km de qualquer cidade cadastrada nada e sugerido: o
      // estado inicial, de campo vazio, e melhor que uma cidade distante.
      setLocalizando({ tipo: "repouso" });
      if (cidade) escolher(cidade);
    } catch (falha: unknown) {
      setLocalizando({
        tipo: "aviso",
        mensagem: mensagemDeErro(falha, "Nao foi possivel obter sua localizacao."),
      });
    }
  }

  const candidatas =
    resultado?.tipo === "candidatas" ? resultado.cidades : null;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div className="flex items-center gap-2">
        <input
          type="search"
          value={termo}
          onChange={(evento) => digitar(evento.target.value)}
          onKeyDown={(evento) => {
            if (evento.key === "Escape") setResultado(null);
          }}
          placeholder="Buscar cidade…"
          aria-label="Buscar cidade"
          aria-controls={listaId}
          aria-expanded={candidatas !== null && candidatas.length > 0}
          className="w-full rounded-inner bg-card px-4 py-2.5 text-[13px] shadow-card outline-none placeholder:text-ink-3 focus:ring-2 focus:ring-brand/40"
        />

        {/* Sem `navigator.geolocation` o botao nao e renderizado: um alvo que
            nunca funciona e pior que a sua ausencia. */}
        {mostraBotao && (
          <button
            type="button"
            onClick={usarMinhaLocalizacao}
            disabled={localizando.tipo === "buscando"}
            aria-label="Usar minha localizacao"
            title="Usar minha localizacao"
            className="shrink-0 rounded-inner bg-card p-2.5 text-ink-2 shadow-card outline-none transition-colors hover:text-brand focus:ring-2 focus:ring-brand/40 disabled:text-ink-3"
          >
            <Alvo animado={localizando.tipo === "buscando"} />
          </button>
        )}
      </div>

      {/* Discreto de proposito: o painel continua usavel pela busca. */}
      {localizando.tipo === "aviso" && (
        <p role="status" className="absolute top-full mt-1.5 text-[11px] text-ink-2">
          {localizando.mensagem}
        </p>
      )}

      {resultado?.tipo === "buscando" && (
        <p className="absolute top-full mt-1.5 text-[11px] text-ink-3">Buscando…</p>
      )}

      {resultado?.tipo === "erro" && (
        <p role="status" className="absolute top-full mt-1.5 text-[11px] text-ink-2">
          {resultado.mensagem}
        </p>
      )}

      {/* Lista vazia e como a busca diz "nao encontrada". */}
      {candidatas?.length === 0 && (
        <p role="status" className="absolute top-full mt-1.5 text-[11px] text-ink-2">
          Cidade nao encontrada. Confira o nome e tente de novo.
        </p>
      )}

      {candidatas !== null && candidatas.length > 0 && (
        <ul
          id={listaId}
          className="absolute top-full z-10 mt-1.5 max-h-80 w-full overflow-y-auto rounded-inner bg-card py-1.5 shadow-card"
        >
          {candidatas.map((cidade) => {
            const habitantes = populacao(cidade.population);
            return (
              <li key={cidade.id}>
                <button
                  type="button"
                  onClick={() => escolher(cidade)}
                  className="flex w-full items-baseline justify-between gap-3 px-4 py-2 text-left hover:bg-brand-soft"
                >
                  <span className="text-[13px]">
                    {cidade.name}
                    <span className="ml-2 text-[11px] text-ink-2">
                      {procedencia(cidade.admin1, cidade.country)}
                    </span>
                  </span>
                  {habitantes && (
                    <span className="shrink-0 text-[11px] text-ink-3">{habitantes}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
