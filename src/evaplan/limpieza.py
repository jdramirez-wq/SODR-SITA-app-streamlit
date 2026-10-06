"""Funciones puras de limpieza de celdas. Sin dependencias de Streamlit."""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

# Valores que los sistemas fuente usan como "vacío" en columnas de texto.
MARCADORES_VACIO = {"", ".", "-", "nan", "none", "null", "n/a", "na",
                    "#error!", "#n/a", "#ref!", "#value!", "#div/0!", "#name?"}   # errores de fórmula de Excel
# Valores que significan "sin dato" en columnas numéricas (distintos de 'NP').
MARCADORES_SIN_DATO_NUM = {"no disponible", "n/d", "nd", "error", "#n/a", "#div/0!", "#ref!", "#value!"}

_RE_MP = re.compile(r"^MP(\d{5})(\d{2})(\d{2})(\d{7})$")


def normalizar_encabezado(valor) -> str:
    """'2026.0' -> '2026'; 'VAL ALC 2024\\n' -> 'VAL ALC 2024'; colapsa espacios."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return " ".join(str(valor).split())


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def texto(valor):
    """Texto limpio o pd.NA. Convierte marcadores de vacío ('.', 'nan', '') en NA."""
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return pd.NA
    s = " ".join(str(valor).split())
    return pd.NA if s.lower() in MARCADORES_VACIO else s


def codigo(valor):
    """Identificador como texto. Evita '2024009990001.0' y notación científica."""
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return pd.NA
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    s = str(valor).strip()
    return pd.NA if s.lower() in MARCADORES_VACIO else s


def _numero(valor, punto_es_miles: bool):
    if valor is None or isinstance(valor, bool):
        return pd.NA
    if isinstance(valor, (int, float)):
        return pd.NA if pd.isna(valor) else float(valor)
    s = str(valor).strip().replace("$", "").replace(" ", "")
    if s.lower() in MARCADORES_VACIO | MARCADORES_SIN_DATO_NUM or s.upper() == "NP":
        return pd.NA
    s = s.replace("%", "")
    if "," in s and "." in s:          # 1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif punto_es_miles and re.fullmatch(r"-?\d{1,3}(,\d{3}){2,}", s):   # 3,200,000 (miles con coma, p. ej. Z023)
        s = s.replace(",", "")
    elif "," in s:                      # 1234,56
        s = s.replace(",", ".")
    elif punto_es_miles and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):   # 1.234.567 (solo dinero)
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return pd.NA


def decimal(valor):
    """float o NA para indicadores. El punto es separador DECIMAL: '41.667' -> 41.667; '1.500,00' -> 1500.0.

    'NO DISPONIBLE', 'ERROR', 'NP', '.' y vacíos -> NA.
    """
    return _numero(valor, punto_es_miles=False)


def moneda(valor):
    """Pesos como float. El punto es separador de MILES: '2.339.400.000' -> 2339400000.0 (como llega de EVAPLAN)."""
    return _numero(valor, punto_es_miles=True)


def entero(valor):
    """Entero (Int64) o NA. '2020-2023' (rango de años) -> NA."""
    d = decimal(valor)
    if d is pd.NA or pd.isna(d):
        return pd.NA
    return int(round(d))


def valor_np(valor):
    """Devuelve (valor_float_o_NA, es_no_programado). 'NP' = No Programado (no es cero)."""
    if isinstance(valor, str) and valor.strip().upper() == "NP":
        return pd.NA, True
    return decimal(valor), False


def si_no(valor):
    s = texto(valor)
    if s is pd.NA:
        return pd.NA
    s = sin_tildes(str(s)).lower()
    if s in {"si", "s", "true", "1"}:
        return True
    if s in {"no", "n", "false", "0"}:
        return False
    return pd.NA


def fecha(valor):
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return pd.NaT
    return pd.to_datetime(valor, errors="coerce")


def dividir_codigo_nombre(valor):
    """'9999 - SECRETARÍA X' -> ('9999', 'SECRETARÍA X').

    Corrige el duplicado del libro de Drive: '99001 - 99001-ALCANZAR ...' -> ('99001', 'ALCANZAR ...').
    """
    s = texto(valor)
    if s is pd.NA:
        return pd.NA, pd.NA
    cod, sep, nombre = str(s).partition(" - ")
    if not sep:
        return str(s), pd.NA
    cod, nombre = cod.strip(), nombre.strip()
    for prefijo in (f"{cod}-", f"{cod} -"):
        if nombre.startswith(prefijo):
            nombre = nombre[len(prefijo):].strip()
    return cod, nombre or pd.NA


def codigo_mr(valor):
    """'MR99001' -> '99001'; '99001' -> '99001'."""
    s = codigo(valor)
    if s is pd.NA:
        return pd.NA
    return re.sub(r"^MR", "", str(s), flags=re.IGNORECASE)


def descomponer_codigo_mp(mp):
    """MP + [5 dígitos MR][2 subprograma][2 consecutivo][7 producto MGA] -> dict o None si no cumple.

    Ejemplo: 'MP9900204099902101' -> mr='99002', programa='99', subprograma='04',
             consecutivo='09', producto_mga='9902101'.
    """
    if mp is None or mp is pd.NA or (not isinstance(mp, str) and pd.isna(mp)):
        return None
    m = _RE_MP.match(str(mp).strip())
    if not m:
        return None
    mr, sub, cons, prod = m.groups()
    return {"mr": mr, "programa": mr[:2], "subprograma": sub, "consecutivo": cons, "producto_mga": prod}


def normalizar_comportamiento(valor):
    """Unifica mayúsculas: 'Incremento flujo' -> 'Incremento Flujo'."""
    s = texto(valor)
    return s if s is pd.NA else " ".join(w.capitalize() for w in str(s).split())
