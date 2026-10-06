"""Periodo de revisión: tipo (parcial, proyección de cierre o cierre) y mes de corte. Sin Streamlit.

Antes había 5 periodos fijos (primer trimestre, primer semestre…). Las revisiones pueden hacerse a cualquier mes
(p. ej. acumulado a octubre), así que el periodo se describe con dos datos y el prompt se arma a partir de ellos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre")

TIPOS = {
    "parcial": "Corte parcial (acumulado a un mes)",
    "proyectado": "Acumulado y proyección de cierre",
    "cierre": "Cierre definitivo de la vigencia",
}


@dataclass(frozen=True)
class Periodo:
    tipo: str = "parcial"     # clave de TIPOS
    mes: int = 12             # mes de corte (1-12); en 'cierre' siempre 12

    def __post_init__(self):
        if self.tipo not in TIPOS:
            raise ValueError(f"Tipo de revisión desconocido: {self.tipo}")
        if not 1 <= self.mes <= 12:
            raise ValueError(f"Mes de corte inválido: {self.mes}")

    @property
    def nombre_mes(self) -> str:
        return MESES[self.mes - 1]

    @property
    def etiqueta(self) -> str:
        if self.tipo == "cierre":
            return "Cierre de vigencia"
        if self.tipo == "proyectado":
            return f"Acumulado a {self.nombre_mes} y proyección de cierre"
        return f"Acumulado a {self.nombre_mes}"

    @property
    def es_cierre(self) -> bool:
        """Revisiones de cierre (definitivo o proyectado): activan los recordatorios de certificados."""
        return self.tipo in ("proyectado", "cierre")


def mes_por_defecto(hoy: date | None = None) -> int:
    """El último mes cerrado: en noviembre se revisa el acumulado a octubre."""
    hoy = hoy or date.today()
    return max(1, hoy.month - 1)


# Compatibilidad con los nombres de periodo anteriores (prompts guardados, pruebas).
_ANTERIORES = {
    "Revisión acumulada de primer trimestre": Periodo("parcial", 3),
    "Revisión acumulada del Primer semestre": Periodo("parcial", 6),
    "Revisión Acumulada de Tercer Semestre": Periodo("parcial", 9),
    "Revisión Acumulada y Proyectada a Cierre de Vigencia": Periodo("proyectado", 11),
    "Revisión a Cierre de Vigencia": Periodo("cierre", 12),
}


def como_periodo(valor) -> Periodo:
    """Acepta un Periodo o uno de los nombres anteriores."""
    if isinstance(valor, Periodo):
        return valor
    if valor in _ANTERIORES:
        return _ANTERIORES[valor]
    raise ValueError(f"Periodo no reconocido: {valor!r}")
