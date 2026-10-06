"""Motor de seguimiento: cruza Plan Indicativo (Drive + EVAPLAN) con el Plan de Acción (Centralizadas).

Principio: el código calcula HECHOS objetivos (sumas, razones, presencia de datos) y detecta incoherencias que no
necesitan umbral. El JUICIO (¿es suficiente? ¿se devuelve?) lo hace la persona o el LLM: no hay un cronograma
único de ejecución que permita fijar umbrales, así que aquí no se inventan semáforos.

Entradas: DataFrames de `lectura` (pi_mp_evaplan, centralizadas, drive_mp opcional).
Salida: una fila por meta de producto (matriz) y una tabla de hallazgos con el mismo formato que `validaciones`.
"""
from __future__ import annotations

import re

import pandas as pd

from . import aportes as A
from .esquemas import FOCALIZACION
from .validaciones import ANIOS, COLUMNAS_HALLAZGO, inferir_vigencia

COMPORTAMIENTOS_ACUMULATIVOS = ("Incremento Acumulado", "Incremento Capacidad")
_RE_GESTION = re.compile(r"gesti[oó]n|donaci[oó]n|cofinanci|sin\s+costo", re.IGNORECASE)

COLUMNAS_MATRIZ = [
    "codigo_entidad", "codigo_mp", "descripcion_mp", "mr_del_mp", "comportamiento", "unidad_medida", "periodicidad",
    "estado_reporte", "vigencia", "pg", "meta_vigencia", "meta_vigencia_export", "meta_vigencia_np", "logro_previo",
    "resultado", "valor_proyectado", "pct_proyectado_vs_meta", "pct_avance_vigencia", "avance_cuatrienio", "pct_avance_pg",
    "tiene_plan_de_accion", "n_proyectos", "proyectos", "n_registros",
    "ppto_definitivo", "ppto_obligaciones", "ppto_disponible", "pct_ejecucion_financiera",
    "avance_actividades", "avance_por_proyecto", "n_registros_con_obligaciones_sin_avance",
    "n_registros_sin_avance_sin_observacion", "brecha_meta_vs_actividades",
    "focalizacion", "principal_logro", "analisis_logro", "dificultades_gestiones", "menciona_gestion",
    "n_alertas", "alertas",
]

COLUMNAS_Z023 = ["n_proyectos_z023", "n_entidades_aportantes", "n_proyectos_ajenos", "valor_z023",
                 "aportes_otras_entidades"]

ETIQUETAS = {
    "n_proyectos_z023": "N.º proyectos en Z023", "n_entidades_aportantes": "N.º entidades aportantes (Z023)",
    "n_proyectos_ajenos": "N.º proyectos de otras entidades (Z023)", "valor_z023": "Valor de actividades Z023 (vigencia)",
    "aportes_otras_entidades": "Aportes de otras entidades (Z023)",
    "codigo_entidad": "Cód. entidad", "codigo_mp": "Código MP", "descripcion_mp": "Descripción de la meta",
    "mr_del_mp": "Meta de resultado", "comportamiento": "Comportamiento", "unidad_medida": "Unidad",
    "periodicidad": "Periodicidad", "estado_reporte": "Estado del reporte", "vigencia": "Vigencia",
    "pg": "PG cuatrienio", "meta_vigencia": "Meta vigencia", "meta_vigencia_export": "Meta vigencia según el export de EVAPLAN", "meta_vigencia_np": "Vigencia no programada (NP)",
    "logro_previo": "Logro vigencias cerradas", "resultado": "Resultado (último acumulado)",
    "valor_proyectado": "Valor proyectado (cierre)", "pct_proyectado_vs_meta": "% proyectado vs meta vigencia", "pct_avance_vigencia": "% avance vs meta vigencia",
    "avance_cuatrienio": "Avance cuatrienio", "pct_avance_pg": "% avance vs PG",
    "tiene_plan_de_accion": "Tiene plan de acción", "n_proyectos": "N.º proyectos", "proyectos": "Proyectos asociados",
    "n_registros": "N.º registros presupuestales", "ppto_definitivo": "Ppto. definitivo", "ppto_obligaciones": "Obligaciones",
    "ppto_disponible": "Disponible", "pct_ejecucion_financiera": "% ejecución financiera",
    "avance_actividades": "Avance promedio actividades (0-1)", "avance_por_proyecto": "Avance actividades por proyecto",
    "n_registros_con_obligaciones_sin_avance": "Registros con obligaciones y sin avance físico",
    "n_registros_sin_avance_sin_observacion": "…de ellos, sin observación que lo explique",
    "brecha_meta_vs_actividades": "Brecha meta vs actividades", "focalizacion": "Focalización",
    "principal_logro": "Principal logro", "analisis_logro": "Análisis del logro",
    "dificultades_gestiones": "Dificultades o gestiones", "menciona_gestion": "Menciona gestión/donación/cofinanciación",
    "n_alertas": "N.º alertas", "alertas": "Alertas",
}


