"""Vistas de la página de Seguimiento EVAPLAN. Solo dibuja: qué mostrar lo decide src/evaplan (vista.py)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.evaplan import reportes
from src.evaplan.aportes import ETIQUETAS_APORTES
from src.evaplan.prompts import generar_prompt_sistema
from src.evaplan.reglas import etiqueta_regla, etiquetar
from src.evaplan.seguimiento import ETIQUETAS
from src.evaplan.vista import FILTROS, alertas_de, contar_filtros, filtrar_metas, lineas_por_proyecto, tabla_metas

from . import estilos


def _md(texto) -> str:
    """Escapa el signo $ para que Markdown no lo tome por una fórmula matemática."""
    return str(texto).replace("$", "\\$")


def _pesos(x) -> str:
    return "—" if pd.isna(x) else "$ " + f"{float(x):,.0f}".replace(",", ".")


def _pct(x, decimales: int = 1) -> str:
    return "sin dato" if pd.isna(x) else f"{float(x) * 100:.{decimales}f} %"


def _num(x) -> str:
    return "—" if pd.isna(x) else f"{float(x):g}"


# ------------------------------------------------------------------ cifras y acciones
def cifras(res) -> None:
    R, m = res.resumen, res.matriz
    fin = f"{R['ppto_obligaciones'] / R['ppto_definitivo'] * 100:.1f} %" if R["ppto_definitivo"] else "—"
    estilos.tarjetas([
        ("Metas del Plan Indicativo", str(R["metas_en_plan_indicativo"]), f"{R['metas_reportadas']} reportadas en EVAPLAN", False),
        ("Sin reporte", str(R["metas_sin_reporte"]), "No aparecen en el export de EVAPLAN", R["metas_sin_reporte"] > 0),
        ("Requieren revisión", str(R["metas_con_alertas"]), "Metas con alguna advertencia", R["metas_con_alertas"] > 0),
        ("Ejecución financiera", fin, f"{_pesos(R['ppto_obligaciones'])} de {_pesos(R['ppto_definitivo'])}", False),
    ])


@st.cache_data(show_spinner=False, max_entries=3)
def _entregables(matriz: pd.DataFrame, hallazgos: pd.DataFrame, calidad: pd.DataFrame,
                 aportes: pd.DataFrame | None) -> tuple[bytes, bytes]:
    """Excel y PDF: se generan una sola vez por resultado (no en cada clic de la pantalla)."""
    return reportes.a_excel(matriz, hallazgos, calidad, aportes), reportes.a_pdf(matriz)


@st.dialog("Prompt para el asistente de IA", width="large")
def _dialogo_prompt(texto: str) -> None:
    st.markdown("**1.** Copia el prompt con el icono de la esquina del recuadro.  \n"
                "**2.** Pégalo en la IA y adjunta el PDF y el Excel descargados.")
    st.code(texto, language="markdown", wrap_lines=True)
    a, b = st.columns(2)
    a.link_button("Abrir Google Gemini", "https://gemini.google.com/", use_container_width=True, type="primary")
    b.link_button("Abrir ChatGPT", "https://chatgpt.com/", use_container_width=True)


def barra_acciones(res, periodo: str, con_hechos: bool, recordatorios: list[dict]) -> None:
    excel, pdf = _entregables(res.matriz, res.hallazgos, res.calidad, res.aportes if res.usa_z023 else None)
    c0, c1, c2, c3 = st.columns([3.2, 1, 1, 1.3], vertical_alignment="center")
    c0.caption(f"Vigencia **{res.vigencia}** · Periodo de revisión: {periodo}")
    c1.download_button("⬇ Excel", excel, file_name="MP_PI_PA_Integrado.xlsx", use_container_width=True,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       help="Matriz integrada, hallazgos, metas sin reporte y calidad de datos")
    c2.download_button("⬇ PDF", pdf, file_name="MP_PI_PA_Reporte.pdf", mime="application/pdf",
                       use_container_width=True, help="Un reporte por meta, listo para adjuntar al asistente de IA")
    if c3.button("🤖 Prompt para IA", use_container_width=True, type="primary",
                 help="Instrucciones para el asistente de auditoría (Gemini / ChatGPT)"):
        _dialogo_prompt(generar_prompt_sistema(periodo, res.vigencia, con_hechos, recordatorios))


def recordatorios_cierre(recordatorios: list[dict]) -> None:
    if not recordatorios:
        return
    with st.container(border=True):
        st.markdown(f"**⚠️ Cierre de vigencia: {len(recordatorios)} "
                    f"{'recordatorio' if len(recordatorios) == 1 else 'recordatorios'} para solicitar certificados**")
        for r in recordatorios:
            st.markdown(f"- **{r['titulo']}.** {r['texto']}")
            if r["metas"]:
                st.caption("Metas: " + ", ".join(r["metas"]))
        st.caption("Son pendientes de quien revisa, no hallazgos sobre lo que reportó la entidad. "
                   "También se agregan al prompt.")


# ------------------------------------------------------------------ lista de metas + ficha
def lista_y_ficha(res) -> None:
    m, h = res.matriz, res.hallazgos
    conteo = contar_filtros(m)
    st.subheader("Metas")
    etiquetas = {f"{f} ({conteo[f]})": f for f in FILTROS if f in conteo}
    elegido = st.segmented_control("Mostrar", list(etiquetas), default=list(etiquetas)[0],
                                   label_visibility="collapsed", key="filtro_metas")
    filtro = etiquetas.get(elegido, "Todas")
    reglas = sorted({etiqueta_regla(r): r for r in h["regla"]}.items())
    a, b = st.columns([2, 1.4])
    texto = a.text_input("Buscar", placeholder="Buscar por código o descripción de la meta",
                         label_visibility="collapsed")
    tipo = b.selectbox("Tipo de hallazgo", ["Cualquier hallazgo", *[n for n, _ in reglas]],
                       label_visibility="collapsed")
    regla = dict(reglas).get(tipo)

    v = filtrar_metas(m, h, filtro, texto, regla)
    if v.empty:
        st.info("Ninguna meta coincide con el filtro.")
        return
    t = tabla_metas(v)
    config = {"Alertas": st.column_config.NumberColumn("Alertas", format="%d", width=70),
              "Meta": st.column_config.TextColumn("Meta", width=190),
              "Código": st.column_config.TextColumn("Código", width=160),
              "Reportó": st.column_config.TextColumn("Reportó", width=75),
              "Otras entidades": st.column_config.NumberColumn("Otras entidades", format="%d", width=95)}
    for c in ("% de la meta", "Ejecución fin.", "Avance act."):
        config[c] = st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f%%", width=100)
    evento = st.dataframe(t, hide_index=True, use_container_width=True, column_config=config,
                          height=min(42 + 35 * len(t), 390), on_select="rerun", selection_mode="single-row",
                          key=f"tabla_{filtro}_{tipo}_{texto}")
    filas = evento.selection.rows
    st.caption(f"{len(t)} {'meta' if len(t) == 1 else 'metas'}, primero las que tienen más alertas. "
               + ("" if filas else "Haz clic en una fila para ver su ficha; por ahora se muestra la primera."))
    ficha(res, v.iloc[filas[0] if filas else 0]["codigo_mp"])


def ficha(res, codigo_mp: str) -> None:
    f = res.matriz.set_index("codigo_mp").loc[codigo_mp]
    revision, info = alertas_de(res.hallazgos, codigo_mp)
    with st.container(border=True):
        st.markdown(f'<span class="ficha-codigo">{codigo_mp}</span>', unsafe_allow_html=True)
        st.markdown(f'<p class="ficha-titulo">{f["descripcion_mp"]}</p>', unsafe_allow_html=True)
        estilos.chips([str(f["comportamiento"]) if pd.notna(f["comportamiento"]) else "", str(f["unidad_medida"])
                       if pd.notna(f["unidad_medida"]) else "", f["estado_reporte"]])

        c = st.columns(4)
        c[0].metric("Meta de la vigencia", "No programada" if f["meta_vigencia_np"] else _num(f["meta_vigencia"]))
        c[1].metric("Resultado acumulado", _num(f["resultado"]))
        c[2].metric("% de la meta", _pct(f["pct_avance_vigencia"]))
        c[3].metric("Proyección de cierre", _num(f["valor_proyectado"]) if pd.notna(f["valor_proyectado"]) else "sin dato")

        izq, der = st.columns(2)
        with izq:
            st.markdown("##### Plan de acción")
            if not f["tiene_plan_de_accion"]:
                st.markdown('<span class="vacio">Esta dependencia no tiene actividades para la meta.</span>',
                            unsafe_allow_html=True)
            else:
                st.write(_md(f"**Presupuesto definitivo:** {_pesos(f['ppto_definitivo'])}  \n"
                             f"**Obligaciones:** {_pesos(f['ppto_obligaciones'])} · {_pct(f['pct_ejecucion_financiera'])}"))
                st.write(f"**Avance de todas las actividades** *(el que prima para el análisis)*: "
                         f"{_pct(f['avance_actividades'])}  \n"
                         f"**Avance solo de las que tienen obligaciones** *(complementario)*: "
                         f"{_pct(f['avance_actividades_con_obligaciones'])}"
                         + (f" · {int(f['n_registros_con_obligaciones'])} de {int(f['n_registros'])} registros"
                            if pd.notna(f["avance_actividades_con_obligaciones"]) else ""))
                for linea in lineas_por_proyecto(f["avance_por_proyecto"]):
                    st.caption(f"Proyecto {linea}")
        with der:
            st.markdown("##### Alertas")
            if revision.empty:
                st.success("Sin alertas objetivas.")
            for _, a in revision.iterrows():
                (st.error if a["severidad"] == "error" else st.warning)(_md(f"**{etiqueta_regla(a['regla'])}.** {a['detalle']}"))
            if len(info):
                with st.expander(f"Notas informativas ({len(info)})"):
                    for _, a in info.iterrows():
                        st.markdown(_md(f"- **{etiqueta_regla(a['regla'])}.** {a['detalle']}"))

        with st.expander("Narrativa que reportó la dependencia"):
            for titulo, col in (("Principal logro", "principal_logro"), ("Análisis del logro", "analisis_logro"),
                                ("Dificultades o gestiones", "dificultades_gestiones")):
                st.markdown(f"**{titulo}.** " + (_md(f[col]) if pd.notna(f[col]) else "*(vacío)*"))
        if res.usa_z023:
            ap = res.aportes[res.aportes["codigo_mp"] == codigo_mp]
            with st.expander(f"Proyectos que aportan a esta meta según el Z023 ({ap['proyecto_ppm'].nunique()})"):
                if ap.empty:
                    st.caption("El Z023 no tiene actividades de ningún proyecto para esta meta en la vigencia.")
                else:
                    st.dataframe(ap.drop(columns=["codigo_mp", "vigencia"]).rename(columns=ETIQUETAS_APORTES),
                                 column_config={ETIQUETAS_APORTES["valor_actividades"]:
                                                st.column_config.NumberColumn(format="$ %,.0f")},
                                 hide_index=True, use_container_width=True)
                    st.caption("Las entidades descentralizadas solo llegan a PPM: no tienen código PS ni actividades "
                               "en EVAPLAN.")


# ------------------------------------------------------------------ detalle técnico (cerrado por defecto)
def detalle_tecnico(res) -> None:
    n = len(res.calidad)
    with st.expander(f"🔧 Detalle técnico · {n} {'observación' if n == 1 else 'observaciones'} sobre los datos"):
        t1, t2, t3 = st.tabs(["Calidad de los datos", "Todos los hallazgos", "Matriz completa"])
        with t1:
            st.caption("Reglas de integridad y comparación entre fuentes. Útil para quien administra la herramienta.")
            if res.calidad.empty:
                st.success("Sin observaciones.")
            else:
                st.dataframe(etiquetar(res.calidad), hide_index=True, use_container_width=True)
        with t2:
            sev = st.multiselect("Severidad", ["error", "advertencia", "info"], default=["error", "advertencia", "info"])
            st.dataframe(etiquetar(res.hallazgos[res.hallazgos["severidad"].isin(sev)]).drop(columns=["fila_excel", "fuente"]),
                         hide_index=True, use_container_width=True)
        with t3:
            st.dataframe(res.matriz.rename(columns=ETIQUETAS), hide_index=True, use_container_width=True)
