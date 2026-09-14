import { useEffect, useState } from "react";

type Health = {
  status: string;
  service: string;
};

/**
 * Esqueleto: prova que o caminho frontend -> proxy do Vite -> backend esta
 * ligado, com a paleta e a tipografia do design ja aplicadas. Sera substituido
 * pelos nove paineis.
 */
export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<Health>;
      })
      .then(setHealth)
      .catch(() => setFailed(true));
  }, []);

  return (
    <main className="grid min-h-screen place-items-center p-4">
      <section className="w-full max-w-md rounded-card bg-card p-[18px] shadow-card">
        <h1 className="text-sm font-semibold">Painel de Clima</h1>
        <p className="mt-1 text-[13px] text-ink-2">
          Esqueleto do ambiente de desenvolvimento.
        </p>

        <p className="mt-4 text-[11px] tracking-wide text-ink-3 uppercase">
          Backend
        </p>
        <p className="mt-1 text-[13px]">
          {failed
            ? "Backend indisponivel — suba o uvicorn e recarregue."
            : health
              ? `${health.service}: ${health.status}`
              : "Carregando…"}
        </p>
      </section>
    </main>
  );
}
