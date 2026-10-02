# Plataforma de Gestión SODR — Seguimiento al Plan de Desarrollo Departamental

Herramienta en Streamlit para cruzar, auditar y reportar información del seguimiento al Plan de
Desarrollo Departamental (Plan Indicativo, Plan de Acción, proyectos, MGA, POAI).

> ⚠️ Repositorio **público**: no subir datos reales ni credenciales. Ver [`data/README.md`](data/README.md).

## Módulos
| Módulo | Archivo | Estado |
|---|---|---|
| Auditoría EVAPLAN | `pages/1_Auditoria_EVAPLAN.py` | Operativo |
| POAI 2027 (control previo) | `pages/2_POAI_2027.py` | En desarrollo |

## Ejecutar en local
```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

## Documentación
- [Cómo trabajamos (Git, ramas, Claude)](docs/FLUJO_DE_TRABAJO.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Fuentes de datos](docs/FUENTES_DE_DATOS.md)
- [Hoja de ruta](docs/HOJA_DE_RUTA.md)
- [Contexto para Claude](CLAUDE.md)
