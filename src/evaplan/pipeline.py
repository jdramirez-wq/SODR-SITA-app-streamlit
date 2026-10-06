"""Orquestador de la página de seguimiento: archivos de entrada → resultado listo para mostrar y descargar.

Separado de Streamlit para poder probarlo. La página solo recoge archivos, llama a `ejecutar` y dibuja.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import aportes as A
from . import lectura as L
from . import recordatorios as R
from . import seguimiento as S
from . import validaciones as V


@dataclass
class Resultado:
    vigencia: int
    matriz: pd.DataFrame
    hallazgos: pd.DataFrame            # incoherencias objetivas por meta (seguimiento)
    calidad: pd.DataFrame              # reglas de integridad/cruces entre fuentes (validaciones)
    resumen: dict
    avisos: list[str] = field(default_factory=list)
    usa_drive: bool = False
    entidad: str = ""                       # '1216 · NOMBRE' de la(s) entidad(es) del export
    usa_z023: bool = False
    es_descentralizada: bool = False      # ¿la entidad del export es descentralizada? (certificados de cierre)
    z023_filas_por_vigencia: dict = field(default_factory=dict)   # {año: n.º de filas} del Z023 cargado
    z023_equivalencias: dict = field(default_factory=dict)        # {código EVAPLAN: código Z023} de las entidades
    aportes: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=A.COLUMNAS_APORTES))


def ejecutar(pi_mp_evaplan, centralizadas, drive=None, vigencia: int | None = None,
             criterio_flexible: bool = False, z023=None) -> Resultado:
    """`drive`: ruta, URL de exportación xlsx o archivo del Plan Indicativo (hoja MP). Opcional.

    Sin Drive el seguimiento funciona, pero no puede detectar metas sin reporte ni validar contra la programación.
    `z023`: Z023 consolidado (opcional, información no pública: solo en memoria). Agrega los aportes por meta.
    """
    avisos: list[str] = []
    pi = L.leer_pi_mp_evaplan(pi_mp_evaplan)
    ce = L.leer_centralizadas(centralizadas)
    dr = None
    if drive is not None:
        try:
            dr = L.leer_pi_drive_mp(drive)
        except L.EsquemaError:
            raise
        except Exception as e:                       # red, permisos, URL…
            avisos.append(f"No se pudo leer el Plan Indicativo de Drive ({type(e).__name__}: {e}). "
                          "Se continúa solo con los archivos de EVAPLAN.")
    if dr is not None and vigencia is None:
        vigencia = V.inferir_vigencia(dr)
    entidad = " / ".join(dict.fromkeys(f"{c} · {n}" for c, n in zip(pi["codigo_entidad"], pi["nombre_entidad"])
                                       if pd.notna(c)))
    zz = L.leer_z023(z023) if z023 is not None else None
    matriz = S.construir_matriz(pi, ce, dr, vigencia, criterio_flexible, z023=zz)
    vigencia = int(matriz["vigencia"].iloc[0]) if len(matriz) else (vigencia or 0)
    calidad = V.validar_todo(pi_mp_evaplan=pi, centralizadas=ce, drive_mp=dr, vigencia=vigencia, z023=zz)
    equivalencias = A.equivalencias_z023(A.entidades_de(pi, ce), zz) if zz is not None else {}
    aportes = A.construir_aportes(zz, matriz, vigencia, equivalencias) if zz is not None else None
    extra = ({"usa_z023": True, "aportes": aportes, "z023_equivalencias": equivalencias,
              "z023_filas_por_vigencia": {int(a): int(n) for a, n in zz["vigencia"].value_counts().sort_index().items()}}
             if aportes is not None else {})
    return Resultado(vigencia=vigencia, matriz=matriz, hallazgos=S.detectar_hallazgos(matriz, criterio_flexible), calidad=calidad,
                     resumen=S.resumen(matriz), avisos=avisos, usa_drive=dr is not None, entidad=entidad,
                     es_descentralizada=R.detectar_descentralizada(
                         ce, set(matriz["codigo_entidad"].dropna()) | set(ce["codigo_entidad"].dropna()), equivalencias),
                     **extra)


__all__ = ["Resultado", "ejecutar"]
