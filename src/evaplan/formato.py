"""Formato ÚNICO de cifras para todo lo que lee una persona o una IA (pantalla, PDF, Excel, textos de alertas).

Convención (es-CO), siempre la misma para que ninguna IA tenga que adivinar:
  - Porcentajes: SIEMPRE con el símbolo % y en escala 0-100 ('22,3 %'). Nunca fracciones (0,223).
  - Pesos: '$' y punto de miles, sin decimales ('$ 3.884.965.483').
  - Cantidades: punto de miles y coma decimal ('12.000' = doce mil; '41,667' = cuarenta y uno coma seis…).
  - Sin dato: 'sin dato' (nunca 0 ni guiones).
"""
from __future__ import annotations

import math

SIN_DATO = "sin dato"

CONVENCIONES = (
    "Todos los porcentajes ya vienen calculados, en escala de 0 a 100 y con el símbolo % (ejemplo: 22,3 %). "
    "No hay porcentajes escritos como fracción (0,223).",
    "Los valores en pesos llevan el signo $ y punto de miles, sin decimales (ejemplo: $ 3.884.965.483).",
    "En las cantidades el punto separa miles y la coma separa decimales (12.000 = doce mil; 41,5 = cuarenta y uno "
    "coma cinco).",
    "'sin dato' significa que no hay información: no es cero.",
)


def es_na(x) -> bool:
    if x is None:
        return True
    try:
        return bool(math.isnan(float(x)))
    except (TypeError, ValueError):
        return str(x) in ("<NA>", "nan", "NaT")


def _es_co(texto_en: str) -> str:
    """'1,234,567.89' (formato inglés) -> '1.234.567,89'."""
    return texto_en.replace(",", "§").replace(".", ",").replace("§", ".")


def numero(x, max_decimales: int = 3) -> str:
    """Cantidad de un indicador: '12.000', '41,667', '0,5'. Quita ceros decimales sobrantes."""
    if es_na(x):
        return SIN_DATO
    v = float(x)
    if v.is_integer():
        return _es_co(f"{v:,.0f}")
    t = _es_co(f"{v:,.{max_decimales}f}").rstrip("0").rstrip(",")
    return t


def pesos(x) -> str:
    """'$ 3.884.965.483'."""
    return SIN_DATO if es_na(x) else "$ " + _es_co(f"{float(x):,.0f}")


def porcentaje(fraccion, decimales: int = 1) -> str:
    """De una fracción (0,223) a '22,3 %'."""
    return SIN_DATO if es_na(fraccion) else _es_co(f"{float(fraccion) * 100:,.{decimales}f}") + " %"


def porcentaje_100(valor, decimales: int = 1) -> str:
    """De un valor ya en escala 0-100 (22,3) a '22,3 %'."""
    return SIN_DATO if es_na(valor) else _es_co(f"{float(valor):,.{decimales}f}") + " %"


def puntos(fraccion, decimales: int = 1) -> str:
    """Diferencia entre dos porcentajes, en puntos porcentuales: '+12,5 puntos'."""
    if es_na(fraccion):
        return SIN_DATO
    return _es_co(f"{float(fraccion) * 100:+,.{decimales}f}") + " puntos"
