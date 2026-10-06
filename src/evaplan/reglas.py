"""Nombres legibles de las reglas (para pantalla y Excel). El código técnico se conserva en la columna `regla`."""
from __future__ import annotations

import pandas as pd

ETIQUETAS_REGLAS = {
    # --- seguimiento por meta
    "sin_reporte": "Meta sin reporte en EVAPLAN",
    "resultado_vacio": "Meta reportada con el Resultado vacío",
    "reporte_sin_meta_programada": "Avance reportado sin meta programada en la vigencia",
    "sin_plan_de_accion": "Meta sin actividades en el Plan de Acción de la dependencia",
    "avance_sin_ejecucion_financiera": "Avance físico sin obligaciones (sin justificar gestión)",
    "avance_sin_ejecucion_con_gestion": "Avance sin obligaciones, justificado como gestión",
    "ejecucion_sin_avance_sin_explicacion": "Obligaciones y resultado 0, sin justificación",
    "avance_cero_sin_justificacion": "Resultado 0 sin justificación",
    "registros_con_obligaciones_sin_avance": "Registros con obligaciones y sin avance (sin observación)",
    "registros_sin_avance_con_observacion": "Registros con obligaciones y sin avance, explicados en la observación",
    "narrativa_con_resultado_cero": "Resultado 0 con logro o análisis (debe explicarse en Dificultades)",
    "resultado_sin_narrativa": "Avance sin Principal logro o Análisis",
    "proyeccion_bajo_meta": "Proyección de cierre por debajo de la meta",
    "proyeccion_menor_que_resultado": "Proyección menor que el resultado ya acumulado",
    "resultado_supera_meta_vigencia": "Resultado supera la meta de la vigencia",
    "meta_vigencia_difiere_del_export": "Meta de la vigencia distinta entre EVAPLAN y Drive",
    # --- calidad de datos y cruces
    "llave_unica": "ID repetido",
    "codigo_mp_formato": "Código de meta con formato inválido",
    "codigo_mp_vs_programa": "Programa no coincide con el código de la meta",
    "codigo_mp_vs_subprograma": "Subprograma no coincide con el código de la meta",
    "codigo_mp_vs_producto_mga": "Producto MGA no coincide con el código de la meta",
    "mr_inexistente": "Meta de resultado inexistente",
    "mp_falta_en_evaplan": "Meta del Plan Indicativo sin reporte en EVAPLAN",
    "mp_falta_en_drive": "Meta de EVAPLAN que no está en el Plan Indicativo de Drive",
    "actividad_sin_meta_en_pi": "Registros que aportan a una meta de otra dependencia",
    "meta_sin_actividades": "Meta sin actividades en Centralizadas",
    "valores_difieren": "Valores de EVAPLAN distintos a los de Drive",
    "pg_vs_anios[pi]": "PG no coincide con los años (según el comportamiento)",
    "presupuesto_incompleto": "Presupuesto incompleto",
    "presupuesto_negativo": "Cifras presupuestales negativas",
    "obligaciones_mayores_definitivo": "Obligaciones mayores al presupuesto definitivo",
    "disponible_excede_saldo": "Disponible mayor al saldo",
    "sin_programacion_fisica": "Registro sin cantidad programada en la vigencia",
    "avance_vacio_con_programacion": "Registros con cantidad programada y % de avance vacío (cuentan como 0 %)",
    "avance_no_coincide": "% de avance no coincide con ejecutada/programada",
    "avance_supera_100": "Avance físico mayor a 100 %",
    "financiero_sin_fisico": "Obligaciones sin avance físico y sin observación",
    "financiero_sin_fisico_con_observacion": "Obligaciones sin avance físico, explicadas en la observación",
    "estado_vs_obligaciones": "Estado de la actividad no coincide con las obligaciones",
    "proyecto_con_varios_bpin": "Proyecto con más de un BPIN",
    "actividad_fuera_de_proyecto": "Código de actividad no corresponde a su proyecto",
    "ppto_supera_recursos_pi": "Presupuesto definitivo mayor a los recursos del Plan Indicativo",
    "vigencia_cerrada_sin_marca_logro": "Vigencia cerrada sin marca de logro (VAL ALC) en Drive",
    "vigencia_abierta_con_marca_logro": "Vigencia abierta con marca de logro (VAL ALC) en Drive",
    # --- Z023 consolidado
    "meta_con_aportes_de_otras_entidades": "Meta compartida: le aportan proyectos de otras entidades (Z023)",
    "meta_sin_proyectos_en_z023": "Meta sin actividades en el Z023 en la vigencia",
    "z023_sin_meta_producto": "Actividad del Z023 sin meta de producto",
    "z023_mp_formato": "Meta de producto del Z023 con formato incorrecto",
    "z023_bpin_no_valido": "Proyecto del Z023 con BPIN vacío o no válido",
    "actividad_no_esta_en_z023": "Actividad de Centralizadas que no está en el Z023",
    "mp_distinta_en_z023": "Actividad con meta de producto distinta en Centralizadas y en el Z023",
}


def etiqueta_regla(regla: str) -> str:
    return ETIQUETAS_REGLAS.get(regla, str(regla).replace("_", " "))


def etiquetar(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna `hallazgo` (texto legible) antes de `regla`."""
    if "regla" not in df.columns:
        return df
    out = df.copy()
    out.insert(list(out.columns).index("regla"), "hallazgo", out["regla"].map(etiqueta_regla))
    return out
