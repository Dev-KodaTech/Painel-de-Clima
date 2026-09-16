/**
 * A pagina Condicoes: alertas oficiais do INMET e condicoes previstas.
 *
 * Duas secoes separadas e rotuladas (ADR 0007), a de alertas acima. O painel
 * da Visao geral deduplica condicao prevista por categoria e corta em dois
 * cards, para caber numa altura fixa — `also_days: int` e a admissao de que o
 * dado por dia existe e esta sendo descartado. A segunda secao desta pagina e
 * o contrario: a semana de Wellington vira cinco itens de vento, com data e
 * rajada de cada um, em vez de um card dizendo "(+4 dias)". Os limiares sao os
 * mesmos de `condicoes.py`, so o colapso muda.
 *
 * ## Por que a requisicao mora aqui, e nao no `Shell`
 *
 * Regra do `docs/adr/0003-historico-e-buscado-na-pagina.md`: dado que so uma
 * pagina le, vai nela. So a Condicoes le `/api/condicoes` — as outras cinco
 * nunca leem um item por dia, so o par deduplicado (e agora possivelmente
 * precedido por alerta) que ja vem no painel.
 *
 * O custo aceito e o mesmo da Tendencia: sair da pagina e voltar refaz a
 * requisicao. O cache de dez minutos do backend absorve — a chamada reaproveita
 * a mesma previsao que `/api/weather` ja buscou para esta coordenada, sem
 * chamada extra a API externa dentro do TTL.
 *
 * ## Os cinco estados sao tratados aqui
 *
 * Como na Tendencia e em Cidades vizinhas: o carregamento e o erro da pagina
 * nao tocam no cabecalho nem na atribuicao, que vem do painel. Dentro do
 * estado "pronto", a secao de alertas tem os seus proprios tres estados —
 * ver `AlertasOficiais`.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { buscarCondicoes, mensagemDeErro } from "../api/client";
import type { AlertaOficial, CondicaoPrevista, StatusDosAlertas } from "../api/types";
import { cidadeDosParametros } from "../cidadeNaUrl";
import { AlertasOficiais } from "../components/AlertasOficiais";
import { Painel } from "../components/Painel";
import { WeatherIcon } from "../components/WeatherIcon";
import { usePainel } from "../estadoDoPainel";
import { diaDoCard } from "../formato";

/**
 * O que a requisicao devolveu, carimbado com a coordenada que a originou.
 *
 * O mesmo padrao da Tendencia: com a chave junto, "carregando" e derivado — um
 * resultado de outra cidade significa que o desta ainda nao chegou.
 */
type Resultado =
  | {
      chave: string;
      tipo: "pronto";
      alertas: AlertaOficial[];
      statusDosAlertas: StatusDosAlertas;
      condicoes: CondicaoPrevista[];
    }
  | { chave: string; tipo: "erro"; mensagem: string };

export function Condicoes() {
  const { estado } = usePainel();
  const [parametros] = useSearchParams();
  const [resultado, setResultado] = useState<Resultado | null>(null);

  const cidade = cidadeDosParametros(parametros);
  const latitude = cidade?.latitude;
  const longitude = cidade?.longitude;
  // Nao entra na chave: a consulta e a mesma para a mesma coordenada, e o
  // codigo do pais so acompanha a cidade — nunca muda sem que a coordenada
  // mude junto. Entra nas dependencias porque a requisicao o usa.
  const countryCode = cidade?.country_code ?? "";
  const chave = latitude === undefined ? null : `${latitude},${longitude}`;

  useEffect(() => {
    if (chave === null || latitude === undefined || longitude === undefined) {
      return;
    }

    const controller = new AbortController();

    buscarCondicoes(
      { latitude, longitude, country_code: countryCode },
      controller.signal,
    )
      .then((resposta) =>
        setResultado({
          chave,
          tipo: "pronto",
          alertas: resposta.alertas,
          statusDosAlertas: resposta.status_dos_alertas,
          condicoes: resposta.condicoes,
        }),
      )
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setResultado({
          chave,
          tipo: "erro",
          mensagem: mensagemDeErro(
            falha,
            "Nao foi possivel carregar as condicoes.",
          ),
        });
      });

    return () => controller.abort();
  }, [chave, latitude, longitude, countryCode]);

  // Nada, de proposito: o app ainda decide se abre com uma cidade, e a
  // instrucao de buscar uma seria errada por um instante.
  if (estado.tipo === "decidindo") return null;

  if (!cidade) {
    return (
      <p className="py-6 text-[13px] text-ink-2">
        Busque uma cidade para ver as condicoes.
      </p>
    );
  }

  const pronto = resultado?.chave === chave && resultado.tipo === "pronto";
  const erro =
    resultado?.chave === chave && resultado.tipo === "erro"
      ? resultado.mensagem
      : null;

  return (
    <section className="flex flex-col gap-4 py-2">
      <h2 className="text-lg font-semibold">Condicoes</h2>

      {!pronto && !erro && (
        <p role="status" className="py-6 text-[13px] text-ink-2">
          Carregando as condicoes…
        </p>
      )}

      {erro && (
        <p role="alert" className="py-6 text-[13px] text-ink-2">
          {erro}
        </p>
      )}

      {pronto && (
        <>
          <AlertasOficiais
            alertas={resultado.alertas}
            status={resultado.statusDosAlertas}
          />
          <ListaDeCondicoes condicoes={resultado.condicoes} />
        </>
      )}
    </section>
  );
}

function ListaDeCondicoes({ condicoes }: { condicoes: CondicaoPrevista[] }) {
  if (condicoes.length === 0) {
    return (
      <Painel titulo="Condicoes previstas">
        <div className="flex flex-col items-center justify-center gap-1 py-6">
          <WeatherIcon
            icon="clear-day"
            description="Nenhuma condicao severa"
            className="size-10"
          />
          <p className="text-[13px] font-medium">Sem condicoes severas</p>
          <p className="text-[11px] text-ink-3">nos proximos 7 dias</p>
        </div>
      </Painel>
    );
  }

  return (
    <Painel titulo="Condicoes previstas">
      <ul className="flex flex-col gap-2.5">
        {condicoes.map((item, indice) => (
          <li
            // A mesma categoria repete em dias diferentes (Wellington: cinco
            // itens de vento), entao `kind` sozinho nao identifica a linha —
            // par com a data, que junto com a categoria e unico na lista.
            key={`${item.kind}-${item.date}-${indice}`}
            className="flex items-center gap-3 rounded-inner bg-brand-soft p-2.5"
          >
            <WeatherIcon
              icon={item.icon}
              description={item.label}
              className="size-9 shrink-0"
            />
            <div className="min-w-0">
              <p className="text-[13px] font-semibold">{item.label}</p>
              <p className="text-[11px] text-ink-2">
                {diaDoCard(item.date)} · {item.detail}
              </p>
              {/* Em cada item, nao so no rodape: um item lido sozinho precisa
                  carregar a sua propria procedencia — ADR 0001, reafirmado
                  pelo ADR 0007. */}
              <p className="text-[10px] text-ink-3">Derivado da previsao</p>
            </div>
          </li>
        ))}
      </ul>
    </Painel>
  );
}
