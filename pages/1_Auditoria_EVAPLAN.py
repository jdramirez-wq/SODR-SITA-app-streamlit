"""Seguimiento EVAPLAN: cruza lo reportado por la dependencia con el Plan Indicativo (Drive) y el Plan de Acción.

La lógica vive en src/evaplan (probada con archivos de ejemplo). Esta página solo recoge archivos y dibuja.
"""
import io
import os
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st

# Raíz del repositorio en sys.path: así `from src...` funciona aunque Streamlit se lance con esta página como
# archivo principal o desde otra carpeta (si no, falla con "No module named 'src'").
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaplan import pipeline, reportes
from src.evaplan.lectura import EsquemaError
from src.evaplan.prompts import PERIODOS, generar_prompt_sistema
from src.evaplan.seguimiento import ETIQUETAS
from src.evaplan.version import version_codigo

st.set_page_config(page_title="Seguimiento EVAPLAN", page_icon="📊", layout="wide")
st.markdown(
    """<style>
    div[data-testid="stHeader"] {background-color: transparent;}
    footer {visibility: hidden;}
    </style>""",
    unsafe_allow_html=True,
)

st.title("📊 Seguimiento EVAPLAN al Plan de Desarrollo")
st.write(
    "Sube las descargas de **una dependencia** desde EVAPLAN. La herramienta las cruza con el Plan Indicativo "
    "en Drive, calcula los hechos objetivos (avance, ejecución financiera, metas sin reporte) y deja listo el "
    "material para el análisis. **No emite semáforos**: el juicio sigue siendo de quien revisa."
)


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


# ------------------------------------------------------------------ barra lateral
st.sidebar.header("⚙️ Configuración")
periodo = st.sidebar.selectbox("Periodo de revisión (para el prompt):", PERIODOS)
vigencia_manual = st.sidebar.number_input(
    "Vigencia (0 = detectar automáticamente)", min_value=0, max_value=2027, value=0, step=1,
    help="Se detecta con los encabezados 'VAL ALC' del Plan Indicativo en Drive: la vigencia en curso es el "
         "primer año que aún no está marcado como logro.")
con_hechos = st.sidebar.checkbox("Incluir 'hechos verificados' en el prompt", value=True,
                                 help="Indica al LLM que las cifras ya fueron calculadas por código.")
url_drive = _url_drive()
st.sidebar.markdown("**Plan Indicativo (Drive)**")
st.sidebar.write("✅ Conectado por enlace" if url_drive else "⚠️ Sin enlace configurado (secreto `URL_DRIVE_PLAN_INDICATIVO`)")
st.sidebar.caption(f"Versión del código: {version_codigo()}")

# ------------------------------------------------------------------ carga de archivos
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("1. Plan Indicativo MP")
    f_pi = st.file_uploader("'Informe de Plan Indicativo MP.xlsx' (EVAPLAN)", type=["xlsx"], key="up_pi")
with c2:
    st.subheader("2. Centralizadas")
    f_ce = st.file_uploader("'Centralizadas.xlsx' (EVAPLAN)", type=["xlsx"], key="up_ce")
with c3:
    st.subheader("3. Plan Indicativo (Drive)")
    f_dr = st.file_uploader("Opcional: libro del Plan Indicativo en .xlsx", type=["xlsx"], key="up_dr",
                            help="Solo si no hay enlace configurado o Drive no responde.")

if f_pi and f_ce and st.button("🚀 Procesar", type="primary"):
    try:
        with st.spinner("Cruzando EVAPLAN, Plan Indicativo y Plan de Acción…"):
            drive = f_dr
            if drive is None and url_drive:
                try:
                    drive = io.BytesIO(_descargar_drive(url_drive))
                except Exception as e:
                    st.warning(f"No se pudo leer Drive ({type(e).__name__}). Se continúa sin él: no se detectarán "
                               "metas sin reporte.")
            st.session_state["resultado"] = pipeline.ejecutar(f_pi, f_ce, drive, vigencia_manual or None)
    except EsquemaError as e:
        st.session_state.pop("resultado", None)
        st.error(f"**Un archivo no tiene la estructura esperada.** ¿Subiste cada archivo en su lugar?\n\n{e}")
    except Exception as e:
        st.session_state.pop("resultado", None)
        st.error(f"Ocurrió un error al procesar los archivos: {type(e).__name__}: {e}")