def _focalizacion(r) -> object:
    """Texto con los grupos poblacionales que tienen datos (misma lógica que la página original)."""
    if r is None:
        return pd.NA
    partes = []
    for canon, origen in FOCALIZACION:
        v = r[canon] if canon in r.index else pd.NA
        if not _na(v) and float(v) != 0:
            partes.append(f"{origen}: {float(v):g}")
    if "foc_otro_cual" in r.index and not _na(r["foc_otro_cual"]):
        partes.append(f"¿Cuál Otro?: {r['foc_otro_cual']}")
    return " | ".join(partes) if partes else "No reporta focalización."


def _na(x) -> bool:
    return x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x))


def _num(x):
    return pd.NA if _na(x) else float(x)


def _consolidar_plan_de_accion(ce: pd.DataFrame) -> pd.DataFrame:
    """Una fila por meta de producto con presupuesto sumado y avance de actividades (global y por proyecto)."""
    filas = []
    for mp, g in ce.groupby("codigo_mp"):
        # % de avance vacío con cantidad programada = sin ejecución reportada: cuenta como 0, igual que EVAPLAN con las
        # centralizadas (cantidad ejecutada vacía -> 0 %). Sin cantidad programada no hay avance que medir (queda vacío).
        avance = g["avance_actividad_pct"].where(
            g["avance_actividad_pct"].notna() | (g["cant_programada_vigencia"].fillna(0) <= 0), 0.0)
        por_proyecto = avance.groupby(g["codigo_proyecto"]).mean()
        proyectos = (g[["codigo_proyecto", "nombre_proyecto"]].drop_duplicates()
                     .apply(lambda r: f"{r['codigo_proyecto']} - {r['nombre_proyecto']}", axis=1))
        # Registros con obligaciones, sin avance físico y con cantidad programada en la vigencia
        sin_avance = g[(g["ppto_obligaciones"].fillna(0) > 0) & (g["avance_actividad_pct"].fillna(0) == 0)
                       & (g["cant_programada_vigencia"].fillna(0) > 0)]
        filas.append({
            "codigo_mp": mp,
            "n_proyectos": g["codigo_proyecto"].nunique(),
            "proyectos": " | ".join(proyectos),
            "n_registros": len(g),            # NO se agrupa por actividad: sus códigos no son confiables
            "ppto_definitivo": g["ppto_definitivo"].sum(min_count=1),
            "ppto_obligaciones": g["ppto_obligaciones"].sum(min_count=1),
            "ppto_disponible": g["ppto_disponible"].sum(min_count=1),
            # fracción 0-1, como la usa el prompt del auditor (promedio por registro, como la página original)
            "avance_actividades": avance.mean() / 100,
            "avance_por_proyecto": " | ".join(f"{p}: {v:.1f} %" for p, v in por_proyecto.items() if not _na(v)),
            "n_registros_con_obligaciones_sin_avance": len(sin_avance),
            "n_registros_sin_avance_sin_observacion": int(sin_avance["observacion"].isna().sum()),
        })
    return pd.DataFrame(filas)


