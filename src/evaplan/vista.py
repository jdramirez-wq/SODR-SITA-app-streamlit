"""Preparación de lo que se muestra en pantalla (sin Streamlit, para poder probarlo).

La página decide CÓMO se dibuja; aquí se decide QUÉ filas, en qué orden y con qué texto.
Principio: lo que requiere atención va primero y lo informativo queda a un clic.
"""
from __future__ import annotations

import pandas as pd

FILTROS = ("Todas", "Con alertas", "Sin reporte", "Compartidas")


def contar_filtros(m: pd.DataFrame) -> dict[str, int]:
    """Cuántas metas tiene cada filtro (las "Compartidas" solo existen si se cargó el Z023)."""
    n = {"Todas": len(m), "Con alertas": int((m["n_alertas"] > 0).sum()),
         "Sin reporte": int((m["estado_reporte"] != "Reportada").sum())}
    if "n_proyectos_ajenos" in m.columns:
        n["Compartidas"] = int((m["n_proyectos_ajenos"] > 0).sum())
    return n


def filtrar_metas(m: pd.DataFrame, hallazgos: pd.DataFrame, filtro: str = "Todas", texto: str = "",
                  regla: str | None = None) -> pd.DataFrame:
    """Metas a mostrar. Orden: primero las que más alertas tienen, luego por código."""
    v = m
    if filtro == "Con alertas":
        v = v[v["n_alertas"] > 0]
    elif filtro == "Sin reporte":
        v = v[v["estado_reporte"] != "Reportada"]
    elif filtro == "Compartidas" and "n_proyectos_ajenos" in v.columns:
        v = v[v["n_proyectos_ajenos"] > 0]
    if regla:
        v = v[v["codigo_mp"].isin(set(hallazgos.loc[hallazgos["regla"] == regla, "llave"]))]
    if texto:
        t = texto.strip()
        v = v[v["codigo_mp"].str.contains(t, case=False, na=False)
              | v["descripcion_mp"].astype("string").str.contains(t, case=False, na=False)]
    return v.sort_values(["n_alertas", "codigo_mp"], ascending=[False, True], kind="stable")


def alertas_de(hallazgos: pd.DataFrame, codigo_mp: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(requieren revisión, informativas) de una meta."""
    h = hallazgos[hallazgos["llave"] == codigo_mp]
    return h[h["severidad"] != "info"], h[h["severidad"] == "info"]


def recortar(texto, n: int = 90) -> str:
    """Texto en una línea y con un máximo de caracteres."""
    if texto is None or texto is pd.NA or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    t = " ".join(str(texto).split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def lineas_por_proyecto(avance_por_proyecto) -> list[str]:
    """'P1: 50.0 % | P2: 0.0 %' -> ['P1: 50.0 %', 'P2: 0.0 %']."""
    if avance_por_proyecto is None or avance_por_proyecto is pd.NA or pd.isna(avance_por_proyecto):
        return []
    return [p.strip() for p in str(avance_por_proyecto).split(" | ") if p.strip()]


def tabla_metas(v: pd.DataFrame) -> pd.DataFrame:
    """Columnas compactas para la lista de metas (los porcentajes van de 0 a 100)."""
    def pct(c):
        return v[c].astype("Float64") * 100

    t = pd.DataFrame({
        "Código": v["codigo_mp"],
        "Meta": v["descripcion_mp"].map(lambda x: recortar(x, 80)),
        "Reportó": v["estado_reporte"].map(lambda e: "✅ Sí" if e == "Reportada" else "⛔ No"),
        "% de la meta": pct("pct_avance_vigencia"),
        "Ejecución fin.": pct("pct_ejecucion_financiera"),
        "Avance act.": pct("avance_actividades"),
        "Alertas": v["n_alertas"],
    })
    if "n_proyectos_ajenos" in v.columns:
        t["Otras entidades"] = v["n_proyectos_ajenos"]
    return t
