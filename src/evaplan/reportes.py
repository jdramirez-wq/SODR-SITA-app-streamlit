"""Salidas descargables: Excel integrado y PDF por meta (el PDF alimenta al asistente de IA).

Pensadas para que una IA SENCILLA (incluida una versión gratuita que solo lee PDF) no tenga que adivinar nada:
  - Un solo formato de cifras (formato.py): porcentajes siempre 0-100 con '%', pesos con '$', 'sin dato' ≠ 0.
  - Cada dato con su nombre completo y su unidad en la misma línea ('Ejecución financiera: 22,3 %').
  - Una guía de lectura al inicio y un bloque por meta con secciones numeradas y marcas de inicio y fin.
  - Solo texto plano (sin emojis ni símbolos que el PDF no pueda mostrar).
"""
from __future__ import annotations

import io
from datetime import date
from html import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import formato as F
from .aportes import ETIQUETAS_APORTES
from .condiciones import condiciones_prompt, texto_condicion
from .reglas import etiqueta_regla, etiquetar
from .seguimiento import COLUMNAS_MATRIZ, COLUMNAS_PORCENTAJE, COLUMNAS_Z023, ETIQUETAS

# ------------------------------------------------------------------ Excel


def matriz_legible(matriz: pd.DataFrame) -> pd.DataFrame:
    """Matriz con nombres legibles y los porcentajes en escala 0-100 (una IA o persona no ve fracciones)."""
    extra = [c for c in COLUMNAS_Z023 if c in matriz.columns]
    m = matriz[COLUMNAS_MATRIZ + extra].copy()
    for c in COLUMNAS_PORCENTAJE:
        m[c] = (m[c].astype("Float64") * 100).round(1)
    return m.rename(columns=ETIQUETAS)


def _hoja_leeme(entidad: str, vigencia) -> pd.DataFrame:
    filas = [("Reporte", "Seguimiento EVAPLAN al Plan de Desarrollo Departamental"),
             ("Entidad", entidad or "sin dato"), ("Vigencia analizada", str(vigencia or "sin dato")),
             ("Generado", date.today().isoformat())]
    filas += [("Convención", c) for c in F.CONVENCIONES]
    filas += [("Avance de actividades", "Hay dos promedios. El que PRIMA para el análisis es el de TODAS las "
               "actividades; el de las actividades con obligaciones es complementario."),
              ("Alertas", "Son hechos detectados por la herramienta, no un dictamen. '[Revisar]' requiere revisión; "
               "'[Informativa]' es contexto."),
              ("Hojas", "MP_PI_PA: una fila por meta. Hallazgos: alertas por meta. Sin_reporte: metas que no "
               "aparecen en EVAPLAN. Calidad_de_datos: revisión técnica de los archivos. Aportes_Z023: proyectos "
               "que aportan a cada meta (si se cargó el Z023).")]
    return pd.DataFrame(filas, columns=["Tema", "Detalle"])


