/**
 * Campo de busca com dropdown de desambiguacao.
 *
 * Cada candidata exibe estado e pais porque a busca do geocoding e fuzzy
 * ("Springfield" tambem traz "Palmyra") e ha homonimas legitimas: sem essa
 * procedencia a escolha seria as cegas.
 */

import { useEffect, useId, useRef, useState } from "react";
import { buscarCidades, mensagemDeErro } from "../api/client";
import type { Cidade } from "../api/types";
import { populacao, procedencia } from "../formato";

/** Espera antes de consultar, para nao disparar a cada tecla digitada. */
const ESPERA_MS = 300;

type Props = {
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

export function BuscaCidade({ onEscolher }: Props) {
  const [termo, setTermo] = useState("");
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const listaId = useId();

  useEffect(() => {
    const q = termo.trim();
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
  }, [termo]);

  /** Digitar e o evento que abre a busca; o efeito apenas a resolve. */
  function digitar(texto: string) {
    setTermo(texto);
    setResultado(texto.trim().length < 2 ? null : { tipo: "buscando" });
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
    setResultado(null);
  }

  const candidatas =
    resultado?.tipo === "candidatas" ? resultado.cidades : null;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
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
