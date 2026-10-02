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

from .esquemas import FOCALIZACION
from .validaciones import ANIOS, COLUMNAS_HALLAZGO, inferir_vigencia

COMPORTAMIENTOS_ACUMULATIVOS = ("Incremento Acumulado", "Incremento Capacidad")
_RE_GESTION = re.compile(r"gesti[oó]n|donaci[oó]n|cofinanci|sin\s+costo", re.IGNORECASE)

COLUMNAS_MATRIZ = [
    "codigo_entidad", "codigo_mp", "descripcion_mp", "mr_del_mp", "comportamiento", "unidad_medida", "periodicidad",
    "estado_reporte", "vigencia", "pg", "meta_vigencia", "meta_vigencia_export", "meta_vigencia_np", "logro_previo",
    "resultado", "valor_proyectado", "pct_proyectado_vs_meta", "pct_avance_vigencia", "avance_cuatrienio", "pct_avance_pg",
    "tiene_plan_de_accion", "n_proyectos", "proyectos", "n_actividades", "n_registros",
    "ppto_definitivo", "ppto_obligaciones", "ppto_disponible", "pct_ejecucion_financiera",
    "avance_actividades", "avance_por_proyecto", "n_actividades_con_obligaciones_sin_avance",
    "n_actividades_sin_avance_sin_observacion", "brecha_meta_vs_actividades",
    "focalizacion", "principal_logro", "analisis_logro", "dificultades_gestiones", "menciona_gestion",
    "n_alertas", "alertas",
]

