"""Lectores tipados: convierten los Excel de EVAPLAN y del libro de Drive en DataFrames limpios.

Todos devuelven nombres de columna canónicos (ver esquemas.py), tipos consistentes y la columna
`fila_excel` (número de fila en el archivo original) para poder señalar el origen de cada hallazgo.

`origen` puede ser una ruta, una URL de exportación xlsx, o un archivo en memoria
(p. ej. el objeto de `st.file_uploader`).
"""
from __future__ import annotations

import pandas as pd

from . import limpieza as lz
from .esquemas import (
    CENTRALIZADAS,
    PI_DRIVE_MP,
    PI_DRIVE_MR,
    PI_MP_EVAPLAN,
    PI_MR_EVAPLAN,
    Campo,
    Esquema,
)


class EsquemaError(ValueError):
    """El archivo no tiene la estructura que describe el diccionario de datos."""


def _clave(texto: str) -> str:
    return lz.sin_tildes(texto).lower()


def _coincide(campo: Campo, encabezado: str) -> bool:
    esperado, real = _clave(campo.origen), _clave(encabezado)
    return real.startswith(esperado) if campo.prefijo else real == esperado


def _resolver_columnas(esquema: Esquema, encabezados: list[str]) -> dict[str, int]:
    """Mapea cada campo a su índice de columna, o lanza EsquemaError con TODOS los problemas."""
    indices, problemas = {}, []
    for c in esquema.campos:
        if c.pos is not None:
            if c.pos >= len(encabezados):
                problemas.append(f"'{c.origen}': se esperaba en la columna {c.pos + 1}, pero el archivo es más corto")
            elif not _coincide(c, encabezados[c.pos]):
                problemas.append(
                    f"columna {c.pos + 1}: se esperaba '{c.origen}' y llegó '{encabezados[c.pos]}'"
                )
            else:
                indices[c.canonico] = c.pos
        else:
            candidatos = [i for i, h in enumerate(encabezados) if _coincide(c, h)]
            if not candidatos:
                if not c.nulo:
                    problemas.append(f"falta la columna '{c.origen}'")
            elif len(candidatos) > 1:
                problemas.append(f"el encabezado '{c.origen}' está repetido (columnas {[i + 1 for i in candidatos]})")
            else:
                indices[c.canonico] = candidatos[0]
    if problemas:
        raise EsquemaError(
            f"El archivo no coincide con '{esquema.titulo}':\n  - " + "\n  - ".join(problemas)
        )
    return indices


def _serie(campo: Campo, valores: pd.Series) -> dict[str, pd.Series]:
    """Convierte una columna cruda según su tipo. Devuelve {nombre_columna: serie}."""
    n, t = campo.canonico, campo.tipo
    if t == "texto":
        return {n: valores.map(lz.texto).astype("string")}
    if t == "codigo":
        s = valores.map(lz.codigo)
        if n == "codigo_mr":
            s = s.map(lz.codigo_mr)
        return {n: s.astype("string")}
    if t == "entero":
        return {n: valores.map(lz.entero).astype("Int64")}
    if t in ("decimal", "moneda"):
        f = lz.moneda if t == "moneda" else lz.decimal
        return {n: valores.map(f).astype("Float64")}
    if t == "valor_np":
        pares = valores.map(lz.valor_np)
        return {
            n: pares.map(lambda p: p[0]).astype("Float64"),
            f"{n}_np": pares.map(lambda p: p[1]).astype("boolean"),
        }
    if t == "si_no":
        return {n: valores.map(lz.si_no).astype("boolean")}
    if t == "fecha":
        return {n: pd.to_datetime(valores.map(lz.fecha), errors="coerce")}
    if t == "codigo_nombre":
        pares = valores.map(lz.dividir_codigo_nombre)
        return {
            f"{n}_codigo": pares.map(lambda p: p[0]).astype("string"),
            f"{n}_nombre": pares.map(lambda p: p[1]).astype("string"),
        }
    raise ValueError(f"Tipo desconocido '{t}' en el campo '{n}'")


def leer(origen, esquema: Esquema) -> pd.DataFrame:
    """Lee `origen` según `esquema` y devuelve un DataFrame tipado."""
    columnas = (max(c.pos for c in esquema.campos if c.pos is not None) + 1) if esquema.usa_posiciones else None
    try:
        crudo = pd.read_excel(
            origen, sheet_name=esquema.hoja, header=None, dtype=object,
            usecols=range(columnas) if columnas else None, engine="openpyxl",
        )
    except ValueError as e:  # hoja inexistente, etc.
        raise EsquemaError(f"No se pudo abrir '{esquema.titulo}' (hoja '{esquema.hoja}'): {e}") from e

    if len(crudo) <= esquema.fila_encabezado:
        raise EsquemaError(f"El archivo no tiene encabezados en la fila {esquema.fila_encabezado + 1}")
    encabezados = [lz.normalizar_encabezado(h) for h in crudo.iloc[esquema.fila_encabezado]]
    indices = _resolver_columnas(esquema, encabezados)

    datos = crudo.iloc[esquema.fila_encabezado + 1:]
    salida: dict[str, pd.Series] = {}
    for campo in esquema.campos:
        if campo.canonico in indices:
            salida.update(_serie(campo, datos.iloc[:, indices[campo.canonico]]))
        else:  # columna opcional ausente
            salida.update(_serie(campo, pd.Series([None] * len(datos), index=datos.index, dtype=object)))
    df = pd.DataFrame(salida)
    df.insert(0, "fila_excel", datos.index + 1)

    if "comportamiento" in df.columns:
        df["comportamiento"] = df["comportamiento"].map(lz.normalizar_comportamiento).astype("string")

    # Filas vacías (p. ej. al final del libro de Drive): sin ningún valor en las llaves.
    llaves = [c for c in esquema.llave if c in df.columns]
    df = df[df[llaves].notna().any(axis=1)].reset_index(drop=True)
    df.attrs["esquema"] = esquema.nombre
    return df


def enriquecer_codigo_mp(df: pd.DataFrame, columna: str = "codigo_mp") -> pd.DataFrame:
    """Agrega las partes del código MP: mr_del_mp, programa_mp, subprograma_mp, consecutivo_mp, producto_mga_mp."""
    partes = df[columna].map(lz.descomponer_codigo_mp)
    df = df.copy()
    df["codigo_mp_valido"] = partes.map(lambda p: p is not None).astype("boolean")
    for clave, nombre in [("mr", "mr_del_mp"), ("programa", "programa_mp"), ("subprograma", "subprograma_mp"),
                          ("consecutivo", "consecutivo_mp"), ("producto_mga", "producto_mga_mp")]:
        df[nombre] = partes.map(lambda p, k=clave: p[k] if p else pd.NA).astype("string")
    return df


# ------------------------------------------------------------------ API pública
def leer_pi_mp_evaplan(origen) -> pd.DataFrame:
    return enriquecer_codigo_mp(leer(origen, PI_MP_EVAPLAN))


def leer_pi_mr_evaplan(origen) -> pd.DataFrame:
    return leer(origen, PI_MR_EVAPLAN)


def leer_centralizadas(origen) -> pd.DataFrame:
    return enriquecer_codigo_mp(leer(origen, CENTRALIZADAS))


def leer_pi_drive_mp(origen) -> pd.DataFrame:
    return enriquecer_codigo_mp(leer(origen, PI_DRIVE_MP))


def leer_pi_drive_mr(origen) -> pd.DataFrame:
    return leer(origen, PI_DRIVE_MR)
