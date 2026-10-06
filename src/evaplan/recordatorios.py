"""Recordatorios de cierre de vigencia: lo que hay que SOLICITAR al cerrar el año. Sin Streamlit.

No son hallazgos sobre lo que reportó la entidad: son pendientes de la persona que revisa (certificados que el
sistema no trae). Se muestran en la página y se agregan al prompt para que el LLM los repita como advertencia al
final de su informe. Solo aplican en los periodos de cierre (ver `PERIODOS_CIERRE`).

Reglas (confirmadas por el equipo, 6-oct; el detalle de los certificados está por definir):
  - Entidades descentralizadas: registran ellas mismas su información financiera (no viene de SAP), así que a
    cierre de año hay que pedirles el certificado financiero.
  - Todas (centrales y descentralizadas): el avance declarado por gestión, donación, cofinanciación o sin costo
    requiere a cierre de año el certificado o soporte correspondiente.
"""
from __future__ import annotations

import pandas as pd

from .aportes import PREFIJO_DESCENTRALIZADA
from .prompts import PERIODOS

PERIODOS_CIERRE = tuple(PERIODOS[3:])      # "…Proyectada a Cierre de Vigencia" y "Revisión a Cierre de Vigencia"


def es_cierre(periodo: str) -> bool:
    return periodo in PERIODOS_CIERRE


def detectar_descentralizada(centralizadas: pd.DataFrame, codigos_entidad, equivalencias: dict[str, str]) -> bool:
    """¿La entidad del export es descentralizada?

    1) Si se cargó el Z023: su código allí empieza por '00' (las descentralizadas no tienen código de dependencia central).
    2) Si no: sus actividades no tienen código PS ('<proyecto>/1/1/01/01') sino código PPM numérico, sin '/'.
    """
    homologados = [equivalencias[c] for c in codigos_entidad if c in equivalencias]
    if homologados:
        return any(str(c).startswith(PREFIJO_DESCENTRALIZADA) for c in homologados)
    actividades = centralizadas["codigo_actividad"].dropna().astype(str)
    return bool(len(actividades)) and bool((~actividades.str.contains("/")).mean() >= 0.5)


def recordatorios_cierre(periodo: str, matriz: pd.DataFrame, es_descentralizada: bool = False,
                         aportes: pd.DataFrame | None = None) -> list[dict]:
    """Lista de {id, titulo, texto, metas}. Vacía si el periodo no es de cierre."""
    if not es_cierre(periodo):
        return []
    out = []
    if es_descentralizada:
        out.append({
            "id": "certificado_financiero_entidad",
            "titulo": "Certificado financiero de la entidad descentralizada",
            "texto": "Esta entidad registra ella misma su información financiera (no viene de SAP). A cierre de año "
                     "solicite su certificado financiero antes de dar por buenas las cifras de ejecución.",
            "metas": [],
        })
    if aportes is not None and len(aportes):
        desc = aportes[(aportes["tipo_entidad"] == "Descentralizada") & ~aportes["es_propia"]]
        if len(desc):
            nombres = sorted(desc["nombre_dependencia"].dropna().unique())
            out.append({
                "id": "certificado_financiero_aportantes",
                "titulo": "Certificados financieros de las descentralizadas que aportan a las metas",
                "texto": "Estas metas reciben aportes de entidades descentralizadas, que registran ellas mismas su "
                         "información financiera. A cierre de año solicite el certificado financiero a: "
                         + "; ".join(nombres) + ".",
                "metas": sorted(desc["codigo_mp"].unique()),
            })
    gestion = matriz[(matriz["estado_reporte"] == "Reportada") & matriz["menciona_gestion"].fillna(False).astype(bool)
                     & (matriz["resultado"].fillna(0) > 0)]
    if len(gestion):
        out.append({
            "id": "declaracion_avance_por_gestion",
            "titulo": "Certificados del avance declarado por gestión",
            "texto": "En estas metas el avance se declara por gestión, donación, cofinanciación o sin costo. A cierre "
                     "de año solicite el certificado o soporte correspondiente.",
            "metas": sorted(gestion["codigo_mp"]),
        })
    return out
