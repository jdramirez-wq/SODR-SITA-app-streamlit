"""Seguimiento EVAPLAN: cruza lo reportado por la dependencia con el Plan Indicativo (Drive) y el Plan de Acción.

La lógica vive en src/evaplan (probada con archivos de ejemplo) y las vistas en interfaz/. Esta página solo
orquesta: recoge archivos, procesa y muestra.
"""
import io
import os
import sys
import urllib.request
from pathlib import Path

import streamlit as st

# Raíz del repositorio en sys.path: así `from src...` funciona aunque Streamlit se lance con esta página como
# archivo principal o desde otra carpeta (si no, falla con "No module named 'src'").
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from interfaz import estilos, seguimiento as vista
from src.evaplan import pipeline
from src.evaplan.lectura import EsquemaError
from src.evaplan.prompts import PERIODOS
from src.evaplan.recordatorios import recordatorios_cierre
from src.evaplan.version import version_codigo

st.set_page_config(page_title="Seguimiento EVAPLAN", page_icon="📊", layout="wide")
estilos.aplicar_estilos()


# ------------------------------------------------------------------ Drive
def _url_drive() -> str | None:
    """URL de exportación (xlsx) del Plan Indicativo. Va en Secrets de Streamlit, no en el código (repo público)."""
    try:
        url = st.secrets.get("URL_DRIVE_PLAN_INDICATIVO")
    except Exception:  # sin archivo de secretos
        url = None
    return url or os.environ.get("URL_DRIVE_PLAN_INDICATIVO")


@st.cache_data(ttl=600, show_spinner="Leyendo el Plan Indicativo de Drive…")
def _descargar_drive(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 (URL configurada por el administrador)
        return r.read()


# ------------------------------------------------------------------ barra lateral (solo lo esencial)
st.sidebar.markdown("### Revisión")
periodo = st.sidebar.selectbox(
    "Periodo de revisión", PERIODOS,
    help="Ajusta el texto del prompt. En los periodos de cierre aparecen además los recordatorios de certificados.")
with st.sidebar.expander("Opciones avanzadas"):
    vigencia_manual = st.number_input(
        "Vigencia (0 = detectar sola)", min_value=0, max_value=2027, value=0, step=1,
        help="Se detecta con los encabezados 'VAL ALC' del Plan Indicativo en Drive: la vigencia en curso es el "
             "primer año que aún no está marcado como logro.")
    con_hechos = st.checkbox("Decirle a la IA que las cifras ya están verificadas", value=True,
                             help="Agrega al prompt el bloque de 'hechos verificados'.")
    criterio_flexible = st.checkbox(
        "Criterio flexible para el avance 0", value=False,
        help="Por defecto (lineamiento del equipo) un avance 0 se justifica en Dificultades. Marca esta casilla solo "
             "si el equipo decide aceptar también el Análisis del logro.")
st.sidebar.caption(f"Versión del código: {version_codigo()}")
url_drive = _url_drive()

res = st.session_state.get("resultado")

# ------------------------------------------------------------------ encabezado
estilos.encabezado(
    "Seguimiento EVAPLAN",
    "Cruza lo que reportó una dependencia en EVAPLAN con el Plan Indicativo y su Plan de Acción, y deja listos los "
    "hechos para el análisis. No emite semáforos: el juicio es de quien revisa.",
    entidad=res.entidad if res is not None else "")
if res is None:
    estilos.pasos([("Descarga de EVAPLAN", "Dos archivos de la dependencia: Plan Indicativo MP y Plan de Acción."),
                   ("Cárgalos y procesa", "El Plan Indicativo de Drive se lee solo si está configurado."),
                   ("Revisa y descarga", "Metas con alertas primero, Excel, PDF y prompt para la IA.")])

# ------------------------------------------------------------------ carga de archivos
with st.expander("📁 Archivos de la dependencia", expanded=res is None):
    c1, c2 = st.columns(2)
    f_pi = c1.file_uploader("Plan Indicativo MP", type=["xlsx"], key="up_pi",
                            help="'Informe de Plan Indicativo MP.xlsx', descargado de EVAPLAN")
    f_ce = c2.file_uploader("Plan de Acción", type=["xlsx"], key="up_ce",
                            help="'Centralizadas.xlsx' o 'Descentralizadas.xlsx', descargado de EVAPLAN")
    f_dr = f_z = None
    if st.checkbox("Agregar fuentes opcionales (Plan Indicativo de Drive, Z023)", key="ver_opcionales"):
        o1, o2 = st.columns(2)
        f_dr = o1.file_uploader("Plan Indicativo de Drive (.xlsx)", type=["xlsx"], key="up_dr",
                                help="Solo si no hay enlace configurado o Drive no responde.")
        f_z = o2.file_uploader("Z023 consolidado (.xlsx o .xlsm)", type=["xlsx", "xlsm"], key="up_z023",
                               help="Muestra qué proyectos de otras entidades aportan a cada meta. Es información no "
                                    "pública: se usa solo en esta sesión y no se guarda.")
    listo = bool(f_pi and f_ce)
    b1, b2 = st.columns([1, 3], vertical_alignment="center")
    procesar = b1.button("Procesar", type="primary", disabled=not listo, use_container_width=True)
    b2.caption(("✅ Plan Indicativo de Drive conectado por enlace" if url_drive else
                "⚠️ Sin enlace al Plan Indicativo de Drive: no se detectarán las metas sin reporte")
               + ("" if listo else " · Sube los dos archivos de EVAPLAN para continuar"))

if procesar:
    try:
        with st.spinner("Cruzando EVAPLAN, Plan Indicativo y Plan de Acción…"):
            drive = f_dr
            if drive is None and url_drive:
                try:
                    drive = io.BytesIO(_descargar_drive(url_drive))
                except Exception as e:
                    st.warning(f"No se pudo leer Drive ({type(e).__name__}). Se continúa sin él: no se detectarán "
                               "metas sin reporte.")
            st.session_state["resultado"] = pipeline.ejecutar(f_pi, f_ce, drive, vigencia_manual or None,
                                                              criterio_flexible, z023=f_z)
        st.rerun()
    except EsquemaError as e:
        st.session_state.pop("resultado", None)
        st.error(f"**Un archivo no tiene la estructura esperada.** ¿Subiste cada archivo en su lugar?\n\n{e}")
    except Exception as e:
        st.session_state.pop("resultado", None)
        st.error(f"Ocurrió un error al procesar los archivos: {type(e).__name__}: {e}")

if res is None:
    st.stop()

# ------------------------------------------------------------------ resultados
for aviso in res.avisos:
    st.warning(aviso)
if not res.usa_drive:
    st.info("Sin el Plan Indicativo de Drive no se detectan las **metas sin reporte** ni se valida la programación. "
            "La vigencia se tomó del año actual.")
if res.usa_z023 and not res.z023_equivalencias:
    st.warning("No pude identificar la entidad del export en el Z023 (los códigos y nombres no coinciden): todos los "
               "proyectos del Z023 se muestran como de otras entidades.")

recordatorios = recordatorios_cierre(periodo, res.matriz, res.es_descentralizada, res.aportes if res.usa_z023 else None)
vista.barra_acciones(res, periodo, con_hechos, recordatorios)
vista.recordatorios_cierre(recordatorios)
vista.cifras(res)
vista.lista_y_ficha(res)
vista.detalle_tecnico(res)