def construir_matriz(pi_mp: pd.DataFrame, centralizadas: pd.DataFrame, drive_mp: pd.DataFrame | None = None,
                     vigencia: int | None = None, criterio_flexible: bool = False,
                     z023: pd.DataFrame | None = None) -> pd.DataFrame:
    """Matriz de seguimiento: una fila por meta de producto de la(s) dependencia(s) del export.

    Si se da `drive_mp`, el universo de metas es el del Plan Indicativo (así aparecen las metas SIN REPORTE);
    si no, solo las metas que vienen en el export de EVAPLAN. Si se da `z023`, se agregan las columnas de
    aportes (proyectos de la propia y de otras entidades que aportan a la meta, `COLUMNAS_Z023`).
    """
    if vigencia is None:
        vigencia = (inferir_vigencia(drive_mp) if drive_mp is not None else None) or max(
            ANIOS[0], min(ANIOS[-1], pd.Timestamp.today().year))
    entidades = set(pi_mp["codigo_entidad"].dropna()) | set(centralizadas["codigo_entidad"].dropna())
    anios_cerrados = [a for a in ANIOS if a < vigencia]

    rep = pi_mp.drop_duplicates("codigo_mp").set_index("codigo_mp")
    if drive_mp is not None:
        dr = drive_mp[drive_mp["entidad_codigo"].isin(entidades)].drop_duplicates("codigo_mp").set_index("codigo_mp")
        universo = list(dict.fromkeys([*dr.index, *rep.index]))
    else:
        dr, universo = pd.DataFrame(), list(rep.index)

    plan = _consolidar_plan_de_accion(centralizadas).set_index("codigo_mp") if len(centralizadas) else pd.DataFrame()

    filas = []
    for mp in universo:
        r = rep.loc[mp] if mp in rep.index else None
        d = dr.loc[mp] if len(dr) and mp in dr.index else None
        base = d if d is not None else r             # programación: Drive manda cuando existe

        def de_base(col, alt=None):
            for fuente in (base, r, d):
                if fuente is not None and col in fuente.index and not _na(fuente[col]):
                    return fuente[col]
            return pd.NA if alt is None else alt

        comp = de_base("comportamiento")
        meta = de_base(f"valor_{vigencia}")
        meta_np = bool(de_base(f"valor_{vigencia}_np", False)) if not _na(de_base(f"valor_{vigencia}_np", False)) else False
        resultado = _num(r["resultado"]) if r is not None else pd.NA
        previos = [de_base(f"valor_{a}") for a in anios_cerrados]
        logro_previo = (sum(0.0 if _na(v) else float(v) for v in previos)
                        if comp in COMPORTAMIENTOS_ACUMULATIVOS else pd.NA)
        pg = de_base("valor_pg")
        proyectado = _num(r["valor_proyectado"]) if r is not None else pd.NA
        pct_proy = (proyectado / float(meta)) if not _na(proyectado) and not _na(meta) and float(meta) > 0 else pd.NA
        pct_vig = (resultado / float(meta)) if not _na(resultado) and not _na(meta) and float(meta) > 0 else pd.NA
        avance_cuat = (logro_previo + resultado) if not _na(logro_previo) and not _na(resultado) else pd.NA
        pct_pg = (avance_cuat / float(pg)) if not _na(avance_cuat) and not _na(pg) and float(pg) > 0 else pd.NA

        p = plan.loc[mp] if len(plan) and mp in plan.index else None
        definitivo = _num(p["ppto_definitivo"]) if p is not None else pd.NA
        obligaciones = _num(p["ppto_obligaciones"]) if p is not None else pd.NA
        pct_fin = obligaciones / definitivo if not _na(obligaciones) and not _na(definitivo) and definitivo > 0 else pd.NA
        avance_act = _num(p["avance_actividades"]) if p is not None else pd.NA

        textos = [r[c] if r is not None and not _na(r[c]) else "" for c in
                  ("principal_logro", "analisis_logro", "dificultades_gestiones")]
        filas.append({
            "codigo_entidad": de_base("codigo_entidad", de_base("entidad_codigo")),
            "codigo_mp": mp,
            "descripcion_mp": (r["descripcion_mp"] if r is not None else
                               (d["meta_producto"] if d is not None else pd.NA)),
            "mr_del_mp": de_base("mr_del_mp"),
            "comportamiento": comp, "unidad_medida": de_base("unidad_medida"), "periodicidad": de_base("periodicidad"),
            "estado_reporte": "Reportada" if r is not None else "Sin reporte en EVAPLAN",
            "vigencia": vigencia, "pg": _num(pg), "meta_vigencia": _num(meta), "meta_vigencia_np": meta_np,
            "meta_vigencia_export": _num(r[f"valor_{vigencia}"]) if r is not None and f"valor_{vigencia}" in r.index else pd.NA,
            "logro_previo": logro_previo,
            "resultado": resultado, "valor_proyectado": proyectado, "pct_proyectado_vs_meta": pct_proy,
            "pct_avance_vigencia": pct_vig, "avance_cuatrienio": avance_cuat, "pct_avance_pg": pct_pg,
            "tiene_plan_de_accion": p is not None,
            "n_proyectos": p["n_proyectos"] if p is not None else 0,
            "proyectos": p["proyectos"] if p is not None else pd.NA,
            "n_registros": p["n_registros"] if p is not None else 0,
            "ppto_definitivo": definitivo, "ppto_obligaciones": obligaciones,
            "ppto_disponible": _num(p["ppto_disponible"]) if p is not None else pd.NA,
            "pct_ejecucion_financiera": pct_fin,
            "avance_actividades": avance_act,
            "avance_por_proyecto": p["avance_por_proyecto"] if p is not None else pd.NA,
            "n_registros_con_obligaciones_sin_avance":
                p["n_registros_con_obligaciones_sin_avance"] if p is not None else 0,
            "n_registros_sin_avance_sin_observacion":
                p["n_registros_sin_avance_sin_observacion"] if p is not None else 0,
            "brecha_meta_vs_actividades": (pct_vig - avance_act) if not _na(pct_vig) and not _na(avance_act) else pd.NA,
            "focalizacion": _focalizacion(r),
            "principal_logro": textos[0] or pd.NA, "analisis_logro": textos[1] or pd.NA,
            "dificultades_gestiones": textos[2] or pd.NA,
            "menciona_gestion": bool(_RE_GESTION.search(" ".join(textos))),
        })
    m = pd.DataFrame(filas)
    if z023 is not None:
        eq = A.equivalencias_z023(A.entidades_de(pi_mp, centralizadas), z023)
        m = m.join(A.resumen_por_meta(A.construir_aportes(z023, m, vigencia, eq), m["codigo_mp"]), on="codigo_mp")
    h = detectar_hallazgos(m, criterio_flexible)
    if len(h):
        # El texto lista primero lo que requiere revisión y después lo informativo; el contador solo cuenta lo primero.
        h = h.assign(_txt=h.apply(lambda r: r["detalle"] if r["severidad"] != "info" else f"ℹ️ {r['detalle']}", axis=1))
        por_mp = h.groupby("llave")["_txt"].agg(" · ".join)
        n_rev = h[h["severidad"] != "info"].groupby("llave").size()
    else:
        por_mp, n_rev = pd.Series(dtype=str), pd.Series(dtype=int)
    m["alertas"] = m["codigo_mp"].map(por_mp).fillna("").astype("string")
    m["n_alertas"] = m["codigo_mp"].map(n_rev).fillna(0).astype(int)      # sin contar las informativas
    for c in ("pg", "meta_vigencia", "meta_vigencia_export", "logro_previo", "resultado", "valor_proyectado", "pct_proyectado_vs_meta", "pct_avance_vigencia",
              "avance_cuatrienio", "pct_avance_pg", "ppto_definitivo", "ppto_obligaciones", "ppto_disponible",
              "pct_ejecucion_financiera", "avance_actividades", "brecha_meta_vs_actividades"):
        m[c] = m[c].astype("Float64")
    return m[COLUMNAS_MATRIZ + (COLUMNAS_Z023 if z023 is not None else [])]