ETIQUETAS = {
    "codigo_entidad": "Cód. entidad", "codigo_mp": "Código MP", "descripcion_mp": "Descripción de la meta",
    "mr_del_mp": "Meta de resultado", "comportamiento": "Comportamiento", "unidad_medida": "Unidad",
    "periodicidad": "Periodicidad", "estado_reporte": "Estado del reporte", "vigencia": "Vigencia",
    "pg": "PG cuatrienio", "meta_vigencia": "Meta vigencia", "meta_vigencia_export": "Meta vigencia según el export de EVAPLAN", "meta_vigencia_np": "Vigencia no programada (NP)",
    "logro_previo": "Logro vigencias cerradas", "resultado": "Resultado (último acumulado)",
    "valor_proyectado": "Valor proyectado (cierre)", "pct_proyectado_vs_meta": "% proyectado vs meta vigencia", "pct_avance_vigencia": "% avance vs meta vigencia",
    "avance_cuatrienio": "Avance cuatrienio", "pct_avance_pg": "% avance vs PG",
    "tiene_plan_de_accion": "Tiene plan de acción", "n_proyectos": "N.º proyectos", "proyectos": "Proyectos asociados",
    "n_actividades": "N.º actividades", "n_registros": "N.º registros presupuestales", "ppto_definitivo": "Ppto. definitivo", "ppto_obligaciones": "Obligaciones",
    "ppto_disponible": "Disponible", "pct_ejecucion_financiera": "% ejecución financiera",
    "avance_actividades": "Avance promedio actividades (0-1)", "avance_por_proyecto": "Avance actividades por proyecto",
    "n_actividades_con_obligaciones_sin_avance": "Actividades con obligaciones y sin avance",
    "n_actividades_sin_avance_sin_observacion": "…de ellas, sin observación que lo explique",
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
        por_proyecto = g.groupby("codigo_proyecto")["avance_actividad_pct"].mean()
        proyectos = (g[["codigo_proyecto", "nombre_proyecto"]].drop_duplicates()
                     .apply(lambda r: f"{r['codigo_proyecto']} - {r['nombre_proyecto']}", axis=1))
        # Registros con obligaciones, sin avance físico y con cantidad programada en la vigencia
        sin_avance = g[(g["ppto_obligaciones"].fillna(0) > 0) & (g["avance_actividad_pct"].fillna(0) == 0)
                       & (g["cant_programada_vigencia"].fillna(0) > 0)]
        filas.append({
            "codigo_mp": mp,
            "n_proyectos": g["codigo_proyecto"].nunique(),
            "proyectos": " | ".join(proyectos),
            "n_actividades": g["codigo_actividad"].nunique(),      # una actividad puede tener varios registros
            "n_registros": len(g),
            "ppto_definitivo": g["ppto_definitivo"].sum(min_count=1),
            "ppto_obligaciones": g["ppto_obligaciones"].sum(min_count=1),
            "ppto_disponible": g["ppto_disponible"].sum(min_count=1),
            # fracción 0-1, como la usa el prompt del auditor (promedio por registro, como la página original)
            "avance_actividades": g["avance_actividad_pct"].mean() / 100,
            "avance_por_proyecto": " | ".join(f"{p}: {v:.1f} %" for p, v in por_proyecto.items() if not _na(v)),
            "n_actividades_con_obligaciones_sin_avance": sin_avance["codigo_actividad"].nunique(),
            "n_actividades_sin_avance_sin_observacion": sin_avance[sin_avance["observacion"].isna()]["codigo_actividad"].nunique(),
        })
    return pd.DataFrame(filas)


def construir_matriz(pi_mp: pd.DataFrame, centralizadas: pd.DataFrame, drive_mp: pd.DataFrame | None = None,
                     vigencia: int | None = None) -> pd.DataFrame:
    """Matriz de seguimiento: una fila por meta de producto de la(s) dependencia(s) del export.

    Si se da `drive_mp`, el universo de metas es el del Plan Indicativo (así aparecen las metas SIN REPORTE);
    si no, solo las metas que vienen en el export de EVAPLAN.
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
            "n_actividades": p["n_actividades"] if p is not None else 0,
            "n_registros": p["n_registros"] if p is not None else 0,
            "ppto_definitivo": definitivo, "ppto_obligaciones": obligaciones,
            "ppto_disponible": _num(p["ppto_disponible"]) if p is not None else pd.NA,
            "pct_ejecucion_financiera": pct_fin,
            "avance_actividades": avance_act,
            "avance_por_proyecto": p["avance_por_proyecto"] if p is not None else pd.NA,
            "n_actividades_con_obligaciones_sin_avance":
                p["n_actividades_con_obligaciones_sin_avance"] if p is not None else 0,
            "n_actividades_sin_avance_sin_observacion":
                p["n_actividades_sin_avance_sin_observacion"] if p is not None else 0,
            "brecha_meta_vs_actividades": (pct_vig - avance_act) if not _na(pct_vig) and not _na(avance_act) else pd.NA,
            "focalizacion": _focalizacion(r),
            "principal_logro": textos[0] or pd.NA, "analisis_logro": textos[1] or pd.NA,
            "dificultades_gestiones": textos[2] or pd.NA,
            "menciona_gestion": bool(_RE_GESTION.search(" ".join(textos))),
        })
    m = pd.DataFrame(filas)
    h = detectar_hallazgos(m)
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
    return m[COLUMNAS_MATRIZ]


def detectar_hallazgos(m: pd.DataFrame) -> pd.DataFrame:
    """Incoherencias objetivas por meta (sin umbrales). Formato igual al de `validaciones`."""
    out = []

    def add(regla, sev, fila, detalle):
        out.append({"regla": regla, "severidad": sev, "fuente": "seguimiento", "llave": fila["codigo_mp"],
                    "fila_excel": None, "detalle": detalle})

    for _, f in m.iterrows():
        if f["estado_reporte"] != "Reportada":
            add("sin_reporte", "advertencia", f,
                "La dependencia no aparece en el export de EVAPLAN para esta meta (probable: no reportó)")
            continue
        res, obl = f["resultado"], f["ppto_obligaciones"]
        me, mv = f["meta_vigencia_export"], f["meta_vigencia"]
        if not _na(me) and not _na(mv) and abs(me - mv) > 1e-6 * max(1.0, abs(me), abs(mv)):
            add("meta_vigencia_difiere_del_export", "advertencia", f,
                f"La meta {f['vigencia']} en el export de EVAPLAN ({me:g}) difiere de la del Plan Indicativo de Drive "
                f"({mv:g}); el cálculo usa la de Drive (probable reprogramación posterior al export)")
        if _na(res):
            add("resultado_vacio", "advertencia", f, "Reporta la meta pero el campo Resultado está vacío")
            continue
        if res > 0 and (f["meta_vigencia_np"] or _na(f["meta_vigencia"]) or f["meta_vigencia"] <= 0):
            add("reporte_sin_meta_programada", "advertencia", f,
                f"Reporta avance ({res:g}) pero la vigencia {f['vigencia']} no tiene meta programada")
        if not f["tiene_plan_de_accion"]:
            add("sin_plan_de_accion", "info", f,
                "La meta no tiene actividades en Centralizadas de esta dependencia (puede ejecutarla un proyecto de "
                "otra dependencia): no se puede cruzar con presupuesto")
        else:
            if res > 0 and not _na(obl) and obl == 0:
                if f["menciona_gestion"]:
                    add("avance_sin_ejecucion_con_gestion", "info", f,
                        "Avance sin obligaciones; la narrativa menciona gestión/donación/cofinanciación (verificar soporte)")
                else:
                    add("avance_sin_ejecucion_financiera", "advertencia", f,
                        "Reporta avance físico sin obligaciones en sus actividades y sin justificar gestión, donación, "
                        "cofinanciación o sin costo (o el aporte viene de un proyecto de otra dependencia: validar con ella)")
            n_sin, n_sin_obs = (int(f["n_actividades_con_obligaciones_sin_avance"]),
                                int(f["n_actividades_sin_avance_sin_observacion"]))
            if n_sin_obs > 0:
                add("actividades_con_obligaciones_sin_avance", "advertencia", f,
                    f"{n_sin_obs} actividad(es) con obligaciones, sin avance físico y sin observación que lo explique")
            elif n_sin > 0:
                add("actividades_sin_avance_con_observacion", "info", f,
                    f"{n_sin} actividad(es) con obligaciones y sin avance físico, explicadas en su observación")
        if res > 0 and (_na(f["principal_logro"]) or _na(f["analisis_logro"])):
            add("resultado_sin_narrativa", "advertencia", f, "Reporta avance pero falta Principal Logro o Análisis del Logro")
        if res == 0 and _na(f["analisis_logro"]) and _na(f["dificultades_gestiones"]):
            if f["tiene_plan_de_accion"] and not _na(obl) and obl > 0:
                add("ejecucion_sin_avance_sin_explicacion", "advertencia", f,
                    "Tiene obligaciones, el resultado de la meta es 0 y no hay justificación (ni en Análisis del logro ni en Dificultades)")
            else:
                add("avance_cero_sin_justificacion", "advertencia", f,
                    "Resultado 0 sin justificación: la circular exige explicar por qué no hubo avance (Análisis del logro o Dificultades)")
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
