"""Salidas descargables: Excel integrado y PDF por meta (el PDF alimenta al LLM auditor)."""
from __future__ import annotations

import io
from textwrap import wrap

import pandas as pd
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from .seguimiento import COLUMNAS_MATRIZ, ETIQUETAS

_MARGEN_X, _MARGEN_Y = 50, 50


def _fmt(v, formato="{:,.2f}") -> str:
    if v is None or v is pd.NA or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return formato.format(v) if isinstance(v, (int, float)) else str(v)


def _pct(v) -> str:
    return _fmt(v * 100 if v is not None and v is not pd.NA and not pd.isna(v) else v, "{:.1f} %")


def a_excel(matriz: pd.DataFrame, hallazgos: pd.DataFrame, calidad: pd.DataFrame | None = None) -> bytes:
    """Libro con: matriz por meta, hallazgos de seguimiento, metas sin reporte y calidad de datos."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        matriz[COLUMNAS_MATRIZ].rename(columns=ETIQUETAS).to_excel(w, index=False, sheet_name="MP_PI_PA")
        hallazgos.to_excel(w, index=False, sheet_name="Hallazgos")
        matriz.loc[matriz["estado_reporte"] != "Reportada",
                   ["codigo_entidad", "codigo_mp", "descripcion_mp", "comportamiento", "meta_vigencia"]
                   ].rename(columns=ETIQUETAS).to_excel(w, index=False, sheet_name="Sin_reporte")
        if calidad is not None:
            calidad.to_excel(w, index=False, sheet_name="Calidad_de_datos")
        for ws in w.book.worksheets:           # anchos legibles y encabezado fijo
            ws.freeze_panes = "A2"
            for col in ws.columns:
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in list(col)[:50])
                ws.column_dimensions[col[0].column_letter].width = min(max(ancho + 2, 10), 60)
    return buf.getvalue()


def _bloque(c, texto, y, width, height, tamano=10, negrilla=False):
    t = c.beginText(_MARGEN_X, y)
    fuente = "Helvetica-Bold" if negrilla else "Helvetica"
    t.setFont(fuente, tamano)
    for linea in wrap(str(texto), 95) or [""]:
        if t.getY() <= _MARGEN_Y:
            c.drawText(t)
            c.showPage()
            t = c.beginText(_MARGEN_X, height - _MARGEN_Y)
            t.setFont(fuente, tamano)
        t.textLine(linea)
    c.drawText(t)
    return t.getY() - 12


def a_pdf(matriz: pd.DataFrame) -> bytes:
    """Una página (o más) por meta REPORTADA, con las secciones de la página original + hechos verificados.

    Al inicio, una carátula con las metas sin reporte.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER

    sin = matriz[matriz["estado_reporte"] != "Reportada"]
    y = height - _MARGEN_Y
    y = _bloque(c, "RESUMEN DE LA REVISIÓN", y, width, height, 12, True)
    y = _bloque(c, f"Metas en el Plan Indicativo: {len(matriz)} | Reportadas: {len(matriz) - len(sin)} | "
                   f"Sin reporte en EVAPLAN: {len(sin)}", y, width, height)
    if len(sin):
        y = _bloque(c, "Metas SIN REPORTE (no se evalúan; reportar como omisión):", y, width, height, 10, True)
        for _, f in sin.iterrows():
            y = _bloque(c, f"- {f['codigo_mp']}: {f['descripcion_mp']}", y, width, height)
    c.showPage()

    for _, f in matriz[matriz["estado_reporte"] == "Reportada"].iterrows():
        y = height - _MARGEN_Y
        y = _bloque(c, "META PRODUCTO", y, width, height, 11, True)
        y = _bloque(c, f"Código de Meta: {f['codigo_mp']}", y, width, height)
        y = _bloque(c, f"Descripción de Meta: {f['descripcion_mp']}", y, width, height)
        y = _bloque(c, f"Comportamiento del Indicador: {f['comportamiento']}", y, width, height)
        y -= 8
        y = _bloque(c, f"PLAN INDICATIVO (PI) — vigencia {f['vigencia']}", y, width, height, 11, True)
        y = _bloque(c, f"Programación de la vigencia (meta): {_fmt(f['meta_vigencia'])}", y, width, height)
        y = _bloque(c, f"Resultado (último reporte acumulado): {_fmt(f['resultado'])}", y, width, height)
        y = _bloque(c, f"Valor Proyectado (cierre de vigencia, según la dependencia): {_fmt(f['valor_proyectado'])} "
                       f"({_pct(f['pct_proyectado_vs_meta'])} de la meta)", y, width, height)
        y = _bloque(c, f"% avance frente a la meta de la vigencia: {_pct(f['pct_avance_vigencia'])}", y, width, height)
        if not pd.isna(f["logro_previo"]):
            y = _bloque(c, f"Logro de vigencias cerradas: {_fmt(f['logro_previo'])} | PG: {_fmt(f['pg'])} | "
                           f"% avance frente al PG: {_pct(f['pct_avance_pg'])}", y, width, height)
        y -= 8
        y = _bloque(c, "PROYECTOS ASOCIADOS", y, width, height, 11, True)
        y = _bloque(c, f"Proyectos Asociados: {_fmt(f['proyectos'])}", y, width, height)
        y -= 8
        y = _bloque(c, "FOCALIZACIÓN", y, width, height, 11, True)
        y = _bloque(c, _fmt(f["focalizacion"]), y, width, height)
        y -= 8
        y = _bloque(c, "PLAN DE ACCIÓN (PA)", y, width, height, 11, True)
        y = _bloque(c, f"Suma Presupuesto Definitivo: {_fmt(f['ppto_definitivo'])}", y, width, height)
        y = _bloque(c, f"Suma Total Obligaciones: {_fmt(f['ppto_obligaciones'])}", y, width, height)
        y = _bloque(c, f"Relación Obligaciones / Definitivo: {_pct(f['pct_ejecucion_financiera'])}", y, width, height)
        y = _bloque(c, f"Promedio Avance Actividades (todas): {_fmt(f['avance_actividades'], '{:.3f}')}", y, width, height)
        y = _bloque(c, f"Avance de actividades por proyecto: {_fmt(f['avance_por_proyecto'])}", y, width, height)
        y -= 8
        y = _bloque(c, "ALERTAS OBJETIVAS DE LA HERRAMIENTA (no son dictamen)", y, width, height, 11, True)
        y = _bloque(c, f["alertas"] if str(f["alertas"]).strip() else "Sin alertas objetivas.", y, width, height)
        y -= 8
        y = _bloque(c, "ANÁLISIS CUALITATIVO", y, width, height, 11, True)
        y = _bloque(c, f"Principal Logro en Función del Cumplimiento: {_fmt(f['principal_logro'])}", y, width, height)
        y = _bloque(c, f"Análisis del Logro: {_fmt(f['analisis_logro'])}", y, width, height)
        y = _bloque(c, f"Dificultades o Gestiones: {_fmt(f['dificultades_gestiones'])}", y, width, height)
        c.showPage()
    c.save()
    return buf.getvalue()
