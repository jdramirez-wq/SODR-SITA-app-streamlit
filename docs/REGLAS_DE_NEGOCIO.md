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

## Seguimiento por meta (matriz de la página)
Se calculan **hechos**, sin umbrales: no existe un cronograma único de ejecución, así que no se inventan semáforos.
| Id | Hecho / incoherencia | Estado | Severidad | Hallazgo |
|---|---|---|---|---|
| S1 | Vigencia en curso = primer año del Plan Indicativo sin `VAL ALC` en el encabezado | ✅ | — | `inferir_vigencia` |
| S2 | `% avance vs meta vigencia = Resultado / meta de la vigencia` (meta > 0) | ✅ | — | columna |
| S3 | Acumulado/Capacidad: `avance cuatrienio = Σ logros de vigencias cerradas + Resultado`; `% vs PG` | ✅ ❓1 | — | columnas |
| S4 | `% ejecución financiera = Σ obligaciones / Σ definitivo` de las actividades de la meta | ✅ | — | columna |
| S5 | Avance de actividades: promedio global **y por proyecto de inversión** (el prompt lo exige por proyecto) | ✅ | — | `avance_por_proyecto` |
| S6 | Meta del Plan Indicativo sin reporte en EVAPLAN | ✅ ❓ | advertencia | `sin_reporte` |
| S7 | Avance (Resultado > 0) con obligaciones = 0 y sin mencionar gestión/donación/cofinanciación/sin costo | ✅ | advertencia | `avance_sin_ejecucion_financiera` |
| S8 | Lo mismo pero la narrativa sí menciona gestión (verificar soporte) | ✅ | info | `avance_sin_ejecucion_con_gestion` |
| S9 | Obligaciones > 0, Resultado = 0 y sin explicación en Dificultades | ✅ | advertencia | `ejecucion_sin_avance_sin_explicacion` |
| S10 | Actividades con obligaciones y sin avance físico (crítico en actividades) | ✅ | advertencia | `actividades_con_obligaciones_sin_avance` |
| S11 | Avance sin Principal Logro/Análisis; resultado 0 con logro/análisis | ✅ | advertencia / info | `resultado_sin_narrativa`, `narrativa_con_resultado_cero` |
| S12 | Reporte con avance pero sin meta programada (NP o 0); resultado supera la meta | ✅ | advertencia / info | `reporte_sin_meta_programada`, `resultado_supera_meta_vigencia` |
| S12b | Proyección de cierre de la dependencia (`Valor Proyectado`) por debajo de la meta de la vigencia; o menor que el resultado ya acumulado en metas acumulativas | ✅ | advertencia | `proyeccion_bajo_meta`, `proyeccion_menor_que_resultado` |
| S13 | Meta sin actividades en Centralizadas | — | info | `sin_plan_de_accion` |
| S14 | Encabezado del año cerrado sin `VAL ALC` (o abierto con `VAL ALC`) en Drive | ✅ | advertencia | `vigencia_*_marca_logro` |

*Lo que se deja al LLM/analista:* si el avance es "suficiente", la gravedad de cada alerta, la desconexión
jerárquica (se entrega la brecha numérica `meta vs actividades`, no un veredicto), la calidad narrativa y el dictamen.

## Pendiente de definir (requiere al equipo)
- Tratamiento de `Reducción Anual` (metas de resultado) y de metas reprogramadas dentro del cuatrienio.
- Metas de resultado: fuera de alcance por ahora (solo metas de producto).
- Semáforos: **descartados por ahora** (no hay umbrales únicos); se retomarán si el equipo define un cronograma.
