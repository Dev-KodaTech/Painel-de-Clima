/**
 * O mapa da regiao: a cidade escolhida no centro, as vizinhas em volta.
 *
 * E o que transforma uma distancia em posicao. A tabela diz "Potsdam, 26 km", e
 * 26 km nao diz para que lado — nem se as cinco vizinhas estao todas do mesmo
 * lado, nem se a cidade escolhida esta no meio delas ou na beira. O mapa
 * responde as tres de uma vez, e e a unica parte desta pagina que responde.
 *
 * ## Leaflet nao e React, e e por isso que este arquivo parece diferente
 *
 * Leaflet monta sobre um elemento do DOM e o governa por conta propria: cria
 * filhos, escuta eventos, guarda estado interno. React tambem quer governar o
 * que esta dentro do JSX. Os dois no mesmo elemento brigam — dai o `<div>` do
 * mapa ficar **vazio** no JSX, com `ref`, e tudo o que acontece nele acontecer
 * em efeito. O `<div>` e a fronteira: de fora dele, React; de dentro, Leaflet.
 *
 * A consequencia pratica e que este componente tem tres efeitos em vez de
 * renderizar. Ver cada um deles.
 *
 * ## Sem camadas meteorologicas
 *
 * O mapa mostra **onde as cidades ficam**, e nada mais. Chuva, nuvem e
 * temperatura em camadas exigiriam um segundo fornecedor com chave propria,
 * enquanto o `CONTEXT.md` descreve "a API externa" no singular — e a Open-Meteo
 * serve dados por coordenada, nao tiles. Ver o ADR 0006.
 *
 * ## Props, e nao o painel inteiro
 *
 * Recebe a cidade escolhida e as vizinhas ja como pontos, e nao o
 * `WeatherResponse`: o mapa nao tem nada a ver com previsao, unidade nem
 * atribuicao, e recebendo o payload inteiro qualquer mudanca nele passaria por
 * aqui. Assim ele serve a qualquer outra pagina que um dia queira um mapa —
 * que e o que a spec pede ao chama-lo de componente proprio.
 */

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

/**
 * Um ponto no mapa: uma cidade reduzida ao que o mapa desenha.
 *
 * Nome e coordenada, e nada mais. Temperatura, icone e distancia sao da tabela;
 * o mapa responde "para que lado fica", e um tipo que carregasse o clima
 * convidaria a responder outra pergunta.
 */
export type Ponto = {
  nome: string;
  latitude: number;
  longitude: number;
};

type Props = {
  escolhida: Ponto;
  vizinhas: Ponto[];
};

/**
 * Quanto respiro fica entre a cidade mais externa e a borda do mapa, em pixels.
 *
 * Sem ele o enquadramento encosta os marcadores na borda, e um marcador
 * encostado fica metade cortado — o pino e desenhado acima da coordenada.
 */
const RESPIRO = 48;

/**
 * O zoom maximo do enquadramento automatico.
 *
 * So morde no caso degenerado: uma cidade escolhida **sem vizinhas** enquadra um
 * ponto unico, e um ponto unico nao tem extensao — Leaflet daria o zoom maximo
 * do mapa e cairia na rua da cidade, que nao e um mapa de regiao. Com duas ou
 * mais cidades a extensao real manda, e este teto nunca e alcancado.
 */
const ZOOM_MAXIMO = 11;

