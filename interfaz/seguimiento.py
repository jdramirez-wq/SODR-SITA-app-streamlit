"""Vistas de la página de Seguimiento EVAPLAN. Solo dibuja: qué mostrar lo decide src/evaplan (vista.py).

Las cifras usan el mismo formato que el PDF y el Excel (src/evaplan/formato.py).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.evaplan import formato as F
from src.evaplan import reportes
from src.evaplan.aportes import ETIQUETAS_APORTES
from src.evaplan.condiciones import condiciones_prompt
from src.evaplan.prompts import generar_prompt_sistema
from src.evaplan.reglas import etiqueta_regla, etiquetar
from src.evaplan.vista import FILTROS, alertas_de, contar_filtros, filtrar_metas, lineas_por_proyecto, tabla_metas

from . import estilos


def _md(texto) -> str:
    """Escapa el signo $ para que Markdown no lo tome por una fórmula matemática."""
    return str(texto).replace("$", "\\$")


# ------------------------------------------------------------------ encabezado, cifras y acciones
def encabezado_resultados(res, periodo) -> None:
    estilos.barra_titulo("Seguimiento", "EVAPLAN", [
        (res.entidad, ""), (f"Vigencia {res.vigencia}", "gris"), (periodo.etiqueta, "gris")])


def cifras(res) -> None:
    R = res.resumen
    estilos.tarjetas([
        ("Metas del Plan Indicativo", str(R["metas_en_plan_indicativo"]),
         f"{R['metas_reportadas']} reportadas en EVAPLAN", False),
        ("Sin reporte", str(R["metas_sin_reporte"]), "No aparecen en el export de EVAPLAN", R["metas_sin_reporte"] > 0),
        ("Requieren revisión", str(R["metas_con_alertas"]), "Metas con al menos una advertencia",
         R["metas_con_alertas"] > 0),
        ("Ejecución financiera", F.porcentaje(R["ppto_obligaciones"] / R["ppto_definitivo"]) if R["ppto_definitivo"]
         else F.SIN_DATO, f"{F.pesos(R['ppto_obligaciones'])} de {F.pesos(R['ppto_definitivo'])}", False),
    ])


@st.cache_data(show_spinner=False, max_entries=3)
def _entregables(matriz: pd.DataFrame, hallazgos: pd.DataFrame, calidad: pd.DataFrame,
                 aportes: pd.DataFrame | None, entidad: str) -> tuple[bytes, bytes]:
    """Excel y PDF: se generan una sola vez por resultado (no en cada clic de la pantalla)."""
    return (reportes.a_excel(matriz, hallazgos, calidad, aportes, entidad),
            reportes.a_pdf(matriz, hallazgos, entidad))


@st.dialog("Prompt para el asistente de IA", width="large")
def _dialogo_prompt(texto: str) -> None:
    estilos.pasos([("Copia el prompt", "Con el icono de copiar, en la esquina del recuadro."),
                   ("Pégalo en la IA", "Gemini o ChatGPT. Sirve también la versión gratuita."),
                   ("Adjunta el PDF", "El PDF basta: trae todas las cifras y su guía de lectura.")])
    st.code(texto, language="markdown", wrap_lines=True, height=360)
    a, b = st.columns(2)
    a.link_button("Abrir Google Gemini", "https://gemini.google.com/", width="stretch", type="primary")
    b.link_button("Abrir ChatGPT", "https://chatgpt.com/", width="stretch")


def barra_acciones(res, periodo, con_hechos: bool, recordatorios: list[dict]) -> None:
    excel, pdf = _entregables(res.matriz, res.hallazgos, res.calidad, res.aportes if res.usa_z023 else None,
                              res.entidad)
    c0, c1, c2, c3 = st.columns([2.6, 1.1, 1.1, 1.4], vertical_alignment="center")
    c0.markdown('<div class="nota">Descarga los entregables o prepara el análisis con IA.</div>',
                unsafe_allow_html=True)
    c1.download_button("Excel", excel, file_name="MP_PI_PA_Integrado.xlsx", width="stretch",
                       icon=":material/table_view:",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       help="Matriz por meta, hallazgos, metas sin reporte y calidad de datos")
    c2.download_button("PDF", pdf, file_name="MP_PI_PA_Reporte.pdf", mime="application/pdf", width="stretch",
                       icon=":material/picture_as_pdf:", help="Una sección por meta, lista para adjuntar a la IA")
    if c3.button("Prompt para IA", width="stretch", type="primary", icon=":material/smart_toy:",
                 help="Instrucciones para el asistente de auditoría (Gemini / ChatGPT)"):
        _dialogo_prompt(generar_prompt_sistema(periodo, res.vigencia, con_hechos, recordatorios))


def recordatorios_cierre(recordatorios: list[dict]) -> None:
    if not recordatorios:
        return
    n = len(recordatorios)
    with st.expander(f"Cierre de vigencia: {n} {'certificado' if n == 1 else 'certificados'} por solicitar",
                     expanded=True, icon=":material/assignment_late:"):
        for r in recordatorios:
            estilos.alerta(r["titulo"], r["texto"] + (f" Metas: {', '.join(r['metas'])}." if r["metas"] else ""))
        estilos.nota("Son pendientes de quien revisa, no hallazgos sobre lo que reportó la entidad. "
                     "También se agregan al prompt.")


# ------------------------------------------------------------------ lista de metas + ficha
def lista_y_ficha(res) -> None:
    m, h = res.matriz, res.hallazgos
    conteo = contar_filtros(m)
    st.markdown("### Metas")
    etiquetas = {f"{f} · {conteo[f]}": f for f in FILTROS if f in conteo}
    elegido = st.segmented_control("Mostrar", list(etiquetas), default=list(etiquetas)[0],
                                   label_visibility="collapsed", key="filtro_metas")
    filtro = etiquetas.get(elegido, "Todas")
    c2, c3 = st.columns([1.4, 1], vertical_alignment="center")
    texto = c2.text_input("Buscar", placeholder="Buscar código o descripción", label_visibility="collapsed",
                          icon=":material/search:")
    reglas = sorted({etiqueta_regla(r): r for r in h["regla"]}.items())
    tipo = c3.selectbox("Tipo de hallazgo", ["Cualquier hallazgo", *[n for n, _ in reglas]],
                        label_visibility="collapsed")
    regla = dict(reglas).get(tipo)

    v = filtrar_metas(m, h, filtro, texto, regla)
    if v.empty:
        estilos.alerta("Sin resultados", "Ninguna meta coincide con el filtro.", "info")
        return
    t = tabla_metas(v)
    config = {"Alertas": st.column_config.NumberColumn("Alertas", format="%d", width=70),
              "Meta": st.column_config.TextColumn("Meta", width=175),
              "Código": st.column_config.TextColumn("Código", width=150),
              "Reportó": st.column_config.TextColumn("Reportó", width=75),
              "Otras entidades": st.column_config.NumberColumn("Otras entidades", format="%d", width=95)}
    for c in ("% de la meta", "Ejecución fin.", "Avance act."):
        config[c] = st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f %%", width=100)
    evento = st.dataframe(t, hide_index=True, width="stretch", column_config=config,
                          height=min(42 + 35 * len(t), 390), on_select="rerun", selection_mode="single-row",
                          key=f"tabla_{filtro}_{tipo}_{texto}")
    filas = evento.selection.rows
    estilos.nota(f"{len(t)} {'meta' if len(t) == 1 else 'metas'}, primero las que tienen más alertas. "
                 + ("" if filas else "Haz clic en una fila para ver su ficha; por ahora se muestra la primera."))
    ficha(res, v.iloc[filas[0] if filas else 0]["codigo_mp"])


def _texto(x, alterno: str = "") -> str:
    return alterno if F.es_na(x) else str(x)


def ficha(res, codigo_mp: str) -> None:
    f = res.matriz.set_index("codigo_mp").loc[codigo_mp]
    revision, info = alertas_de(res.hallazgos, codigo_mp)
    with st.container(border=True):
        st.markdown(f'<span class="ficha-codigo">{codigo_mp}</span>', unsafe_allow_html=True)
        st.markdown(f'<p class="ficha-titulo">{_texto(f["descripcion_mp"])}</p>', unsafe_allow_html=True)
        estilos.chips([_texto(f["comportamiento"]), _texto(f["unidad_medida"]), f["estado_reporte"]])

        c = st.columns(4)
        c[0].metric("Meta de la vigencia", "No programada" if f["meta_vigencia_np"] else F.numero(f["meta_vigencia"]))
        c[1].metric("Resultado acumulado", F.numero(f["resultado"]))
        c[2].metric("Avance frente a la meta", F.porcentaje(f["pct_avance_vigencia"]))
        c[3].metric("Proyección de cierre", F.numero(f["valor_proyectado"]))

        izq, der = st.columns([1.05, 1], gap="large")
        with izq:
            st.markdown("##### Plan de acción")
            if not f["tiene_plan_de_accion"]:
                st.markdown('<span class="vacio">La dependencia no tiene actividades para esta meta.</span>',
                            unsafe_allow_html=True)
            else:
                con_obl = F.porcentaje(f["avance_actividades_con_obligaciones"])
                if not F.es_na(f["avance_actividades_con_obligaciones"]):
                    con_obl += f" ({int(f['n_registros_con_obligaciones'])} de {int(f['n_registros'])})"
                estilos.datos([
                    ("Presupuesto definitivo", F.pesos(f["ppto_definitivo"]), False),
                    ("Obligaciones", F.pesos(f["ppto_obligaciones"]), False),
                    ("Ejecución financiera", F.porcentaje(f["pct_ejecucion_financiera"]), True),
                    ("Avance de todas las actividades (prima)", F.porcentaje(f["avance_actividades"]), True),
                    ("Avance de las que tienen obligaciones", con_obl, False),
                ])
                proyectos = lineas_por_proyecto(f["avance_por_proyecto"])
                if proyectos:
                    estilos.nota("Por proyecto: " + " · ".join(proyectos))
        with der:
            st.markdown("##### Alertas")
            if revision.empty:
                estilos.alerta("Sin alertas que revisar", "La herramienta no encontró incoherencias objetivas.", "ok")
            for _, a in revision.iterrows():
                estilos.alerta(etiqueta_regla(a["regla"]), a["detalle"], "error" if a["severidad"] == "error" else "")
            if len(info):
                with st.expander(f"Notas informativas ({len(info)})"):
                    for _, a in info.iterrows():
                        estilos.alerta(etiqueta_regla(a["regla"]), a["detalle"], "info")

        with st.expander("Condiciones de las Alertas Tipo 1, 2 y 3 del prompt", icon=":material/rule:"):
            for cnd in condiciones_prompt(f):
                tono = {True: "", False: "ok", None: "info"}[cnd["se_cumple"]]
                estado = {True: "se cumple", False: "no se cumple", None: "no se puede comprobar"}[cnd["se_cumple"]]
                estilos.alerta(f"Tipo {cnd['tipo']} · {cnd['nombre']}: {estado}", cnd["hechos"], tono)
        with st.expander("Narrativa que reportó la dependencia", icon=":material/notes:"):
            for titulo, col in (("Principal logro", "principal_logro"), ("Análisis del logro", "analisis_logro"),
                                ("Dificultades o gestiones", "dificultades_gestiones")):
                st.markdown(f"**{titulo}.** " + (_md(f[col]) if not F.es_na(f[col]) else "*(vacío)*"))
        if res.usa_z023:
            ap = res.aportes[res.aportes["codigo_mp"] == codigo_mp]
            with st.expander(f"Proyectos que aportan a esta meta según el Z023 ({ap['proyecto_ppm'].nunique()})",
                             icon=":material/hub:"):
                if ap.empty:
                    estilos.nota("El Z023 no tiene actividades de ningún proyecto para esta meta en la vigencia.")
                else:
                    st.dataframe(ap.drop(columns=["codigo_mp", "vigencia"]).rename(columns=ETIQUETAS_APORTES),
                                 column_config={ETIQUETAS_APORTES["valor_actividades"]:
                                                st.column_config.NumberColumn(format="$ %,.0f")},
                                 hide_index=True, width="stretch")
                    estilos.nota("Las entidades descentralizadas solo llegan a PPM: no tienen código PS ni "
                                 "actividades en EVAPLAN.")


# ------------------------------------------------------------------ detalle técnico (cerrado por defecto)
def detalle_tecnico(res) -> None:
    n = len(res.calidad)
    with st.expander(f"Detalle técnico · {n} {'observación' if n == 1 else 'observaciones'} sobre los datos",
                     icon=":material/build:"):
        t1, t2, t3 = st.tabs(["Calidad de los datos", "Todos los hallazgos", "Matriz completa"])
        with t1:
            estilos.nota("Reglas de integridad y comparación entre fuentes. Útil para quien administra la herramienta.")
            if res.calidad.empty:
                estilos.alerta("Sin observaciones", "Los archivos pasaron todas las reglas.", "ok")
            else:
                st.dataframe(etiquetar(res.calidad), hide_index=True, width="stretch")
        with t2:
            sev = st.multiselect("Severidad", ["error", "advertencia", "info"], default=["error", "advertencia", "info"])
            st.dataframe(etiquetar(res.hallazgos[res.hallazgos["severidad"].isin(sev)]).drop(columns=["fila_excel", "fuente"]),
                         hide_index=True, width="stretch")
        with t3:
            estilos.nota("Los porcentajes están en escala 0 a 100, igual que en el Excel.")
            st.dataframe(reportes.matriz_legible(res.matriz), hide_index=True, width="stretch")
