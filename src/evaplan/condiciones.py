"""Comprobación de las condiciones OBJETIVAS de las Alertas Tipo 1, 2 y 3 del prompt del auditor.

Motivo (prueba con un modelo de IA sencillo, 6-oct): con los mismos datos, el modelo confundía los tipos de alerta
(llamaba "Tipo 1" a obligaciones con resultado 0, que es Tipo 2, y "Tipo 3" a la diferencia entre los dos promedios
de actividades). Aquí se comprueba solo lo que el prompt define con cifras, con los mismos umbrales que el prompt
(30 % y sus ejemplos). Si la narrativa explica o no la situación, y el dictamen, siguen siendo juicio de la IA o de
quien revisa: por eso se informa "se cumple la condición", no "se devuelve".
"""
from __future__ import annotations

from . import formato as F

UMBRAL_TIPO_2 = 0.30          # "Total Obligaciones altas (> 30%)" (prompt)
UMBRAL_TIPO_3_META = 1.0      # "avance muy alto (ej. 100%)" (prompt)
UMBRAL_TIPO_3_ACTIVIDADES = 0.30   # "críticamente bajo (ej. < 30%)" (prompt)


def _na(x) -> bool:
    return F.es_na(x)


def _porcentajes_por_proyecto(texto) -> list[float]:
    """'P1: 50,0 % | P2: 0,0 %' -> [0.5, 0.0]."""
    if _na(texto):
        return []
    out = []
    for parte in str(texto).split(" | "):
        try:
            out.append(float(parte.rsplit(":", 1)[1].replace("%", "").replace(".", "").replace(",", ".").strip()) / 100)
        except (IndexError, ValueError):
            continue
    return out


def condiciones_prompt(f) -> list[dict]:
    """[{tipo, nombre, se_cumple (True/False/None), hechos}] para una fila de la matriz."""
    res, obl = f["resultado"], f["ppto_obligaciones"]
    pct_fin, pct_meta, act = f["pct_ejecucion_financiera"], f["pct_avance_vigencia"], f["avance_actividades"]
    tiene_pa = bool(f["tiene_plan_de_accion"])
    dificultades = "vacío" if _na(f["dificultades_gestiones"]) else "diligenciado (revisa si explica la situación)"
    out = []

    # Tipo 1: avance físico > 0 con obligaciones = 0 (sin justificar gestión)
    if _na(res) or not tiene_pa:
        t1, h1 = None, ("no se puede comprobar: " + ("no hay resultado reportado" if _na(res) else
                                                    "la dependencia no tiene plan de acción para la meta"))
    else:
        t1 = res > 0 and (_na(obl) or obl == 0)
        h1 = (f"resultado {F.numero(res)}; obligaciones {F.pesos(obl)}"
              + (f"; la narrativa {'SÍ' if f['menciona_gestion'] else 'NO'} menciona gestión, donación, cofinanciación "
                 "o sin costo" if t1 else ""))
    out.append({"tipo": 1, "nombre": "Falso positivo físico (avance sin obligaciones)", "se_cumple": t1, "hechos": h1})

    # Tipo 2: obligaciones > 30 % del definitivo y avance físico = 0
    if _na(res) or not tiene_pa or _na(pct_fin):
        t2, h2 = None, "no se puede comprobar: falta el resultado o la ejecución financiera"
    else:
        t2 = res == 0 and pct_fin > UMBRAL_TIPO_2
        h2 = (f"resultado {F.numero(res)}; ejecución financiera {F.porcentaje(pct_fin)} (el prompt exige más de 30 %)"
              f"; Dificultades: {dificultades}")
        if f["n_registros_con_obligaciones_sin_avance"]:
            h2 += (f"; además, {int(f['n_registros_con_obligaciones_sin_avance'])} actividad(es) con obligaciones "
                   "tienen avance físico 0")
    out.append({"tipo": 2, "nombre": "Omisión de reporte físico (obligaciones altas y avance 0)", "se_cumple": t2,
                "hechos": h2})

    # Tipo 3: meta con avance muy alto y actividades críticamente bajas (en total o en algún proyecto)
    if _na(pct_meta) or _na(act):
        t3, h3 = None, "no se puede comprobar: falta el avance de la meta o el de las actividades"
    else:
        minimo_proyecto = min(_porcentajes_por_proyecto(f["avance_por_proyecto"]), default=act)
        t3 = pct_meta >= UMBRAL_TIPO_3_META and min(act, minimo_proyecto) < UMBRAL_TIPO_3_ACTIVIDADES
        relacion = ("la meta va POR ENCIMA de las actividades" if pct_meta > act else
                    "la meta va POR DEBAJO de las actividades (esta alerta es para el caso contrario)" if pct_meta < act
                    else "la meta y las actividades van iguales")
        h3 = (f"avance de la meta {F.porcentaje(pct_meta)}; avance de todas las actividades {F.porcentaje(act)}; "
              f"proyecto con menor avance {F.porcentaje(minimo_proyecto)}; {relacion}")
    out.append({"tipo": 3, "nombre": "Desconexión jerárquica (meta muy alta y actividades muy bajas)", "se_cumple": t3,
                "hechos": h3})
    return out


def texto_condicion(c: dict) -> str:
    estado = {True: "SE CUMPLE", False: "NO se cumple", None: "NO SE PUEDE COMPROBAR"}[c["se_cumple"]]
    return f"Alerta Tipo {c['tipo']} ({c['nombre']}): {estado}. Datos: {c['hechos']}."