export function MapaDaRegiao({ escolhida, vizinhas }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  /**
   * A camada que guarda os marcadores, separada do mapa.
   *
   * Existe para que trocar de cidade limpe **so os marcadores**: com eles
   * soltos no mapa, remove-los um a um exigiria guardar a lista anterior, e
   * esquecer um deixaria a cidade antiga marcada sobre a regiao nova. Um
   * `clearLayers` na camada e a operacao inteira.
   */
  const marcadores = useRef<L.LayerGroup | null>(null);

  /**
   * Cria o mapa uma vez, e o destroi ao desmontar.
   *
   * ## Sem dependencias, de proposito
   *
   * O arranjo vazio faz este efeito rodar na montagem e a limpeza no desmonte,
   * e nada mais. A cidade nao entra aqui: trocar de cidade nao recria o mapa —
   * recriar apagaria o zoom e o arrasto de quem estava explorando. Quem reage a
   * troca e o efeito de baixo.
   *
   * ## O `StrictMode` monta e desmonta duas vezes
   *
   * Em desenvolvimento o React roda montagem, limpeza e montagem de novo. Sem a
   * limpeza abaixo, a segunda montagem encontraria o `<div>` ja inicializado e
   * Leaflet lancaria "Map container is already initialized" — e, se nao
   * lancasse, restaria uma instancia orfa governando um DOM que ninguem ve,
   * segurando listeners de `resize` para sempre.
   *
   * `remove()` desfaz tudo o que `L.map` fez: os listeners, os filhos do
   * container e a marca interna que causa aquele erro. Zerar os refs depois
   * fecha o ciclo — um ref apontando para um mapa removido e um ponteiro para
   * algo que nao responde mais.
   */
  useEffect(() => {
    if (!container.current) return;

    const instancia = L.map(container.current, {
      // O scroll da roda dentro do mapa rolaria a pagina *e* daria zoom, ou
      // prenderia a rolagem da pagina num mapa que ocupa a largura toda.
      // Arrastar e os botoes +/- continuam, que e o que o ticket pede.
      scrollWheelZoom: false,
      // O controle padrao fica no canto superior esquerdo, onde cairia em cima
      // do primeiro marcador de uma regiao a noroeste.
      zoomControl: false,
    });

    L.control.zoom({ position: "topright" }).addTo(instancia);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      // **Obrigatorio pela licenca do OpenStreetMap**, e por isso mora aqui e
      // nao no rodape do `Shell`: o rodape vem do backend (`ATRIBUICAO` em
      // `models.py`) e viaja para todas as paginas, e so esta tem tiles. O
      // controle de atribuicao do proprio Leaflet e onde o credito fica junto
      // do que ele credita, aparecendo e sumindo com o mapa.
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(instancia);

    marcadores.current = L.layerGroup().addTo(instancia);
    mapa.current = instancia;

    return () => {
      instancia.remove();
      mapa.current = null;
      marcadores.current = null;
    };
  }, []);

  /**
   * Redesenha os marcadores e reenquadra quando a cidade escolhida muda.
   *
   * Um efeito so para os dois porque sao a mesma mudanca: as cidades novas e o
   * enquadramento que as cabe. Separa-los abriria um quadro com os marcadores
   * novos no enquadramento velho — Honolulu desenhada sobre a Alemanha.
   *
   * ## A dependencia e o texto das coordenadas, e nao o arranjo
   *
   * `vizinhas` e um arranjo novo a cada render do pai — `nearby.map(...)` —, e
   * um arranjo novo nunca e igual ao anterior por identidade: o efeito rodaria
   * em **todo** render, redesenhando marcadores e cancelando o zoom de quem
   * estivesse explorando o mapa a cada vez que a pagina renderizasse por
   * qualquer outro motivo. O texto e igual quando as cidades sao as mesmas,
   * que e a pergunta que o efeito de fato faz.
   */
  const cidades = [escolhida, ...vizinhas];
  // O nome entra na chave junto da coordenada porque ele **e desenhado** — vai
  // no popup e no `title`. So a coordenada bastaria para o enquadramento, mas
  // uma cidade que mudasse de nome sem mudar de lugar manteria o rotulo antigo
  // na tela, e o efeito nao redesenharia. `chaveDaLinha`, em `linhas.ts`, usa
  // so a coordenada porque la ela e **identidade**; aqui a chave e "o que, se
  // mudar, precisa ser redesenhado", que e outra pergunta.
  const chave = cidades
    .map((c) => `${c.latitude},${c.longitude},${c.nome}`)
    .join(";");

  useEffect(() => {
    const instancia = mapa.current;
    const camada = marcadores.current;
    if (!instancia || !camada) return;

    camada.clearLayers();

    // Pelo indice, e nao por `cidade === escolhida`: a comparacao por
    // identidade daria certo hoje — `cidades[0]` *e* a referencia recebida —,
    // mas silenciosamente marcaria duas cidades como escolhidas se um dia a
    // mesma referencia aparecesse tambem entre as vizinhas. O indice 0 e a
    // posicao que `cidades` acabou de construir, duas linhas acima.
    cidades.forEach((cidade, indice) => {
      const ehEscolhida = indice === 0;
      L.marker([cidade.latitude, cidade.longitude], {
        icon: iconeDaCidade(ehEscolhida),
        // A escolhida por cima: numa regiao densa os marcadores se sobrepoem, e
        // o que nao pode desaparecer sob outro e a referencia.
        zIndexOffset: ehEscolhida ? 1000 : 0,
        title: cidade.nome,
        alt: cidade.nome,
      })
        // Clicar identifica a cidade, que e o que liga o ponto a linha da
        // tabela. `escape` porque o nome vem do payload e entra como HTML.
        .bindPopup(
          `<strong>${escaparHtml(cidade.nome)}</strong>${
            ehEscolhida ? "<br><em>cidade escolhida</em>" : ""
          }`,
        )
        .addTo(camada);
    });

    // O enquadramento sai das coordenadas, nunca de um zoom fixo: as vizinhas
    // de Berlim cabem em dezenas de quilometros e as de Honolulu em milhares, e
    // um zoom fixo erraria os dois. `fitBounds` resolve o zoom **e** o centro a
    // partir da extensao real do conjunto.
    instancia.fitBounds(
      L.latLngBounds(cidades.map((c) => [c.latitude, c.longitude])),
      { padding: [RESPIRO, RESPIRO], maxZoom: ZOOM_MAXIMO },
    );
    // `cidades` e derivado de `chave`: as mesmas coordenadas e os mesmos nomes
    // produzem os mesmos marcadores e o mesmo enquadramento. Ver o cabecalho.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave]);

  return (
    <div
      ref={container}
      // A altura precisa ser explicita: Leaflet mede o container para calcular
      // o enquadramento, e um container de altura zero — que e o que um `<div>`
      // vazio tem — faria `fitBounds` enquadrar sobre nada.
      className="h-[360px] w-full rounded-inner"
      // O mapa e uma imagem interativa de terceiro, e nao ha texto alternativo
      // que descreva uma regiao. O rotulo nomeia o que e; a tabela ao lado
      // carrega a mesma informacao em texto, que e o caminho de quem nao ve.
      role="application"
      aria-label="Mapa da regiao, com a cidade escolhida e as cidades vizinhas"
    />
  );
}

/**
 * O marcador de uma cidade: um circulo, e nao o pino padrao do Leaflet.
 *
 * ## Por que nao o pino padrao
 *
 * Duas razoes, e qualquer uma bastaria. A primeira e que ele **nao sobrevive ao
 * bundler**: Leaflet resolve os PNGs do pino por caminho relativo ao CSS, o
 * Vite renomeia os arquivos no build, e o resultado classico e o mapa com
 * marcadores quebrados — o bug mais conhecido de Leaflet com empacotador. A
 * segunda e que o pino e uma imagem de cor fixa, e o marcador da cidade
 * escolhida precisa ser **distinto** do das vizinhas.
 *
 * Um `divIcon` e HTML comum: nao passa pelo bundler, herda os tokens de cor do
 * tema e distingue as duas cidades por tamanho e cor ao mesmo tempo.
 *
 * ## A distincao nao e so a cor
 *
 * A escolhida e maior, tem anel proprio e fica por cima. Cor sozinha deixaria
 * de fora quem nao a distingue — e o mesmo cuidado que a linha da tabela toma
 * com o rotulo "cidade escolhida", que aqui aparece no popup.
 */
function iconeDaCidade(ehEscolhida: boolean): L.DivIcon {
  const tamanho = ehEscolhida ? 18 : 12;

  return L.divIcon({
    className: "",
    // `border-card` e nao branco fixo: o aro separa o marcador do mapa, e no
    // tema escuro um aro branco seria o clarao que o filtro dos tiles evita.
    html: `<span class="block size-full rounded-full border-2 border-card ${
      ehEscolhida ? "bg-brand shadow-[0_0_0_4px_var(--color-brand-soft)]" : "bg-accent"
    }"></span>`,
    iconSize: [tamanho, tamanho],
    // Centrado na coordenada: um circulo marca o ponto onde esta, ao contrario
    // do pino, cuja ponta fica embaixo.
    iconAnchor: [tamanho / 2, tamanho / 2],
    popupAnchor: [0, -tamanho / 2],
  });
}

/**
 * O nome da cidade entra num `innerHTML`; um apostrofo ou `&` nao pode virar
 * marcacao. `Hawai'i Kai` e `Frankfurt (Oder)` sao nomes reais do payload.
 *
 * `escaparHtml` e nao `escape`: o nome curto sombraria a funcao global
 * depreciada de mesmo nome, que faz outra coisa (codifica URL).
 */
function escaparHtml(texto: string): string {
  return texto.replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );
}
