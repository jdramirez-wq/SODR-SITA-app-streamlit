"""Genera docs/DICCIONARIO_DE_DATOS.md a partir de src/evaplan/esquemas.py.

Uso:  python scripts/generar_diccionario.py            # escribe el archivo
      python scripts/generar_diccionario.py --check    # falla si el archivo está desactualizado (lo usa el CI)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.evaplan.esquemas import ESQUEMAS, TIPOS, VOCABULARIOS  # noqa: E402

DESTINO = RAIZ / "docs" / "DICCIONARIO_DE_DATOS.md"


def _celda(texto: str) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def generar() -> str:
    L: list[str] = [
        "# Diccionario de datos",
        "",
        "> **Archivo generado** por `scripts/generar_diccionario.py` desde `src/evaplan/esquemas.py`. "
        "No editar a mano: cambia el esquema y vuelve a generarlo.",
        "",
        "Cada fuente se lee con un lector tipado (`src/evaplan/lectura.py`) que devuelve nombres canónicos, "
        "tipos consistentes y la columna `fila_excel` (fila en el archivo original).",
        "",
        "## Tipos lógicos",
        "",
        "| Tipo | Significado |",
        "|---|---|",
        *[f"| `{k}` | {_celda(v)} |" for k, v in TIPOS.items()],
        "",
    ]
    for e in ESQUEMAS.values():
        L += [f"## {e.titulo}", "", e.descripcion, "",
              f"- **Origen:** {e.origen_datos}",
              f"- **Hoja:** {'primera hoja' if e.hoja == 0 else f'`{e.hoja}`'} · **Encabezados en la fila:** {e.fila_encabezado + 1}",
              f"- **Llave:** {', '.join(f'`{k}`' for k in e.llave)}",
              f"- **Lector:** `leer_{e.nombre}()`", ""]
        for n in e.notas:
            L.append(f"> {n}")
        if e.notas:
            L.append("")
        usa_pos = e.usa_posiciones
        L += [f"| {'Col.' if usa_pos else '#'} | Encabezado original | Campo canónico | Tipo | ¿Vacío? | Descripción | Notas |",
              "|---|---|---|---|---|---|---|"]
        for i, c in enumerate(e.campos, start=1):
            pos = c.pos + 1 if c.pos is not None else "—"
            tipo = c.tipo if c.tipo not in ("valor_np", "codigo_nombre") else f"{c.tipo} (2 columnas)"
            origen = c.origen + ("…" if c.prefijo else "")
            L.append(f"| {pos if usa_pos else i} | `{_celda(origen)}` | `{c.canonico}` | {tipo} | "
                     f"{'sí' if c.nulo else 'no'} | {_celda(c.descripcion)} | {_celda(c.notas)} |")
        L.append("")
    L += ["## Vocabularios controlados", "",
          "Valores esperados en columnas categóricas. Un valor fuera de la lista debe revisarse, no ignorarse.", ""]
    for nombre, vocab in VOCABULARIOS.items():
        L += [f"### {nombre}", "", "| Valor | Significado |", "|---|---|",
              *[f"| `{k}` | {_celda(v) or '—'} |" for k, v in vocab.items()], ""]
    return "\n".join(L).rstrip() + "\n"


if __name__ == "__main__":
    contenido = generar()
    if "--check" in sys.argv:
        if not DESTINO.exists() or DESTINO.read_text(encoding="utf-8") != contenido:
            sys.exit("docs/DICCIONARIO_DE_DATOS.md está desactualizado: ejecuta scripts/generar_diccionario.py")
        print("Diccionario al día")
    else:
        DESTINO.write_text(contenido, encoding="utf-8")
        print(f"Escrito {DESTINO}")
