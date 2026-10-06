"""Aportes a cada meta de producto según el Z023 consolidado (metas compartidas). Sin Streamlit.

El Z023 trae TODAS las actividades de TODOS los proyectos con su MP. Para cada meta del seguimiento se listan los
proyectos que le aportan y se separa lo que viene de la propia dependencia de lo que viene de otras entidades
(dependencias centrales o entidades descentralizadas). Son HECHOS: aquí no se juzga si el aporte es suficiente.

El Z023 es información no pública: estas funciones solo trabajan en memoria con el DataFrame que se les entrega.
"""
from __future__ import annotations

import pandas as pd

COLUMNAS_APORTES = [
    "codigo_mp", "vigencia", "codigo_dependencia", "nombre_dependencia", "tipo_entidad", "es_propia",
    "proyecto_ppm", "codigo_proyecto_ps", "nombre_proyecto", "bpin", "n_actividades", "n_sin_codigo_ps",
    "valor_actividades",
]

ETIQUETAS_APORTES = {
    "codigo_mp": "Código MP", "vigencia": "Vigencia", "codigo_dependencia": "Cód. dependencia",
    "nombre_dependencia": "Dependencia / entidad", "tipo_entidad": "Tipo de entidad", "es_propia": "De la propia dependencia",
    "proyecto_ppm": "Proyecto (PPM)", "codigo_proyecto_ps": "Proyecto (PS)", "nombre_proyecto": "Nombre del proyecto",
    "bpin": "BPIN", "n_actividades": "N.º actividades", "n_sin_codigo_ps": "…sin código PS",
    "valor_actividades": "Valor de las actividades (vigencia)",
}

# Observado en el Z023: las entidades descentralizadas tienen códigos '00xx' y solo llegan a PPM (sin código PS).
PREFIJO_DESCENTRALIZADA = "00"


def tipo_entidad(codigo) -> str:
    return "Descentralizada" if isinstance(codigo, str) and codigo.startswith(PREFIJO_DESCENTRALIZADA) else "Dependencia"


def construir_aportes(z023: pd.DataFrame, matriz: pd.DataFrame, vigencia: int) -> pd.DataFrame:
    """Una fila por meta × dependencia × proyecto, solo para las metas de `matriz` y la `vigencia` dada."""
    z = z023[(z023["vigencia"] == vigencia) & z023["codigo_mp"].isin(set(matriz["codigo_mp"]))]
    if z.empty:
        return pd.DataFrame(columns=COLUMNAS_APORTES)
    dueña = matriz.drop_duplicates("codigo_mp").set_index("codigo_mp")["codigo_entidad"].astype("string")
    g = (z.assign(_sin_ps=z["ps_actividad"].isna())
         .groupby(["codigo_mp", "dependencia", "proyecto_ppm"], dropna=False, sort=True)
         .agg(nombre_dependencia=("nombre_dependencia", "first"), codigo_proyecto_ps=("codigo_proyecto_ps", "first"),
              nombre_proyecto=("nombre_proyecto", "first"), bpin=("bpin", "first"),
              n_actividades=("ppm_actividad", "nunique"), n_sin_codigo_ps=("_sin_ps", "sum"),
              valor_actividades=("valor_actividad", lambda s: s.sum(min_count=1)))
         .reset_index().rename(columns={"dependencia": "codigo_dependencia"}))
    g["vigencia"] = vigencia
    g["tipo_entidad"] = g["codigo_dependencia"].map(tipo_entidad)
    g["es_propia"] = g["codigo_dependencia"].astype("string") == g["codigo_mp"].map(dueña)
    g["n_sin_codigo_ps"] = g["n_sin_codigo_ps"].astype(int)
    return g[COLUMNAS_APORTES].sort_values(["codigo_mp", "es_propia", "codigo_dependencia", "proyecto_ppm"],
                                           ascending=[True, False, True, True]).reset_index(drop=True)


def resumen_por_meta(aportes: pd.DataFrame, codigos_mp: pd.Series) -> pd.DataFrame:
    """Por meta: n.º de proyectos y de entidades aportantes, valor y texto de los aportes ajenos."""
    filas = []
    for mp in codigos_mp:
        a = aportes[aportes["codigo_mp"] == mp]
        ajenos = a[~a["es_propia"]]
        texto = " | ".join(
            f"{r.codigo_dependencia} {r.nombre_dependencia} · {r.proyecto_ppm} ({r.n_actividades} act.)"
            for r in ajenos.itertuples()) if len(ajenos) else pd.NA
        filas.append({
            "codigo_mp": mp,
            "n_proyectos_z023": int(a["proyecto_ppm"].nunique()),
            "n_entidades_aportantes": int(a["codigo_dependencia"].nunique()),
            "n_proyectos_ajenos": int(ajenos["proyecto_ppm"].nunique()),
            "valor_z023": a["valor_actividades"].sum(min_count=1) if len(a) else pd.NA,
            "aportes_otras_entidades": texto,
        })
    return pd.DataFrame(filas).set_index("codigo_mp")
