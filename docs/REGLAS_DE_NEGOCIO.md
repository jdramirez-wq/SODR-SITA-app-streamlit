# Reglas de negocio y de integridad

Las reglas viven en `src/evaplan/validaciones.py` y se prueban con los ejemplos de `data/ejemplos/`
(`tests/test_validaciones.py`). **Una regla "por confirmar" nunca se reporta como error.**

## Identificación (llaves)
| Id | Regla | Estado | Severidad | Función |
|---|---|---|---|---|
| L1 | El código MP tiene 18 caracteres: `MP`+MR(5)+subprograma(2)+consecutivo(2)+producto MGA(7) | ✅ | error | `codigo_mp_coherente` |
| L2 | Programa, subprograma y producto MGA de la fila coinciden con los del código MP | ✅ | error | `codigo_mp_coherente` |
| L3 | La llave de cada tabla es única (`codigo_mp`, `codigo_mr`, `codigo_actividad`) | ✅ | error | `llave_unica` |
| L4 | Un proyecto tiene un único BPIN; el código de actividad empieza por el del proyecto | ✅ | error | `integridad_centralizadas` |
| L5 | Toda MP cuelga de una MR existente (dígitos 3-7 del código MP) | ✅ | error | `mr_existe` |
| L6 | La entidad se identifica por su **código**, nunca por el nombre | ✅ | — | (convención) |

## Cobertura entre fuentes
| Id | Regla | Estado | Severidad | Función |
|---|---|---|---|---|
| C1 | Toda meta del export de EVAPLAN existe en el Plan Indicativo de Drive | ✅ | error | `cobertura_evaplan_vs_drive` |
| C2 | Toda meta de Drive de las entidades del export aparece en el export | ✅ | advertencia | `cobertura_evaplan_vs_drive` |
| C3 | Toda actividad de Centralizadas apunta a una meta existente en el PI | ✅ | error | `cobertura_centralizadas_vs_pi` |
| C4 | Metas del PI sin actividades en Centralizadas | — | info | `cobertura_centralizadas_vs_pi` |
| C5 | PG y valores 2024-2027 (con `NP`) del export = bloque vigente de Drive | ✅ | advertencia | `valores_evaplan_vs_drive` |

## Indicadores
| Id | Regla | Estado | Severidad | Función |
|---|---|---|---|---|
| I1 | Acumulado: PG = suma de años. Flujo: PG = valor 2027. Mantenimiento: todos los años = PG | ❓ | advertencia | `pg_vs_anios` |
| I2 | Se aplica solo a la **programación** (bloque original); nunca al bloque vigente (trae logros) | ✅ | — | `validar_todo` |
| I3 | `NP` (No Programado) no es 0: se conserva como marca aparte | ✅ | — | `limpieza.valor_np` |

## Presupuesto y avance (Centralizadas)
| Id | Regla | Estado | Severidad | Función |
|---|---|---|---|---|
| P1 | Obligaciones ≤ presupuesto definitivo; sin cifras negativas | ✅ | error | `presupuesto_invariantes` |
| P2 | Disponible ≤ definitivo − obligaciones | ✅ | error | `presupuesto_invariantes` |
| P3 | `% avance = ejecutada / programada × 100` (ejecutada vacía = 0) | ✅ | error | `avance_consistente` |
| P4 | Avance físico superior a 100 % | — | advertencia | `avance_consistente` |
| P5 | Obligaciones > 0 sin avance físico reportado | ✅ | advertencia | `ejecucion_financiera_vs_fisica` |
| P6 | `CON EJECUCION` ⇔ obligaciones > 0 | ✅ | advertencia | `ejecucion_financiera_vs_fisica` |
| P7 | Presupuesto definitivo de la meta > recursos de la vigencia programados en el PI | ❓ | advertencia | `presupuesto_vs_recursos_pi` |

## Pendiente de definir (requiere al equipo)
- **Cumplimiento por periodo:** cómo se compara `Resultado` con lo programado según el comportamiento y el
  corte (trimestre, semestre…). Es el cálculo central del seguimiento y aún no se ha implementado.
- Semáforos / umbrales de alerta (¿qué % es "en riesgo"?).
- Tratamiento de metas reprogramadas y de `Reducción Anual`.