def detectar_hallazgos(m: pd.DataFrame, criterio_flexible: bool = False) -> pd.DataFrame:
    """Incoherencias objetivas por meta (sin umbrales). Formato igual al de `validaciones`.

    Criterio por defecto (lineamiento de la líder del equipo): un avance 0 se justifica en *Dificultades*. Con
    `criterio_flexible=True` también se acepta el *Análisis del logro* (decisión posterior del equipo).
    """
    out = []

    def add(regla, sev, fila, detalle):
        out.append({"regla": regla, "severidad": sev, "fuente": "seguimiento", "llave": fila["codigo_mp"],
                    "fila_excel": None, "detalle": detalle})

    for _, f in m.iterrows():
        if "n_proyectos_z023" in m.columns:      # solo si se cargó el Z023
            if f["n_proyectos_z023"] == 0:
                add("meta_sin_proyectos_en_z023", "info", f,
                    f"El Z023 no tiene actividades de ningún proyecto para esta meta en {f['vigencia']}")
            elif not _na(f["aportes_otras_entidades"]):
                add("meta_con_aportes_de_otras_entidades", "info", f,
                    f"Meta compartida: según el Z023 también le aportan {f['n_proyectos_ajenos']} proyecto(s) de otras "
                    f"entidades ({f['aportes_otras_entidades']}). Quien reporta debe conocer ese avance")
        if f["estado_reporte"] != "Reportada":
            add("sin_reporte", "advertencia", f,
                "La dependencia no aparece en el export de EVAPLAN para esta meta (probable: no reportó)")
            continue
        res, obl = f["resultado"], f["ppto_obligaciones"]
        me, mv = f["meta_vigencia_export"], f["meta_vigencia"]
        if not _na(me) and not _na(mv) and abs(me - mv) > 1e-6 * max(1.0, abs(me), abs(mv)):
            add("meta_vigencia_difiere_del_export", "advertencia", f,
                f"La meta {f['vigencia']} en el export de EVAPLAN ({me:g}) difiere de la del Plan Indicativo de Drive "
                f"({mv:g}); prevalece Drive (el operador de EVAPLAN a veces no lo tiene actualizado)")
        if _na(res):
            add("resultado_vacio", "advertencia", f, "Reporta la meta pero el campo Resultado está vacío")
            continue
        if res > 0 and (f["meta_vigencia_np"] or _na(f["meta_vigencia"]) or f["meta_vigencia"] <= 0):
            add("reporte_sin_meta_programada", "advertencia", f,
                f"Reporta avance ({res:g}) pero la vigencia {f['vigencia']} no tiene meta programada")
        if not f["tiene_plan_de_accion"]:
            add("sin_plan_de_accion", "info", f,
                "La meta no tiene actividades en Centralizadas de esta dependencia (puede ejecutarla un proyecto de otra "
                "dependencia con la que comparte la meta; quien reporta debe estar enterado de ese avance)")
        else:
            if res > 0 and not _na(obl) and obl == 0:
                if f["menciona_gestion"]:
                    add("avance_sin_ejecucion_con_gestion", "info", f,
                        "Avance sin obligaciones; la narrativa menciona gestión/donación/cofinanciación (verificar soporte)")
                else:
                    add("avance_sin_ejecucion_financiera", "advertencia", f,
                        "Reporta avance físico sin obligaciones en sus actividades y sin justificar gestión, donación, "
                        "cofinanciación o sin costo. Si el avance viene de un proyecto de otra dependencia con la que "
                        "comparte la meta, quien reporta debe conocerlo e indicarlo en la narrativa")
            n_sin, n_sin_obs = (int(f["n_registros_con_obligaciones_sin_avance"]),
                                int(f["n_registros_sin_avance_sin_observacion"]))
            if n_sin_obs > 0:
                add("registros_con_obligaciones_sin_avance", "advertencia", f,
                    f"{n_sin_obs} registro(s) presupuestal(es) con obligaciones, sin avance físico y sin observación que lo explique")
            elif n_sin > 0:
                add("registros_sin_avance_con_observacion", "info", f,
                    f"{n_sin} registro(s) presupuestal(es) con obligaciones y sin avance físico, explicados en su observación")
        if res > 0 and (_na(f["principal_logro"]) or _na(f["analisis_logro"])):
            add("resultado_sin_narrativa", "advertencia", f, "Reporta avance pero falta Principal Logro o Análisis del Logro")
        justificado = (not _na(f["dificultades_gestiones"])) or (criterio_flexible and not _na(f["analisis_logro"]))
        donde = "ni en Análisis del logro ni en Dificultades" if criterio_flexible else "en Dificultades"
        if res == 0 and not justificado:
            if f["tiene_plan_de_accion"] and not _na(obl) and obl > 0:
                add("ejecucion_sin_avance_sin_explicacion", "advertencia", f,
                    f"Tiene obligaciones, el resultado de la meta es 0 y no hay justificación {donde}")
            else:
                add("avance_cero_sin_justificacion", "advertencia", f,
                    f"Resultado 0 sin justificación {donde}: el avance 0 debe explicarse")
        if res == 0 and not criterio_flexible and (not _na(f["principal_logro"]) or not _na(f["analisis_logro"])):
            add("narrativa_con_resultado_cero", "info", f,
                "Resultado 0 con Principal logro o Análisis del logro: según el lineamiento, un avance 0 se explica en Dificultades")
        proy = f["valor_proyectado"]
        if not _na(proy) and not _na(f["meta_vigencia"]) and not f["meta_vigencia_np"] and proy < f["meta_vigencia"]:
            add("proyeccion_bajo_meta", "advertencia", f,
                f"La dependencia proyecta cerrar en {proy:g}, por debajo de la meta de la vigencia ({f['meta_vigencia']:g})")
        if not _na(proy) and proy < res and f["comportamiento"] in COMPORTAMIENTOS_ACUMULATIVOS:
            add("proyeccion_menor_que_resultado", "advertencia", f,
                f"La proyección de cierre ({proy:g}) es menor que el resultado ya acumulado ({res:g})")
        if not _na(f["pct_avance_vigencia"]) and f["pct_avance_vigencia"] > 1:
            add("resultado_supera_meta_vigencia", "info", f,
                f"El resultado ({res:g}) supera la meta de la vigencia ({f['meta_vigencia']:g})")
    h = pd.DataFrame(out, columns=COLUMNAS_HALLAZGO)
    orden = {"error": 0, "advertencia": 1, "info": 2}
    return h.sort_values("severidad", key=lambda s: s.map(orden), kind="stable").reset_index(drop=True)


def resumen(m: pd.DataFrame) -> dict:
    """Cifras de cabecera para mostrar en la página."""
    rep = m[m["estado_reporte"] == "Reportada"]
    return {
        "metas_en_plan_indicativo": len(m),
        "metas_reportadas": len(rep),
        "metas_sin_reporte": int((m["estado_reporte"] != "Reportada").sum()),
        "metas_con_plan_de_accion": int(m["tiene_plan_de_accion"].sum()),
        "metas_con_alertas": int((m["n_alertas"] > 0).sum()),
        "ppto_definitivo": float(m["ppto_definitivo"].sum()),
        "ppto_obligaciones": float(m["ppto_obligaciones"].sum()),
    }