def a_excel(matriz: pd.DataFrame, hallazgos: pd.DataFrame, calidad: pd.DataFrame | None = None,
            aportes: pd.DataFrame | None = None, entidad: str = "", vigencia=None) -> bytes:
    """Libro con: guía de lectura, matriz por meta, hallazgos, metas sin reporte, calidad de datos y (si se
    cargó el Z023) los proyectos que aportan a cada meta."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        _hoja_leeme(entidad, vigencia if vigencia is not None else
                    (int(matriz["vigencia"].iloc[0]) if len(matriz) else "")).to_excel(w, index=False, sheet_name="Leeme")
        matriz_legible(matriz).to_excel(w, index=False, sheet_name="MP_PI_PA")
        etiquetar(hallazgos).to_excel(w, index=False, sheet_name="Hallazgos")
        matriz.loc[matriz["estado_reporte"] != "Reportada",
                   ["codigo_entidad", "codigo_mp", "descripcion_mp", "comportamiento", "meta_vigencia"]
                   ].rename(columns=ETIQUETAS).to_excel(w, index=False, sheet_name="Sin_reporte")
        if calidad is not None:
            etiquetar(calidad).to_excel(w, index=False, sheet_name="Calidad_de_datos")
        if aportes is not None:
            aportes.rename(columns=ETIQUETAS_APORTES).to_excel(w, index=False, sheet_name="Aportes_Z023")
        for ws in w.book.worksheets:           # anchos legibles, encabezado fijo y formato de miles
            ws.freeze_panes = "A2"
            for col in ws.columns:
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in list(col)[:50])
                ws.column_dimensions[col[0].column_letter].width = min(max(ancho + 2, 10), 70)
                encabezado = str(col[0].value or "")
                formato = ("0.0" if "(%)" in encabezado or "(puntos %)" in encabezado
                           else "#,##0" if any(k in encabezado for k in ("Ppto", "Obligaciones", "Disponible", "Valor de"))
                           else None)
                if formato:
                    for c in list(col)[1:]:
                        c.number_format = formato
    return buf.getvalue()


# ------------------------------------------------------------------ PDF
_EST = {
    "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=15, leading=19, spaceAfter=6,
                             textColor=colors.HexColor("#0B4F4A")),
    "meta": ParagraphStyle("meta", fontName="Helvetica-Bold", fontSize=12.5, leading=16, spaceAfter=2,
                           textColor=colors.HexColor("#0B4F4A")),
    "seccion": ParagraphStyle("seccion", fontName="Helvetica-Bold", fontSize=10.5, leading=14, spaceBefore=8,
                              spaceAfter=2, textColor=colors.HexColor("#14302C")),
    "texto": ParagraphStyle("texto", fontName="Helvetica", fontSize=9.5, leading=13),
    "linea": ParagraphStyle("linea", fontName="Helvetica", fontSize=9.5, leading=13, leftIndent=10),
    "nota": ParagraphStyle("nota", fontName="Helvetica-Oblique", fontSize=8.5, leading=11,
                           textColor=colors.HexColor("#5B7470")),
    "caja": ParagraphStyle("caja", fontName="Helvetica", fontSize=9.5, leading=13, leftIndent=6),
}


def _limpio(texto) -> str:
    """Texto plano que el PDF puede mostrar (sin emojis) y seguro para Paragraph."""
    if F.es_na(texto):
        return F.SIN_DATO
    t = " ".join(str(texto).split()).replace("≠", "distinto de").replace("→", "->")
    t = t.encode("cp1252", errors="ignore").decode("cp1252")
    return escape(t)


def _dato(nombre: str, valor) -> Paragraph:
    return Paragraph(f"- <b>{escape(nombre)}:</b> {_limpio(valor) if not isinstance(valor, Paragraph) else valor}",
                     _EST["linea"])


def _caja(lineas: list[str], fondo="#E6F2F0") -> Table:
    t = Table([[Paragraph(linea, _EST["caja"])] for linea in lineas], colWidths=[17 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fondo)),
                           ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5E3")),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def _guia(matriz: pd.DataFrame, entidad: str) -> list:
    vig = int(matriz["vigencia"].iloc[0]) if len(matriz) else ""
    sin = matriz[matriz["estado_reporte"] != "Reportada"]
    rep = matriz[matriz["estado_reporte"] == "Reportada"]
    out = [Paragraph("REPORTE DE SEGUIMIENTO EVAPLAN", _EST["titulo"]),
           Paragraph(f"<b>Entidad:</b> {_limpio(entidad or 'sin dato')}<br/><b>Vigencia analizada:</b> {vig}"
                     f"<br/><b>Generado:</b> {date.today().isoformat()}", _EST["texto"]),
           Spacer(1, 8), Paragraph("CÓMO LEER ESTE DOCUMENTO", _EST["seccion"]),
           _caja([f"{i}. {escape(c)}" for i, c in enumerate(F.CONVENCIONES, start=1)] + [
               f"{len(F.CONVENCIONES) + 1}. Avance de actividades: hay DOS promedios. Para el análisis se usa el de "
               "<b>TODAS las actividades</b>; el de las actividades con obligaciones es solo complementario.",
               f"{len(F.CONVENCIONES) + 2}. Las alertas son hechos detectados por la herramienta, no un dictamen. "
               "[Revisar] = requiere revisión; [Informativa] = contexto.",
               f"{len(F.CONVENCIONES) + 3}. En cada meta, la sección 3 dice si se cumplen las condiciones objetivas de "
               "las Alertas Tipo 1, 2 y 3 del prompt. Úsala en lugar de deducirlas.",
               f"{len(F.CONVENCIONES) + 4}. Cada meta empieza con 'INICIO DE LA META' y termina con 'FIN DE LA META'."]),
           Spacer(1, 8), Paragraph("RESUMEN", _EST["seccion"]),
           _dato("Metas del Plan Indicativo", str(len(matriz))),
           _dato("Metas reportadas en EVAPLAN", str(len(rep))),
           _dato("Metas sin reporte en EVAPLAN (no se evalúan; se informan como omisión de reporte)", str(len(sin)))]
    for _, f in sin.iterrows():
        out.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{_limpio(f['codigo_mp'])}: {_limpio(f['descripcion_mp'])}",
                             _EST["linea"]))
    if len(rep):
        out += [Spacer(1, 8), Paragraph("ÍNDICE DE METAS REPORTADAS", _EST["seccion"])]
        for i, (_, f) in enumerate(rep.iterrows(), start=1):
            out.append(Paragraph(
                f"{i}. <b>{_limpio(f['codigo_mp'])}</b>: avance frente a la meta {_avance_meta(f)}; ejecución "
                f"financiera {F.porcentaje(f['pct_ejecucion_financiera'])}; avance de todas las actividades "
                f"{F.porcentaje(f['avance_actividades'])}; alertas que requieren revisión: {int(f['n_alertas'])}.",
                _EST["linea"]))
    return out


def _narrativa(texto) -> str:
    return "vacío (la dependencia no lo diligenció)" if F.es_na(texto) else texto


def _avance_meta(f) -> str:
    if f["meta_vigencia_np"]:
        return "no aplica (vigencia no programada)"
    if not F.es_na(f["meta_vigencia"]) and float(f["meta_vigencia"]) == 0:
        return "no aplica (la meta de la vigencia es 0)"
    return F.porcentaje(f["pct_avance_vigencia"])


def _bloque_meta(f, n: int, total: int, alertas: pd.DataFrame | None) -> list:
    cod = f["codigo_mp"]
    vig = f["vigencia"]
    out = [Paragraph(f"INICIO DE LA META {n} DE {total}: {_limpio(cod)}", _EST["meta"]),
           Paragraph(_limpio(f["descripcion_mp"]), _EST["texto"]),
           _dato("Comportamiento del indicador", f["comportamiento"]),
           _dato("Unidad de medida", f["unidad_medida"])]

    meta_txt = "no programada (NP)" if f["meta_vigencia_np"] else F.numero(f["meta_vigencia"])
    avance_meta = _avance_meta(f)
    out += [Paragraph(f"1. PLAN INDICATIVO (lo que la meta debía lograr en {vig})", _EST["seccion"]),
            _dato(f"Meta programada para {vig}", meta_txt),
            _dato(f"Resultado reportado por la dependencia (acumulado {vig})", F.numero(f["resultado"])),
            _dato(f"Avance frente a la meta de {vig}", avance_meta),
            _dato("Proyección de cierre según la dependencia", F.numero(f["valor_proyectado"])
                  + ("" if F.es_na(f["pct_proyectado_vs_meta"]) else f" ({F.porcentaje(f['pct_proyectado_vs_meta'])} de la meta)"))]
    if not F.es_na(f["logro_previo"]):
        out += [_dato("Logro acumulado de vigencias anteriores", F.numero(f["logro_previo"])),
                _dato("Meta del cuatrienio (PG)", F.numero(f["pg"])),
                _dato("Avance frente a la meta del cuatrienio", F.porcentaje(f["pct_avance_pg"]))]
    elif f["comportamiento"] == "Incremento Capacidad":     # se mide con el nivel alcanzado (último resultado)
        out += [_dato("Meta del cuatrienio (PG, nivel a alcanzar en 2027)", F.numero(f["pg"])),
                _dato("Avance frente a la meta del cuatrienio (nivel alcanzado / PG)", F.porcentaje(f["pct_avance_pg"]))]

    out.append(Paragraph("2. PLAN DE ACCIÓN (actividades de los proyectos de inversión)", _EST["seccion"]))
    if not f["tiene_plan_de_accion"]:
        out.append(_dato("Plan de acción", "la dependencia no tiene actividades para esta meta"))
    else:
        con_obl = (F.porcentaje(f["avance_actividades_con_obligaciones"])
                   + f" ({int(f['n_registros_con_obligaciones'])} de {int(f['n_registros'])} actividades tienen obligaciones)"
                   if not F.es_na(f["avance_actividades_con_obligaciones"])
                   else "sin dato (ninguna actividad tiene obligaciones)")
        proyectos = "; ".join(str(f["avance_por_proyecto"]).split(" | ")) if not F.es_na(f["avance_por_proyecto"]) else F.SIN_DATO
        out += [_dato("Proyectos", str(f["proyectos"]).replace(" | ", "; ")),
                _dato("Presupuesto definitivo", F.pesos(f["ppto_definitivo"])),
                _dato("Obligaciones (ejecución financiera en pesos)", F.pesos(f["ppto_obligaciones"])),
                _dato("Ejecución financiera (obligaciones / presupuesto definitivo)", F.porcentaje(f["pct_ejecucion_financiera"])),
                _dato("Avance físico promedio de TODAS las actividades (USAR ESTE PARA EL ANÁLISIS)", F.porcentaje(f["avance_actividades"])),
                _dato("Avance físico promedio solo de las actividades con obligaciones (complementario)", con_obl),
                _dato("Avance físico promedio por proyecto de inversión", proyectos)]
        if f["n_registros_con_obligaciones_sin_avance"]:
            out.append(_dato("Actividades con obligaciones y sin avance físico",
                             f"{int(f['n_registros_con_obligaciones_sin_avance'])} (de ellas, "
                             f"{int(f['n_registros_sin_avance_sin_observacion'])} sin observación que lo explique)"))
    if "aportes_otras_entidades" in f.index and not F.es_na(f["aportes_otras_entidades"]):
        out.append(_dato("Proyectos de OTRAS entidades que también aportan a la meta (Z023)", f["aportes_otras_entidades"]))

    out.append(Paragraph("3. CONDICIONES DE LAS ALERTAS TIPO 1, 2 Y 3 DEL PROMPT (comprobadas con las cifras)",
                         _EST["seccion"]))
    for c in condiciones_prompt(f):
        out.append(Paragraph("- " + _limpio(texto_condicion(c)), _EST["linea"]))
    out.append(Paragraph("Que una condición se cumpla no es un dictamen: falta revisar si la narrativa lo explica.",
                         _EST["nota"]))

    out.append(Paragraph("4. OTRAS ALERTAS DE LA HERRAMIENTA (hechos, no dictamen)", _EST["seccion"]))
    if alertas is None or alertas.empty:
        out.append(_dato("Alertas", "ninguna"))
    else:
        orden = alertas.assign(_o=alertas["severidad"].map({"error": 0, "advertencia": 1, "info": 2})).sort_values("_o")
        for _, a in orden.iterrows():
            tipo = "[Informativa]" if a["severidad"] == "info" else "[Revisar]"
            out.append(Paragraph(f"- <b>{tipo} {escape(etiqueta_regla(a['regla']))}:</b> {_limpio(a['detalle'])}",
                                 _EST["linea"]))

    out += [Paragraph("5. NARRATIVA REPORTADA POR LA DEPENDENCIA", _EST["seccion"]),
            _dato("Principal logro", _narrativa(f["principal_logro"])),
            _dato("Análisis del logro", _narrativa(f["analisis_logro"])),
            _dato("Dificultades o gestiones", _narrativa(f["dificultades_gestiones"])),
            _dato("Focalización", f["focalizacion"]),
            Spacer(1, 6), Paragraph(f"FIN DE LA META {_limpio(cod)}", _EST["nota"])]
    return out


def a_pdf(matriz: pd.DataFrame, hallazgos: pd.DataFrame | None = None, entidad: str = "") -> bytes:
    """Guía de lectura + resumen + índice, y luego un bloque por meta REPORTADA (cada una en página nueva)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title="Reporte de seguimiento EVAPLAN", author="SODR")
    historia = _guia(matriz, entidad)
    rep = matriz[matriz["estado_reporte"] == "Reportada"]
    for i, (_, f) in enumerate(rep.iterrows(), start=1):
        alertas = hallazgos[hallazgos["llave"] == f["codigo_mp"]] if hallazgos is not None else None
        historia += [PageBreak(), *_bloque_meta(f, i, len(rep), alertas)]
    doc.build(historia)
    return buf.getvalue()


__all__ = ["a_excel", "a_pdf", "matriz_legible"]
