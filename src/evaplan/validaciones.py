"""Reglas de integridad y cruces entre las fuentes. Cada regla devuelve hallazgos; nunca modifica datos.

Severidades:
    error        La integridad está rota: el dato no es confiable (llave duplicada, cruce imposible…).
    advertencia  Merece revisión humana (inconsistencia probable, ejecución sin avance…).
    info         Informativo (metas sin actividades, etc.).

Las reglas marcadas 'por confirmar' en docs/REGLAS_DE_NEGOCIO.md se reportan como advertencia, no como error.
"""
from __future__ import annotations

import math

import pandas as pd

from . import formato as F
from .aportes import entidades_de, equivalencias_z023

COLUMNAS_HALLAZGO = ["regla", "severidad", "fuente", "llave", "fila_excel", "detalle"]
ANIOS = (2024, 2025, 2026, 2027)
TOLERANCIA = 1e-6


def _h(regla, severidad, fuente, llave, detalle, fila=None) -> dict:
    return {"regla": regla, "severidad": severidad, "fuente": fuente, "llave": llave,
            "fila_excel": fila, "detalle": detalle}


def _na(x) -> bool:
    return x is None or x is pd.NA or (isinstance(x, float) and math.isnan(x))


def _fmt(x) -> str:
    """Cantidades con el formato único (formato.py): punto de miles, coma decimal, 'sin dato'."""
    return F.numero(x) if isinstance(x, (int, float)) or _na(x) else str(x)


def _pesos(x) -> str:
    return F.pesos(x)


def _cerca(a, b) -> bool:
    return abs(a - b) <= TOLERANCIA * max(1.0, abs(a), abs(b))