res = st.session_state.get("resultado")
if res is None:
    st.info("💡 Sube **Plan Indicativo MP** y **Centralizadas** para empezar.")
    st.stop()

# ------------------------------------------------------------------ resultados
for aviso in res.avisos:
    st.warning(aviso)
if not res.usa_drive:
    st.warning("Sin el Plan Indicativo de Drive no se detectan las **metas sin reporte** ni se valida la "
               "programación. La vigencia se tomó del año actual.")

m = res.matriz
R = res.resumen
st.caption(f"Vigencia analizada: **{res.vigencia}** · Periodo del prompt: {periodo}")
k = st.columns(5)
k[0].metric("Metas en el Plan Indicativo", R["metas_en_plan_indicativo"])
k[1].metric("Reportadas en EVAPLAN", R["metas_reportadas"])
k[2].metric("Sin reporte", R["metas_sin_reporte"])
k[3].metric("Con alertas objetivas", R["metas_con_alertas"])
k[4].metric("% ejecución financiera", f"{R['ppto_obligaciones'] / R['ppto_definitivo'] * 100:.1f} %"
            if R["ppto_definitivo"] else "—")

tab_res, tab_mat, tab_hal, tab_cal, tab_out = st.tabs(
    ["Resumen", "Matriz por meta", "Hallazgos", "Calidad de datos", "Descargas y prompt"])


def _vista(df: pd.DataFrame) -> pd.DataFrame:
    """Copia para mostrar: fracciones como porcentaje y nombres legibles."""
    d = df.copy()
    for c in ("pct_avance_vigencia", "pct_avance_pg", "pct_ejecucion_financiera", "avance_actividades",
              "brecha_meta_vs_actividades"):
        if c in d:
            d[c] = d[c].astype("Float64") * 100
    return d


PCT = {c: st.column_config.NumberColumn(ETIQUETAS[c].replace(" (0-1)", ""), format="%.1f %%")
       for c in ("pct_avance_vigencia", "pct_avance_pg", "pct_ejecucion_financiera", "avance_actividades",
                 "brecha_meta_vs_actividades")}
DINERO = {c: st.column_config.NumberColumn(ETIQUETAS[c], format="$ %,.0f")
          for c in ("ppto_definitivo", "ppto_obligaciones", "ppto_disponible")}

with tab_res:
    sin = m[m["estado_reporte"] != "Reportada"]
    if len(sin):
        st.subheader(f"⛔ Metas sin reporte ({len(sin)})")
        st.caption("Están en el Plan Indicativo pero no vienen en el export de EVAPLAN (probable: la dependencia no reportó).")
        st.dataframe(sin[["codigo_mp", "descripcion_mp", "comportamiento", "meta_vigencia"]].rename(columns=ETIQUETAS),
                     hide_index=True, use_container_width=True)
    st.subheader("Hallazgos por tipo")
    if res.hallazgos.empty:
        st.success("Sin hallazgos objetivos.")
    else:
        st.dataframe(res.hallazgos.groupby(["severidad", "regla"]).size().rename("metas").reset_index(),
                     hide_index=True, use_container_width=True)
    st.subheader("Plan de acción vs. meta")
    st.dataframe(
        _vista(m[m["tiene_plan_de_accion"]])[["codigo_mp", "pct_avance_vigencia", "pct_ejecucion_financiera",
                                              "avance_actividades", "brecha_meta_vs_actividades"]]
        .rename(columns=ETIQUETAS),
        column_config={ETIQUETAS[c]: v for c, v in PCT.items()}, hide_index=True, use_container_width=True)
    st.caption("La brecha es un número, no un veredicto: sin cronograma de ejecución no hay umbral único.")

