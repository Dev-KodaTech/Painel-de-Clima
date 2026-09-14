"""Tabela WMO: traduz o codigo inteiro em texto e nome de icone.

A Open-Meteo devolve `weather_code` apenas como inteiro — a unidade e
literalmente `"wmo code"`, e nao ha campo de texto. A traducao mora aqui, no
backend, para que o frontend nao conheca a tabela e a regra "todo dado vem do
backend" continue honesta.

Os nomes de icone seguem o conjunto Meteocons (`@bybas/weather-icons`), com as
variantes de dia e noite resolvidas por `is_day`.
"""

from dataclasses import dataclass

#: Texto exibido quando o codigo nao esta na tabela. A Open-Meteo documenta
#: 0-99, mas so ~28 sao emitidos; um codigo novo nao pode derrubar o painel.
DESCRICAO_DESCONHECIDA = "Condicao desconhecida"
ICONE_DESCONHECIDO = "not-available"


@dataclass(frozen=True)
class CondicaoWMO:
    """Uma linha da tabela: o texto e o icone de um codigo.

    `icon_dia` e `icon_noite` diferem apenas nos codigos em que o ceu limpo ou
    parcialmente nublado tem desenho proprio a noite (sol contra lua). Nos
    demais, ambos apontam para o mesmo nome.
    """

    description: str
    icon_dia: str
    icon_noite: str

    def icon(self, is_day: bool) -> str:
        return self.icon_dia if is_day else self.icon_noite


def _mesmo(description: str, icon: str) -> CondicaoWMO:
    """Condicao cujo icone nao muda entre dia e noite."""
    return CondicaoWMO(description=description, icon_dia=icon, icon_noite=icon)


def _dia_noite(description: str, icon_dia: str, icon_noite: str) -> CondicaoWMO:
    return CondicaoWMO(description=description, icon_dia=icon_dia, icon_noite=icon_noite)


#: Os codigos que a Open-Meteo de fato emite (0-3, 45, 48, 51-57, 61-67,
#: 71-77, 80-86, 95-99), confirmados contra respostas ao vivo.
TABELA_WMO: dict[int, CondicaoWMO] = {
    0: _dia_noite("Ceu limpo", "clear-day", "clear-night"),
    1: _dia_noite("Predominantemente limpo", "partly-cloudy-day", "partly-cloudy-night"),
    2: _dia_noite("Parcialmente nublado", "partly-cloudy-day", "partly-cloudy-night"),
    3: _mesmo("Nublado", "overcast"),
    45: _mesmo("Nevoeiro", "fog"),
    48: _mesmo("Nevoeiro com geada", "fog"),
    51: _mesmo("Garoa fraca", "drizzle"),
    53: _mesmo("Garoa moderada", "drizzle"),
    55: _mesmo("Garoa forte", "drizzle"),
    56: _mesmo("Garoa congelante fraca", "sleet"),
    57: _mesmo("Garoa congelante forte", "sleet"),
    61: _mesmo("Chuva fraca", "rain"),
    63: _mesmo("Chuva moderada", "rain"),
    65: _mesmo("Chuva forte", "rain"),
    66: _mesmo("Chuva congelante fraca", "sleet"),
    67: _mesmo("Chuva congelante forte", "sleet"),
    71: _mesmo("Neve fraca", "snow"),
    73: _mesmo("Neve moderada", "snow"),
    75: _mesmo("Neve forte", "snow"),
    77: _mesmo("Granizo fino", "snow"),
    80: _dia_noite("Pancadas de chuva fracas", "partly-cloudy-day-rain", "partly-cloudy-night-rain"),
    81: _mesmo("Pancadas de chuva", "rain"),
    82: _mesmo("Pancadas de chuva fortes", "rain"),
    85: _mesmo("Pancadas de neve fracas", "snow"),
    86: _mesmo("Pancadas de neve fortes", "snow"),
    95: _mesmo("Tempestade", "thunderstorms"),
    96: _mesmo("Tempestade com granizo leve", "thunderstorms-rain"),
    99: _mesmo("Tempestade com granizo forte", "thunderstorms-rain"),
}


def traduzir(weather_code: int, is_day: bool = True) -> tuple[str, str]:
    """Devolve `(description, icon)` para um codigo WMO.

    Um codigo fora da tabela devolve o par desconhecido em vez de levantar: a
    Open-Meteo nao versiona o vocabulario, e um codigo novo deve degradar o
    card, nunca derrubar a resposta inteira.
    """
    condicao = TABELA_WMO.get(weather_code)
    if condicao is None:
        return DESCRICAO_DESCONHECIDA, ICONE_DESCONHECIDO
    return condicao.description, condicao.icon(is_day)