def _como_df(hallazgos: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(hallazgos, columns=COLUMNAS_HALLAZGO)


# ------------------------------------------------------------------ llaves y códigos
def llave_unica(df: pd.DataFrame, columna: str, fuente: str) -> pd.DataFrame:
    dup = df[df[columna].notna() & df[columna].duplicated(keep=False)]
    return _como_df([
        _h("llave_unica", "error", fuente, r[columna], f"'{columna}' repetido", r["fila_excel"])
        for _, r in dup.iterrows()
    ])


def codigo_mp_coherente(df: pd.DataFrame, fuente: str) -> pd.DataFrame:
    """El código MP debe tener 18 caracteres y coincidir con programa/subprograma/producto MGA de la fila."""
    h = []
    for _, r in df.iterrows():
        mp = r["codigo_mp"]
        if not r["codigo_mp_valido"]:
            h.append(_h("codigo_mp_formato", "error", fuente, mp, "no cumple MP+5+2+2+7 dígitos", r["fila_excel"]))
            continue
        if "programa_codigo" in df.columns and not _na(r["programa_codigo"]) and r["programa_codigo"] != r["programa_mp"]:
            h.append(_h("codigo_mp_vs_programa", "error", fuente, mp,
                        f"programa {r['programa_codigo']} distinto de {r['programa_mp']} del código", r["fila_excel"]))
        if "subprograma_codigo" in df.columns and not _na(r["subprograma_codigo"]) \
                and str(r["subprograma_codigo"]).zfill(2) != r["subprograma_mp"]:
            h.append(_h("codigo_mp_vs_subprograma", "error", fuente, mp,
                        f"subprograma {r['subprograma_codigo']} distinto de {r['subprograma_mp']} del código", r["fila_excel"]))
        if "codigo_producto_mga" in df.columns and not _na(r["codigo_producto_mga"]) \
                and r["codigo_producto_mga"] != r["producto_mga_mp"]:
            h.append(_h("codigo_mp_vs_producto_mga", "advertencia", fuente, mp,
                        f"producto MGA {r['codigo_producto_mga']} distinto de {r['producto_mga_mp']} del código", r["fila_excel"]))
    return _como_df(h)


def mr_existe(df_mp: pd.DataFrame, df_mr: pd.DataFrame, fuente: str) -> pd.DataFrame:
    """Toda MP debe colgar de una meta de resultado existente (dígitos 3-7 del código)."""
    existentes = set(df_mr["codigo_mr"].dropna())
    return _como_df([
        _h("mr_inexistente", "error", fuente, r["codigo_mp"], f"MR {r['mr_del_mp']} no está en la tabla de MR", r["fila_excel"])
        for _, r in df_mp.iterrows() if r["codigo_mp_valido"] and r["mr_del_mp"] not in existentes
    ])


# ------------------------------------------------------------------ cobertura entre fuentes
def cobertura_evaplan_vs_drive(pi_evaplan: pd.DataFrame, pi_drive: pd.DataFrame) -> pd.DataFrame:
    """Metas de las entidades del export de EVAPLAN que faltan en un lado u otro."""
    entidades = set(pi_evaplan["codigo_entidad"].dropna())
    drive = pi_drive[pi_drive["entidad_codigo"].isin(entidades)]
    ev, dr = set(pi_evaplan["codigo_mp"]), set(drive["codigo_mp"])
    h = [_h("mp_falta_en_evaplan", "advertencia", "pi_mp_evaplan", mp,
            "Meta del Plan Indicativo SIN REPORTE en el export de EVAPLAN (probable: la dependencia no reportó)",
            int(drive.loc[drive["codigo_mp"] == mp, "fila_excel"].iloc[0]))
         for mp in sorted(dr - ev)]
    h += [_h("mp_falta_en_drive", "error", "pi_mp_evaplan", mp,
             "La meta viene en EVAPLAN pero no existe en el Plan Indicativo de Drive",
             int(pi_evaplan.loc[pi_evaplan["codigo_mp"] == mp, "fila_excel"].iloc[0]))
          for mp in sorted(ev - dr)]
    return _como_df(h)


def cobertura_centralizadas_vs_pi(centralizadas: pd.DataFrame, pi: pd.DataFrame) -> pd.DataFrame:
    en_ce, en_pi = set(centralizadas["codigo_mp"]), set(pi["codigo_mp"])
    h = [_h("actividad_sin_meta_en_pi", "advertencia", "centralizadas", mp,
            "Hay actividades para una meta que no está en el export del Plan Indicativo (¿meta coordinada por OTRA "
            "dependencia? Esa dependencia debe recibir el avance de este proyecto)",
            int(centralizadas.loc[centralizadas["codigo_mp"] == mp, "fila_excel"].iloc[0]))
         for mp in sorted(en_ce - en_pi)]
    h += [_h("meta_sin_actividades", "info", "pi_mp_evaplan", mp,
             "La meta no tiene actividades en Centralizadas de esta dependencia (¿la ejecuta un proyecto de otra dependencia?)",
             int(pi.loc[pi["codigo_mp"] == mp, "fila_excel"].iloc[0]))
          for mp in sorted(en_pi - en_ce)]
    return _como_df(h)


def valores_evaplan_vs_drive(df_ev: pd.DataFrame, df_dr: pd.DataFrame, llave: str = "codigo_mp",
                             fuente: str = "pi_mp_evaplan") -> pd.DataFrame:
    """Compara PG y valores 2024-2027 (incluido 'NP') de EVAPLAN contra el bloque vigente de Drive."""
    campos = ["valor_pg", *[f"valor_{a}" for a in ANIOS]]
    dr = df_dr.set_index(llave)
    h = []
    for _, r in df_ev.iterrows():
        if r[llave] not in dr.index:
            continue
        d = dr.loc[r[llave]]
        difs = []
        for c in campos:
            a, b = r[c], d[c]
            np_a, np_b = bool(r[f"{c}_np"]), bool(d[f"{c}_np"])
            if np_a != np_b or (not np_a and (_na(a) != _na(b) or (not _na(a) and not _cerca(a, b)))):
                txt = lambda v, n: "NP" if n else _fmt(v)  # noqa: E731
                difs.append(f"{c.replace('valor_', '')}: EVAPLAN {txt(a, np_a)} vs Drive {txt(b, np_b)}")
        if difs:
            h.append(_h("valores_difieren", "advertencia", fuente, r[llave], "; ".join(difs), r["fila_excel"]))
    return _como_df(h)


# ------------------------------------------------------------------ reglas de negocio del indicador
def pg_vs_anios(df: pd.DataFrame, fuente: str, prefijo: str = "valor", llave: str = "codigo_mp") -> pd.DataFrame:
    """El PG debe ser coherente con los valores anuales según el comportamiento del indicador (por confirmar).

    Aplica a PROGRAMACIÓN (prefijo 'pi', bloque original de Drive). NO aplicarla al bloque vigente ('valor'),
    porque las vigencias cerradas traen el logro alcanzado y no la meta: daría falsas alarmas.

    Incremento Acumulado: PG = suma de años.  Incremento Flujo y Capacidad: PG = último año (2027).
    Mantenimiento Stock: todos los años = PG.  'Reducción Anual' no se valida.
    """
    h = []
    for _, r in df.iterrows():
        pg, comp = r[f"{prefijo}_pg"], r["comportamiento"]
        if _na(pg) or _na(comp):
            continue
        anios = [r[f"{prefijo}_{a}"] for a in ANIOS]
        valores = [0.0 if _na(v) else float(v) for v in anios]
        msg = None
        if comp == "Incremento Acumulado":
            if not _cerca(sum(valores), pg):
                msg = f"{comp}: suma de años = {_fmt(sum(valores))} distinto de PG {_fmt(pg)}"
        elif comp in ("Incremento Flujo", "Incremento Capacidad"):
            if not _na(anios[-1]) and not _cerca(anios[-1], pg):
                msg = f"{comp}: valor 2027 = {_fmt(anios[-1])} distinto de PG {_fmt(pg)}"
        elif comp == "Mantenimiento Stock":
            malos = [a for a, v in zip(ANIOS, anios) if not _na(v) and not _cerca(v, pg)]
            if malos:
                msg = f"{comp}: años {malos} difieren del PG {_fmt(pg)}"
        if msg:
            h.append(_h(f"pg_vs_anios[{prefijo}]", "advertencia", fuente, r[llave], msg, r["fila_excel"]))
    return _como_df(h)


# ------------------------------------------------------------------ Centralizadas: presupuesto y avance
def presupuesto_invariantes(ce: pd.DataFrame) -> pd.DataFrame:
    h = []
    for _, r in ce.iterrows():
        k, f = r["codigo_actividad"], r["fila_excel"]
        defi, obl, disp = r["ppto_definitivo"], r["ppto_obligaciones"], r["ppto_disponible"]
        if any(_na(v) for v in (defi, obl, disp)):
            h.append(_h("presupuesto_incompleto", "error", "centralizadas", k, "falta definitivo, obligaciones o disponible", f))
            continue
        if min(defi, obl, disp) < 0:
            h.append(_h("presupuesto_negativo", "error", "centralizadas", k, "hay cifras presupuestales negativas", f))
        if obl > defi + 0.5:
            h.append(_h("obligaciones_mayores_definitivo", "error", "centralizadas", k,
                        f"obligaciones {_pesos(obl)} > definitivo {_pesos(defi)}", f))
        elif disp > defi - obl + 0.5:
            h.append(_h("disponible_excede_saldo", "error", "centralizadas", k,
                        f"disponible {_pesos(disp)} > definitivo − obligaciones = {_pesos(defi - obl)}", f))
    return _como_df(h)


def avance_consistente(ce: pd.DataFrame) -> pd.DataFrame:
    h = []
    for _, r in ce.iterrows():
        k, f = r["codigo_actividad"], r["fila_excel"]
        prog, ejec, pct = r["cant_programada_vigencia"], r["cant_ejecutada_vigencia"], r["avance_actividad_pct"]
        if _na(prog) or prog == 0:
            h.append(_h("sin_programacion_fisica", "info", "centralizadas", k, "sin cantidad programada en la vigencia: no hay avance físico que medir", f))
            continue
        calc = (0.0 if _na(ejec) else ejec) / prog * 100
        if not _na(pct) and abs(calc - pct) > 0.01:
            h.append(_h("avance_no_coincide", "error", "centralizadas", k,
                        f"% reportado {F.porcentaje_100(pct, 2)} distinto de ejecutada/programada = {F.porcentaje_100(calc, 2)}", f))
        if calc > 100.0001:
            h.append(_h("avance_supera_100", "advertencia", "centralizadas", k, f"avance {F.porcentaje_100(calc)} > 100 %", f))
    return _como_df(h)


def ejecucion_financiera_vs_fisica(ce: pd.DataFrame) -> pd.DataFrame:
    """Registros con obligaciones y sin avance físico. Solo cuenta si la actividad tiene cantidad programada en la
    vigencia; si la Observación lo explica (p. ej. 'el entregable es en octubre') baja a informativo."""
    h = []
    for _, r in ce.iterrows():
        k, f, obl = r["codigo_actividad"], r["fila_excel"], r["ppto_obligaciones"]
        sin_avance = _na(r["avance_actividad_pct"]) or r["avance_actividad_pct"] == 0
        programada = not _na(r["cant_programada_vigencia"]) and r["cant_programada_vigencia"] > 0
        if not _na(obl) and obl > 0 and sin_avance and programada:
            if _na(r["observacion"]):
                h.append(_h("financiero_sin_fisico", "advertencia", "centralizadas", k,
                            f"obligaciones {_pesos(obl)} sin avance físico y sin observación que lo explique", f))
            else:
                h.append(_h("financiero_sin_fisico_con_observacion", "info", "centralizadas", k,
                            f"obligaciones {_pesos(obl)} sin avance físico; la observación lo explica: "
                            f"«{str(r['observacion'])[:80]}»", f))
        con = str(r["estado_actividad"]).upper().startswith("CON")
        if not _na(obl) and ((obl > 0) != con) and not _na(r["estado_actividad"]):
            h.append(_h("estado_vs_obligaciones", "advertencia", "centralizadas", k,
                        f"estado '{r['estado_actividad']}' con obligaciones {_pesos(obl)}", f))
    return _como_df(h)


def avance_vacio_con_programacion(ce: pd.DataFrame) -> pd.DataFrame:
    """Registros con cantidad programada y % de avance vacío: en el promedio se cuentan como 0 (una alerta por meta)."""
    vacio = ce[ce["avance_actividad_pct"].isna() & (ce["cant_programada_vigencia"].fillna(0) > 0)]
    return _como_df([
        _h("avance_vacio_con_programacion", "info", "centralizadas", mp,
           f"{len(g)} de {int((ce['codigo_mp'] == mp).sum())} registro(s) tienen cantidad programada y el % de avance "
           "vacío: en el promedio de actividades se cuentan como 0 %", int(g["fila_excel"].iloc[0]))
        for mp, g in vacio.groupby("codigo_mp")])


def integridad_centralizadas(ce: pd.DataFrame) -> pd.DataFrame:
    h = []
    for proyecto, g in ce.groupby("codigo_proyecto"):
        if g["bpin"].nunique() > 1:
            h.append(_h("proyecto_con_varios_bpin", "error", "centralizadas", proyecto,
                        f"BPIN distintos: {sorted(g['bpin'].dropna().unique())}"))
    for _, r in ce.iterrows():
        if "/" not in str(r["codigo_actividad"]):
            continue          # entidades descentralizadas: la actividad se identifica con el código PPM (sin '/')
        if not str(r["codigo_actividad"]).startswith(str(r["codigo_proyecto"]) + "/"):
            h.append(_h("actividad_fuera_de_proyecto", "error", "centralizadas", r["codigo_actividad"],
                        f"no empieza por el proyecto {r['codigo_proyecto']}", r["fila_excel"]))
    return _como_df(h)


def presupuesto_vs_recursos_pi(ce: pd.DataFrame, drive_mp: pd.DataFrame, anio: int = 2026) -> pd.DataFrame:
    """Indicador (no error): el presupuesto definitivo del Plan de Acción por meta supera lo programado en el PI."""
    col = f"recurso_total_{anio}"
    por_mp = ce.groupby("codigo_mp")["ppto_definitivo"].sum()
    prog = drive_mp.set_index("codigo_mp")[col]
    h = []
    for mp, definitivo in por_mp.items():
        if mp in prog.index and not _na(prog[mp]) and prog[mp] > 0 and definitivo > prog[mp] + 0.5:
            h.append(_h("ppto_supera_recursos_pi", "advertencia", "centralizadas", mp,
                        f"definitivo {_pesos(definitivo)} > recursos {anio} del PI {_pesos(prog[mp])} "
                        f"({F.porcentaje(definitivo / prog[mp], 0)})"))
    return _como_df(h)


# ------------------------------------------------------------------ marca de logro en encabezados de Drive
def inferir_vigencia(drive: pd.DataFrame) -> int | None:
    """Vigencia en curso = primer año cuyo encabezado en Drive NO está marcado como logro ('VAL ALC').

    El técnico renombra la columna al cerrar la vigencia, así que el encabezado indica hasta dónde hay logro.
    """
    for a in ANIOS:
        col = f"valor_{a}_logro"
        if col in drive.columns and len(drive) and not bool(drive[col].iloc[0]):
            return a
    return None


def marca_logro_vs_vigencia(drive: pd.DataFrame, fuente: str, vigencia: int) -> pd.DataFrame:
    """Vigencias cerradas deben llevar 'VAL ALC' en el encabezado; las pendientes no."""
    h = []
    for a in ANIOS:
        col = f"valor_{a}_logro"
        if col not in drive.columns or drive.empty:
            continue
        marcado = bool(drive[col].iloc[0])
        if a < vigencia and not marcado:
            h.append(_h("vigencia_cerrada_sin_marca_logro", "advertencia", fuente, str(a),
                        f"La vigencia {a} ya cerró pero su encabezado no dice 'VAL ALC {a}': "
                        "¿se cargó el logro o aún está la meta?", 2))
        elif a >= vigencia and marcado:
            h.append(_h("vigencia_abierta_con_marca_logro", "advertencia", fuente, str(a),
                        f"El encabezado de {a} dice 'VAL ALC' pero la vigencia {vigencia} no ha cerrado", 2))
    return _como_df(h)


# ------------------------------------------------------------------ Z023 consolidado
def z023_calidad(z: pd.DataFrame) -> pd.DataFrame:
    """Integridad propia del Z023: llave de actividad, MP presente y bien formada, BPIN válido (por proyecto)."""
    h = [_h("llave_unica", "error", "z023", r["ppm_actividad"], "'ppm_actividad' repetido", r["fila_excel"])
         for _, r in z[z["ppm_actividad"].duplicated(keep=False)].iterrows()]
    for _, r in z[z["codigo_mp"].isna()].iterrows():
        h.append(_h("z023_sin_meta_producto", "advertencia", "z023", r["ppm_actividad"],
                    f"La actividad del proyecto {r['proyecto_ppm']} no tiene meta de producto", r["fila_excel"]))
    for _, r in z[z["codigo_mp"].notna() & ~z["codigo_mp_valido"].fillna(False).astype(bool)].iterrows():
        h.append(_h("z023_mp_formato", "advertencia", "z023", r["codigo_mp"],
                    f"No cumple MP+5+2+2+7 dígitos (actividad {r['ppm_actividad']})", r["fila_excel"]))
    # BPIN válido: empieza por 2 y tiene 12 a 16 caracteres (criterio de la macro del consolidado). Una alerta por proyecto.
    if z.empty:
        return _como_df(h)
    malos = z[~z["bpin"].fillna("").map(lambda b: b.startswith("2") and 12 <= len(b) <= 16).astype(bool)]
    for proy, g in malos.groupby("proyecto_ppm"):
        bpin = g["bpin"].dropna().iloc[0] if g["bpin"].notna().any() else "vacío"
        h.append(_h("z023_bpin_no_valido", "advertencia", "z023", proy,
                    f"BPIN '{bpin}' no válido ({len(g)} fila(s))", int(g["fila_excel"].iloc[0])))
    return _como_df(h)


def centralizadas_vs_z023(centralizadas: pd.DataFrame, z: pd.DataFrame) -> pd.DataFrame:
    """Cada actividad de Centralizadas debe existir en el Z023 y apuntar a la misma meta.

    Dependencias centrales: el código es el PS (`ps_actividad`). Entidades descentralizadas: no tienen código PS y su
    actividad se identifica con el código PPM (`ppm_actividad`); se acepta cualquiera de los dos.
    """
    mp_por_actividad = {}
    for col in ("ps_actividad", "ppm_actividad"):
        for act, g in z[z[col].notna()].groupby(col):
            mp_por_actividad.setdefault(act, set()).update(g["codigo_mp"].dropna())
    h = []
    for act, g in centralizadas.groupby("codigo_actividad"):
        if act not in mp_por_actividad:
            h.append(_h("actividad_no_esta_en_z023", "advertencia", "centralizadas", act,
                        "El código de la actividad no aparece en el Z023 consolidado (¿consolidado desactualizado?)",
                        int(g["fila_excel"].iloc[0])))
        elif mps := set(g["codigo_mp"].dropna()) - mp_por_actividad[act]:
            h.append(_h("mp_distinta_en_z023", "advertencia", "centralizadas", act,
                        f"Meta en Centralizadas {sorted(mps)} distinto de meta en el Z023 {sorted(mp_por_actividad[act])}",
                        int(g["fila_excel"].iloc[0])))
    return _como_df(h)


# ------------------------------------------------------------------ orquestador
def validar_todo(pi_mp_evaplan: pd.DataFrame | None = None, pi_mr_evaplan: pd.DataFrame | None = None,
                 centralizadas: pd.DataFrame | None = None, drive_mp: pd.DataFrame | None = None,
                 drive_mr: pd.DataFrame | None = None, vigencia: int | None = None,
                 z023: pd.DataFrame | None = None) -> pd.DataFrame:
    """Ejecuta todas las reglas aplicables según las fuentes disponibles. Devuelve un DataFrame de hallazgos.

    `vigencia`: año en curso. Si no se da, se infiere de los encabezados 'VAL ALC' de Drive.
    """
    r: list[pd.DataFrame] = []
    if vigencia is None and drive_mp is not None:
        vigencia = inferir_vigencia(drive_mp)
    if pi_mp_evaplan is not None:
        r += [llave_unica(pi_mp_evaplan, "codigo_mp", "pi_mp_evaplan"),
              codigo_mp_coherente(pi_mp_evaplan, "pi_mp_evaplan")]
        if (mr := pi_mr_evaplan if pi_mr_evaplan is not None else drive_mr) is not None:
            r.append(mr_existe(pi_mp_evaplan, mr, "pi_mp_evaplan"))
    if pi_mr_evaplan is not None:
        r.append(llave_unica(pi_mr_evaplan, "codigo_mr", "pi_mr_evaplan"))
    if drive_mr is not None and vigencia:
        r.append(marca_logro_vs_vigencia(drive_mr, "pi_drive_mr", vigencia))
    if centralizadas is not None:
        r += [llave_unica(centralizadas, "id_registro", "centralizadas"),
              codigo_mp_coherente(centralizadas, "centralizadas"), presupuesto_invariantes(centralizadas),
              avance_consistente(centralizadas), avance_vacio_con_programacion(centralizadas),
              ejecucion_financiera_vs_fisica(centralizadas),
              integridad_centralizadas(centralizadas)]
    if drive_mp is not None:
        # El libro de Drive trae TODAS las entidades: se revisan solo las de los archivos cargados (si los hay).
        entidades = set()
        for df in (pi_mp_evaplan, centralizadas):
            if df is not None and "codigo_entidad" in df.columns:
                entidades |= set(df["codigo_entidad"].dropna())
        propio = drive_mp[drive_mp["entidad_codigo"].isin(entidades)] if entidades else drive_mp
        r += [llave_unica(propio, "codigo_mp", "pi_drive_mp"), codigo_mp_coherente(propio, "pi_drive_mp"),
              pg_vs_anios(propio, "pi_drive_mp", prefijo="pi")]
        if vigencia:
            r.append(marca_logro_vs_vigencia(drive_mp, "pi_drive_mp", vigencia))
        if pi_mp_evaplan is not None:
            r += [cobertura_evaplan_vs_drive(pi_mp_evaplan, drive_mp),
                  valores_evaplan_vs_drive(pi_mp_evaplan, drive_mp)]
        if centralizadas is not None:
            r.append(presupuesto_vs_recursos_pi(centralizadas, drive_mp, anio=vigencia or 2026))
    if z023 is not None:
        # Igual que Drive: el Z023 trae TODAS las entidades; se revisan las de los archivos cargados (si los hay).
        entidades = set()
        for df in (pi_mp_evaplan, centralizadas):
            if df is not None and "codigo_entidad" in df.columns:
                entidades |= set(df["codigo_entidad"].dropna())
        # Las descentralizadas tienen otro código en el Z023 (ver aportes.equivalencias_z023).
        equivalentes = set(equivalencias_z023(entidades_de(pi_mp_evaplan, centralizadas), z023).values())
        propio = z023[z023["dependencia"].isin(entidades | equivalentes)] if entidades else z023
        r.append(z023_calidad(propio))
        if centralizadas is not None:
            r.append(centralizadas_vs_z023(centralizadas, z023))
    if centralizadas is not None and (pi := pi_mp_evaplan if pi_mp_evaplan is not None else drive_mp) is not None:
        r.append(cobertura_centralizadas_vs_pi(centralizadas, pi))
    r = [x for x in r if len(x)]
    if not r:
        return _como_df([])
    orden = {"error": 0, "advertencia": 1, "info": 2}
    out = pd.concat(r, ignore_index=True)
    return out.sort_values(["severidad", "fuente", "regla"], key=lambda s: s.map(orden).fillna(9) if s.name == "severidad" else s,
                           kind="stable").reset_index(drop=True)