with tab_mat:
    f1, f2, f3 = st.columns([2, 2, 3])
    estados = f1.multiselect("Estado del reporte", sorted(m["estado_reporte"].unique()),
                             default=sorted(m["estado_reporte"].unique()))
    solo_alertas = f2.checkbox("Solo metas con alertas")
    texto = f3.text_input("Buscar (código o descripción)")
    v = m[m["estado_reporte"].isin(estados)]
    if solo_alertas:
        v = v[v["n_alertas"] > 0]
    if texto:
        v = v[v["codigo_mp"].str.contains(texto, case=False, na=False)
              | v["descripcion_mp"].astype("string").str.contains(texto, case=False, na=False)]
    cols = ["codigo_mp", "estado_reporte", "comportamiento", "meta_vigencia", "resultado", "pct_avance_vigencia",
            "valor_proyectado", "pct_avance_pg", "ppto_definitivo", "ppto_obligaciones", "pct_ejecucion_financiera",
            "avance_actividades", "n_alertas"]
    st.dataframe(_vista(v)[cols].rename(columns=ETIQUETAS),
                 column_config={ETIQUETAS[c]: x for c, x in {**PCT, **DINERO}.items()},
                 hide_index=True, use_container_width=True)
    with st.expander("Ver todas las columnas"):
        st.dataframe(_vista(v).rename(columns=ETIQUETAS), hide_index=True, use_container_width=True)

    st.subheader("Ficha de la meta")
    if len(v):
        mp = st.selectbox("Meta", v["codigo_mp"], format_func=lambda c: f"{c} · {m.set_index('codigo_mp').loc[c, 'descripcion_mp']}"[:140])
        f = m.set_index("codigo_mp").loc[mp]
        a, b, c, d = st.columns(4)
        a.metric("Meta vigencia", f"{f['meta_vigencia']:g}" if pd.notna(f["meta_vigencia"]) else "NP")
        b.metric("Resultado (acumulado)", f"{f['resultado']:g}" if pd.notna(f["resultado"]) else "—")
        c.metric("% vs meta", f"{f['pct_avance_vigencia'] * 100:.1f} %" if pd.notna(f["pct_avance_vigencia"]) else "—")
        d.metric("Proyección de cierre", f"{f['valor_proyectado']:g}" if pd.notna(f["valor_proyectado"]) else "sin dato")
        st.write(f"**Comportamiento:** {f['comportamiento']} · **Proyectos:** {f['proyectos'] if pd.notna(f['proyectos']) else 'sin plan de acción'}")
        st.write(f"**Avance de actividades por proyecto:** {f['avance_por_proyecto'] if pd.notna(f['avance_por_proyecto']) else '—'}")
        if f["alertas"]:
            st.warning(f["alertas"])
        for titulo, col in (("Principal logro", "principal_logro"), ("Análisis del logro", "analisis_logro"),
                            ("Dificultades o gestiones", "dificultades_gestiones")):
            st.markdown(f"**{titulo}:** {f[col] if pd.notna(f[col]) else '_(vacío)_'}")

with tab_hal:
    sev = st.multiselect("Severidad", ["error", "advertencia", "info"], default=["error", "advertencia", "info"])
    h = res.hallazgos[res.hallazgos["severidad"].isin(sev)]
    st.dataframe(h.drop(columns=["fila_excel", "fuente"]), hide_index=True, use_container_width=True)
    st.caption("Son incoherencias objetivas (no necesitan umbral). La gravedad y el dictamen los decide quien revisa.")

with tab_cal:
    st.write("Reglas de integridad y comparación entre fuentes (EVAPLAN vs. Plan Indicativo, presupuesto, avance).")
    if res.calidad.empty:
        st.success("Sin observaciones de calidad de datos.")
    else:
        st.dataframe(res.calidad, hide_index=True, use_container_width=True)

with tab_out:
    d1, d2 = st.columns(2)
    d1.download_button("📥 Matriz integrada (Excel)", reportes.a_excel(m, res.hallazgos, res.calidad),
                       file_name="MP_PI_PA_Integrado.xlsx", use_container_width=True,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d2.download_button("📥 Reporte por meta (PDF) para el LLM", reportes.a_pdf(m),
                       file_name="MP_PI_PA_Reporte.pdf", mime="application/pdf", use_container_width=True)
    st.markdown("---")
    st.subheader("🤖 Asistente de Auditoría EVAPLAN (prompt listo)")
    with st.expander("📋 Ver y copiar el prompt para Gemini / ChatGPT", expanded=True):
        st.markdown("💡 **Paso 1:** copia el prompt con el icono de la esquina superior derecha del bloque.")
        st.code(generar_prompt_sistema(periodo, res.vigencia, con_hechos), language="markdown", wrap_lines=True)
        st.markdown("🚀 **Paso 2:** pégalo en la IA y luego adjunta el PDF y el Excel descargados.")
        g1, g2 = st.columns(2)
        g1.link_button("🌐 Ir a Google Gemini Web", "https://gemini.google.com/", use_container_width=True, type="primary")
        g2.link_button("💬 Ir a ChatGPT (alternativo)", "https://chatgpt.com/", use_container_width=True)
