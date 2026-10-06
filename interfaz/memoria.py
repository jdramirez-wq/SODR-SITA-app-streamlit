"""Memoria de la sesión: que recargar la página (F5) no borre los resultados.

Streamlit guarda el estado (`st.session_state`) mientras la pestaña está abierta; al recargar, el navegador abre una
sesión nueva y todo se pierde. Para evitarlo, lo importante se copia en la memoria del servidor bajo una clave
aleatoria que viaja en la dirección de la página (`?sesion=...`). Al recargar, la dirección conserva la clave y se
recupera lo guardado.

Decisiones (el repositorio es público y los datos no lo son):
- Solo memoria del servidor: nada se escribe en disco ni sale del servidor. Si la app se reinicia, se pierde.
- Vence a las DURACION horas sin uso, y el botón "Borrar resultados" lo elimina de inmediato.
- La clave es aleatoria e imposible de adivinar, pero quien reciba la dirección completa con `?sesion=` verá los
  mismos resultados mientras no venzan: para compartir la app, se comparte la dirección sin esa parte.
"""
from __future__ import annotations

import secrets
import threading
import time

import streamlit as st

PARAMETRO = "sesion"
DURACION = 8 * 3600        # segundos sin uso antes de olvidar (una jornada de trabajo)
MAXIMO = 20                # sesiones guardadas a la vez; al superarlo se olvida la menos usada
_CLAVE = "_memoria_clave"


@st.cache_resource
def _almacen() -> dict:
    """Un solo almacén por servidor, compartido por todas las sesiones (cada una con su clave)."""
    return {"candado": threading.Lock(), "datos": {}}


def _vigentes(datos: dict, ahora: float) -> None:
    for clave in [c for c, v in datos.items() if ahora - v["usado"] > DURACION]:
        del datos[clave]
    while len(datos) > MAXIMO:
        del datos[min(datos, key=lambda c: datos[c]["usado"])]


def recuperar(claves: list[str]) -> list[str] | None:
    """Al iniciar la página: devuelve a `st.session_state` lo guardado que falte (tras recargar o volver a la página).

    Retorna las claves recuperadas (lista vacía si no faltaba nada o no había nada guardado) o None si la dirección
    trae una clave que ya no existe (pasó el plazo o la app se reinició).
    """
    a = _almacen()
    clave = st.session_state.get(_CLAVE) or st.query_params.get(PARAMETRO)
    if not clave:
        return []
    with a["candado"]:
        _vigentes(a["datos"], time.time())
        guardado = a["datos"].get(clave)
        if guardado:
            guardado["usado"] = time.time()
    if not guardado:
        st.session_state.pop(_CLAVE, None)
        st.query_params.pop(PARAMETRO, None)
        return None
    st.session_state[_CLAVE] = clave
    st.query_params[PARAMETRO] = clave             # al navegar entre páginas la dirección pierde la clave
    faltantes = [k for k in claves if k not in st.session_state and k in guardado["valores"]]
    for k in faltantes:
        st.session_state[k] = guardado["valores"][k]
    return faltantes


def conservar_en_direccion() -> None:
    """Vuelve a poner la clave en la dirección (al cambiar de página Streamlit la quita), para que F5 funcione en
    cualquier página y al volver a Seguimiento se recupere lo guardado."""
    clave = st.session_state.get(_CLAVE)
    if not clave:                                   # recién recargada (F5) en otra página: adoptar la de la dirección
        clave = st.query_params.get(PARAMETRO)
        a = _almacen()
        with a["candado"]:
            if clave not in a["datos"]:
                return
        st.session_state[_CLAVE] = clave
    if st.query_params.get(PARAMETRO) != clave:
        st.query_params[PARAMETRO] = clave


def guardar(claves: list[str]) -> None:
    """Copia en la memoria del servidor el valor actual de `claves` (crea la clave de la sesión si no existe)."""
    a = _almacen()
    clave = st.session_state.get(_CLAVE) or secrets.token_urlsafe(16)
    st.session_state[_CLAVE] = clave
    if st.query_params.get(PARAMETRO) != clave:
        st.query_params[PARAMETRO] = clave
    valores = {k: st.session_state[k] for k in claves if k in st.session_state}
    with a["candado"]:
        a["datos"][clave] = {"usado": time.time(), "valores": valores}
        _vigentes(a["datos"], time.time())


def olvidar(claves: list[str]) -> None:
    """Borra lo guardado de esta sesión (servidor, estado y dirección)."""
    a = _almacen()
    clave = st.session_state.pop(_CLAVE, None)
    if clave:
        with a["candado"]:
            a["datos"].pop(clave, None)
    for k in claves:
        st.session_state.pop(k, None)
    st.query_params.pop(PARAMETRO, None)
