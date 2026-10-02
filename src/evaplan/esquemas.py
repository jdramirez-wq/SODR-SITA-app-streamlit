"""Diccionario de datos: una definición por columna de cada fuente.

Este módulo es la ÚNICA fuente de verdad. De aquí salen los lectores (lectura.py) y la
documentación (docs/DICCIONARIO_DE_DATOS.md, vía scripts/generar_diccionario.py).

Tipos lógicos (ver TIPOS):
    texto, codigo, entero, decimal, moneda, valor_np, si_no, fecha, codigo_nombre
"""
from __future__ import annotations

from dataclasses import dataclass, field

TIPOS = {
    "texto": "Texto libre. Los marcadores de vacío ('.', 'nan', '') se convierten en nulo.",
    "codigo": "Identificador guardado como texto (nunca como número: evita '2024009990001.0').",
    "entero": "Número entero (Int64). Valores no numéricos (p. ej. '2020-2023') pasan a nulo.",
    "decimal": "Número real. Acepta formato es-CO ('1.500,00'). 'NO DISPONIBLE', 'ERROR' pasan a nulo.",
    "moneda": "Pesos colombianos como número real. Acepta '2.339.400.000' (texto) y 0 (entero).",
    "valor_np": "Número o 'NP' (No Programado). Genera dos columnas: <campo> y <campo>_np (booleano).",
    "si_no": "Booleano a partir de 'Sí'/'No'.",
    "fecha": "Fecha (datetime). Inválidas pasan a NaT.",
    "codigo_nombre": "Celda 'COD - NOMBRE'. Genera <campo>_codigo y <campo>_nombre.",
}


@dataclass(frozen=True)
class Campo:
    canonico: str               # nombre estándar (snake_case) usado en todo el código
    origen: str                 # encabezado normalizado tal como viene en el archivo
    tipo: str                   # clave de TIPOS
    descripcion: str
    nulo: bool = False          # ¿se permiten vacíos?
    pos: int | None = None      # posición de columna (0-based) cuando hay encabezados repetidos
    prefijo: bool = False       # el encabezado cambia (p. ej. lleva fecha de corte): comparar por prefijo
    alternativas: tuple[str, ...] = ()   # otros encabezados válidos para el mismo campo
    marca_logro: str = ""       # si el encabezado empieza así, el valor es LOGRO (genera <campo>_logro)
    notas: str = ""


@dataclass(frozen=True)
class Esquema:
    nombre: str
    titulo: str
    descripcion: str
    origen_datos: str
    fila_encabezado: int        # 0-based, fila donde están los nombres de columna
    llave: tuple[str, ...]      # columnas canónicas que identifican una fila
    campos: tuple[Campo, ...]
    hoja: str | int = 0
    notas: tuple[str, ...] = field(default_factory=tuple)

    def por_canonico(self, nombre: str) -> Campo:
        return next(c for c in self.campos if c.canonico == nombre)

    @property
    def usa_posiciones(self) -> bool:
        return any(c.pos is not None for c in self.campos)


# ---------------------------------------------------------------- Vocabularios controlados
COMPORTAMIENTOS = {
    "Incremento Acumulado": "El PG es la SUMA de las metas anuales.",
    "Incremento Capacidad": "Observado: el PG es la SUMA de las metas anuales (por confirmar).",
    "Incremento Flujo": "El PG es el valor del ÚLTIMO año (2027); cada año se mide por separado.",
    "Mantenimiento Stock": "Se mantiene un nivel: todos los años igualan al PG.",
    "Reducción Anual": "Solo en Metas de Resultado: el indicador debe bajar (por confirmar regla del PG).",
}
ESTADO_ACTIVIDAD = {"CON EJECUCION": "Tiene obligaciones (> 0).", "SIN EJECUCION": "Sin obligaciones."}
ESTADO_META_PRODUCTO = {"EN EJECUCIÓN": "Meta vigente.", "CUMPLIDA": "Meta de producto ya cumplida."}
VERIFICACION_COMPORTAMIENTO = {
    "ACUMULADO": "", "FLUJO": "", "MANTENIMIENTO": "", "CAPACIDAD": "", "REDUCCIÓN": "",
    "ERROR": "La fórmula de verificación del libro falló (revisar la fila en Drive).",
}
VOCABULARIOS = {
    "Comportamiento del indicador": COMPORTAMIENTOS,
    "Estado de la actividad (Centralizadas)": ESTADO_ACTIVIDAD,
    "Estado de la meta de producto (Drive)": ESTADO_META_PRODUCTO,
    "Verificación del comportamiento (Drive)": VERIFICACION_COMPORTAMIENTO,
}

_ANIOS = (2024, 2025, 2026, 2027)

_NOTA_VALORES = (
    "Valor por vigencia. Vigencia cerrada: LOGRO alcanzado (el técnico renombra el encabezado a 'VAL ALC AAAA' "
    "en Drive, columnas AK:AN). Vigencia pendiente: META, que se modifica si se reprograma. ✅ Confirmado."
)


def _valores_evaplan() -> tuple[Campo, ...]:
    pg = Campo("valor_pg", "PG", "valor_np", "Meta del cuatrienio (Programación de Gobierno) vigente.",
               notas="Reprogramada; puede diferir de 'pi_pg' (PI original).")
    anios = tuple(
        Campo(f"valor_{a}", str(a), "valor_np", f"Valor de la vigencia {a}.", notas=_NOTA_VALORES)
        for a in _ANIOS
    )
    return (pg, *anios)


def _valores_drive(pos_2024: int, marcados: tuple[int, ...]) -> tuple[Campo, ...]:
    """Cuatro columnas anuales consecutivas del bloque vigente de Drive.

    El encabezado cambia con el tiempo: al cerrar una vigencia el técnico lo renombra de '2026' a 'VAL ALC 2026'.
    Se aceptan ambas formas y se registra cuál llegó (<campo>_logro). `marcados` solo fija el nombre 'principal'.
    """
    campos = []
    for i, anio in enumerate(_ANIOS):
        marcado, simple = f"VAL ALC {anio}", str(anio)
        origen, alt = (marcado, (simple,)) if anio in marcados else (simple, (marcado,))
        campos.append(Campo(
            f"valor_{anio}", origen, "valor_np",
            f"Valor de la vigencia {anio}: logro si el encabezado dice 'VAL ALC', meta si no.",
            pos=pos_2024 + i, alternativas=alt, marca_logro="VAL ALC", notas=_NOTA_VALORES))
    return tuple(campos)


_NARRATIVA = (
    Campo("principal_logro", "Principal Logro en Función del Cumplimiento", "texto",
          "Narrativa reportada por la entidad.", nulo=True),
    Campo("analisis_logro", "Análisis del Logro", "texto", "Análisis del logro reportado.", nulo=True),
    Campo("dificultades_gestiones", "Dificultades o Gestiones", "texto",
          "Dificultades o gestiones reportadas.", nulo=True),
)

# Enfoque poblacional (EVAPLAN): cantidad de personas por grupo. Opcionales: la página solo muestra los que tienen datos.
FOCALIZACION = (
    ("foc_narp", "Negro, Mulato, Afrodescendiente, Raizal y Palenquero"), ("foc_indigena", "Indígena"),
    ("foc_rrom", "Room"), ("foc_campesinos", "Campesinos"), ("foc_nna", "Niños Niñas y Adolescentes"),
    ("foc_primera_infancia", "Primera Infancia"), ("foc_juventud", "Juventud"),
    ("foc_personas_mayores", "Personas Mayores"), ("foc_mujer", "Mujer"), ("foc_lgtbiq", "LGTBIQ+"),
    ("foc_discapacidad", "Personas con Discapacidad y sus Curadores"), ("foc_vulnerables", "Personas Vulnerables"),
    ("foc_habitantes_calle", "Habitantes de o en Calle"), ("foc_vbg", "Víctimas de Violencia de Género"),
    ("foc_victimas_conflicto", "Víctimas del Conflicto"), ("foc_reincorporados", "Reincorporados"),
    ("foc_comunales", "Comunales"), ("foc_interreligioso", "Interreligioso"),
    ("foc_rescatistas_animales", "Rescatistas de Animales"), ("foc_migrantes", "Migrantes"),
    ("foc_retornados", "Retornados"), ("foc_otros", "Otros"),
)


def _focalizacion_evaplan() -> tuple[Campo, ...]:
    campos = tuple(
        Campo(c, o, "decimal", f"Personas focalizadas: {o}.", nulo=True,
              notas="Opcional. 0 o vacío = sin focalización." + (" 'Room' (sic) es como viene en EVAPLAN." if o == "Room" else ""))
        for c, o in FOCALIZACION
    )
    return (*campos, Campo("foc_otro_cual", "¿Cuál Otro?", "texto", "Descripción del grupo en 'Otros'.", nulo=True))


# ---------------------------------------------------------------- EVAPLAN: Plan Indicativo MP
PI_MP_EVAPLAN = Esquema(
    nombre="pi_mp_evaplan",
    titulo="EVAPLAN · Informe de Plan Indicativo MP",
    descripcion="Metas de producto (MP) de UNA entidad con su programación vigente y el resultado reportado.",
    origen_datos="Descarga de EVAPLAN: 'Informe de Plan Indicativo MP.xlsx'",
    fila_encabezado=1,
    llave=("codigo_mp",),
    campos=(
        Campo("codigo_entidad", "Codigo Entidad", "codigo", "Código de la entidad (p. ej. '9999')."),
        Campo("nombre_entidad", "Nombre Entidad", "texto", "Nombre completo de la entidad."),
        Campo("codigo_mp", "Código de Meta", "codigo",
              "Código de la meta de producto: 'MP'+MR(5)+subprograma(2)+consecutivo(2)+producto MGA(7).",
              notas="18 caracteres. Ver descomponer_codigo_mp()."),
        Campo("descripcion_mp", "Descripción de Meta", "texto", "Texto de la meta de producto."),
        Campo("programa", "Codigo Programa", "codigo_nombre", "Programa del PDD ('14 - Nombre')."),
        Campo("subprograma", "Codigo Subprograma", "codigo_nombre", "Subprograma ('04 - Nombre')."),
        Campo("comportamiento", "Comportamiento del Indicador", "texto",
              "Tipo de indicador; define cómo se calcula el cumplimiento del PG."),
        Campo("linea_base", "Valor Linea Base", "decimal", "Valor de la línea base.", nulo=True),
        Campo("anio_linea_base", "Año Linea Base", "entero", "Año de la línea base.", nulo=True),
        Campo("periodicidad", "Periodicidad de Medición", "texto", "Anual, semestral, trimestral…"),
        Campo("unidad_medida", "Unidad de Medida", "texto", "Número, Porcentaje, Kilómetros…"),
        Campo("variables", "Variable", "texto", "Definición de las variables V1..Vn del indicador."),
        Campo("constante_k", "Constante (K)", "decimal", "Constante de la fórmula."),
        Campo("formula", "Fórmula", "texto", "Fórmula del indicador, p. ej. 'V1' o '((V1+V2)/720)*100'."),
        Campo("resultado", "Resultado", "decimal",
              "Último reporte ACUMULADO de la dependencia (✅ confirmado).",
              notas="Dato clave de seguimiento. En los datos es el acumulado de la VIGENCIA en curso "
                    "(menor que los logros previos sumados en metas acumuladas), no del cuatrienio."),
        Campo("valor_proyectado", "Valor Proyectado", "decimal",
              "Proyección de la dependencia sobre cómo cerrará la meta en la vigencia (✅ confirmado).",
              nulo=True,
              notas="Campo creado por el operador de EVAPLAN hacia nov-2025 para anticipar el cierre de las MP "
                    "(requerimiento de la Gobernación). Sigue existiendo en 2026, pero puede venir vacío. "
                    "Está en la misma escala que la meta de la vigencia."),
        *_valores_evaplan(),
        *_NARRATIVA,
        *_focalizacion_evaplan(),
    ),
    notas=(
        "Fila 1 es un título ('EvaPlan'); los encabezados están en la fila 2.",
        "No se lee (aún) el enfoque territorial: una columna por municipio (~42).",
        "Los encabezados de año son numéricos (2024, 2025, 2026.0…): se normalizan.",
    ),
)

# ---------------------------------------------------------------- EVAPLAN: Plan Indicativo MR
PI_MR_EVAPLAN = Esquema(
    nombre="pi_mr_evaplan",
    titulo="EVAPLAN · Informe de Plan Indicativo MR",
    descripcion="Metas de resultado (MR) de UNA entidad con programación vigente y resultado reportado.",
    origen_datos="Descarga de EVAPLAN: 'Informe de Plan Indicativo MR.xlsx'",
    fila_encabezado=1,
    llave=("codigo_mr",),
    campos=(
        Campo("codigo_entidad", "Codigo Entidad", "codigo", "Código de la entidad."),
        Campo("nombre_entidad", "Nombre Entidad", "texto", "Nombre completo de la entidad."),
        Campo("codigo_mr", "Código de Meta", "codigo", "Código de la meta de resultado, 5 dígitos ('99001').",
              notas="Equivale a los dígitos 3-7 del código MP asociado."),
        Campo("descripcion_mr", "Descripción de Meta", "texto", "Texto de la meta de resultado."),
        Campo("programa", "Codigo Programa", "codigo_nombre", "Programa del PDD."),
        Campo("comportamiento", "Comportamiento del Indicador", "texto", "Tipo de indicador."),
        Campo("linea_base", "Valor Linea Base", "decimal", "Valor de la línea base.", nulo=True),
        Campo("anio_linea_base", "Año Linea Base", "entero", "Año de la línea base.", nulo=True),
        Campo("periodicidad", "Periodicidad de Medición", "texto", "Periodicidad de medición."),
        Campo("unidad_medida", "Unidad de Medida", "texto", "Unidad de medida."),
        Campo("variables", "Variable", "texto", "Definición de variables."),
        Campo("constante_k", "Constante (K)", "decimal", "Constante de la fórmula."),
        Campo("formula", "Fórmula", "texto", "Fórmula del indicador."),
        Campo("resultado", "Resultado", "decimal", "Último reporte ACUMULADO de la dependencia (✅ confirmado)."),
        Campo("valor_proyectado", "Valor Proyectado", "decimal", "Proyección de cierre de la vigencia (puede venir vacío).", nulo=True),
        *_valores_evaplan(),
        *_NARRATIVA,
    ),
    notas=("Estructura inferida de un archivo de 4 filas; confirmar con una entidad con más metas.",),
)

# ---------------------------------------------------------------- EVAPLAN: Centralizadas
CENTRALIZADAS = Esquema(
    nombre="centralizadas",
    titulo="EVAPLAN · Centralizadas (Plan de Acción)",
    descripcion="Actividades de proyectos de inversión de UNA entidad, con presupuesto y avance de la vigencia.",
    origen_datos="Descarga de EVAPLAN: 'Centralizadas.xlsx'",
    fila_encabezado=1,
    llave=("id_registro",),
    campos=(
        Campo("id_registro", "ID", "codigo", "Identificador único del REGISTRO presupuestal en EVAPLAN (llave de la tabla)."),
        Campo("codigo_entidad", "Cod.Entidad", "codigo", "Código de la entidad."),
        Campo("nombre_entidad", "Nombre.Entidad", "texto", "Nombre ABREVIADO y con caracteres perdidos.",
              notas="No usar como llave: 'SRIA DE EJEMPLO  DE LA INFORM' (faltan tildes)."),
        Campo("codigo_proyecto", "Cód. Proyecto", "codigo", "Código del proyecto de inversión ('PI99-000001')."),
        Campo("nombre_proyecto", "Nombre Proyecto", "texto", "Nombre del proyecto."),
        Campo("bpin", "Cód. BPIN", "codigo", "Código BPIN (13 dígitos). Un proyecto tiene un solo BPIN."),
        Campo("codigo_mp", "Cód. MP", "codigo", "Meta de producto a la que contribuye la actividad."),
        Campo("descripcion_mp", "Descripción MP", "texto", "Texto de la meta de producto."),
        Campo("codigo_producto_mga", "Cód.Producto MGA", "codigo", "Producto MGA (7 dígitos).",
              notas="Casi siempre igual a los últimos 7 caracteres del código MP (en datos reales hay casos con 1 dígito de diferencia)."),
        Campo("producto_mga", "Producto MGA", "texto", "Nombre del producto MGA."),
        Campo("codigo_indicador_producto_mga", "Cod.Indicador Producto MGA", "codigo",
              "Indicador de producto MGA (9 dígitos).", notas="Normalmente producto + '00', no siempre."),
        Campo("indicador_producto_mga", "Indicador Producto MGA", "texto", "Nombre del indicador de producto."),
        Campo("codigo_actividad", "Cód. Actividad", "codigo",
              "Código de la actividad: '<proyecto>/a/b/cc/dd' (5 partes separadas por '/').",
              notas="Empieza siempre por el código del proyecto. NO es único: una actividad puede tener varios "
                    "registros (distinto ID, presupuesto y, a veces, estado, avance y observación)."),
        Campo("nombre_actividad", "Nombre Actividad", "texto", "Nombre de la actividad."),
        Campo("codigo_fondo", "Cód. Fondo", "codigo", "Código de la fuente de financiación."),
        Campo("nombre_fondo", "Nombre Fondo", "texto", "Nombre de la fuente de financiación."),
        Campo("ppto_inicial", "Ppto. Inicial", "moneda", "Presupuesto inicial (COP).",
              notas="Llega como texto con puntos de miles ('2.339.400.000')."),
        Campo("ppto_definitivo", "Ppto. Definitivo", "moneda", "Presupuesto definitivo (COP)."),
        Campo("ppto_obligaciones", "Ppto. Total Obligaciones", "moneda", "Total obligado (COP).",
              notas="Mezcla texto y entero 0 en la misma columna."),
        Campo("ppto_disponible", "Ppto. Disponible", "moneda", "Saldo aún no comprometido (COP).",
              notas="Invariante observado: disponible ≤ definitivo − obligaciones."),
        Campo("ppto_gestion", "Ppto. Gestión", "moneda", "Presupuesto de gestión.", nulo=True,
              notas="Vacío en toda la muestra."),
        Campo("codigo_fondo_gestion", "Cód. Fondo Gestión", "codigo", "Fondo de gestión.", nulo=True),
        Campo("fondo_gestion", "Fondo Gestión", "texto", "Fondo de gestión.", nulo=True),
        Campo("estado_actividad", "Estado Actividad", "texto", "CON EJECUCION / SIN EJECUCION.",
              notas="Observado: CON EJECUCION ⇔ obligaciones > 0."),
        Campo("unidad_medida", "Unid. Medida", "texto", "Unidad de medida de la actividad."),
        Campo("complemento", "Complemento", "texto", "Complemento de la unidad."),
        Campo("unidad_complemento", "Unid. + Compl.", "texto", "Unidad + complemento (texto armado)."),
        Campo("cant_programada_vigencia", "Cant. Prog. Vig.", "decimal", "Cantidad programada en la vigencia."),
        Campo("cant_ejecutada_vigencia", "Cant. Ejec. Vig.", "decimal", "Cantidad ejecutada en la vigencia.",
              nulo=True, notas="Vacío = sin avance reportado (se trata como 0 en el % de avance)."),
        Campo("avance_actividad_pct", "% Avance x Actividad", "decimal",
              "Avance de la actividad en %.", notas="= ejecutada / programada × 100 (verificado)."),
        Campo("observacion", "Observación", "texto", "Observación libre. El '.' es un marcador de vacío.",
              nulo=True),
        Campo("estado_registro", "Estado", "texto", "Estado del registro (ACTIVO)."),
    ),
    notas=("Fila 1 es un título ('EvaPlan'); los encabezados están en la fila 2.",
           "Cada fila es un REGISTRO presupuestal (llave: `ID`), no una actividad: la misma actividad aparece en "
           "varias filas cuando tiene varios registros. Los presupuestos se suman; el avance se promedia por registro.",
           "Solo trae los proyectos de los que la dependencia es centro gestor (módulo PA): pueden aportar a metas "
           "coordinadas por OTRA dependencia, y las metas propias pueden recibir aportes de proyectos ajenos."),
)


# ---------------------------------------------------------------- Drive: Plan Indicativo (hoja MP)
def _recursos_drive() -> tuple[Campo, ...]:
    totales = (
        (54, "recurso_total_2024", "TOTAL RECURSO 2024", "Total de recursos programados 2024 (COP)."),
        (66, "recurso_total_2025", "TOTAL RECURSO 2025", "Total de recursos programados 2025 (COP)."),
        (78, "recurso_total_2026", "TOTAL RECURSO 2026", "Total de recursos programados 2026 (COP)."),
        (90, "recurso_total_2027", "TOTAL RECURSO 2027", "Total de recursos programados 2027 (COP)."),
        (102, "recurso_total_pg", "TOTAL RECURSO 2024-2027", "Total de recursos del cuatrienio (COP)."),
    )
    return tuple(Campo(c, o, "moneda", d, nulo=True, pos=p) for p, c, o, d in totales)


PI_DRIVE_MP = Esquema(
    nombre="pi_drive_mp",
    titulo="Drive · Plan Indicativo (hoja MP)",
    descripcion="Libro maestro del Plan Indicativo 2024-2027: todas las metas de producto de TODAS las entidades.",
    origen_datos="Hoja de cálculo en Drive '<fecha>_Plan Indicativo (PI) 2024-2027', hoja 'MP' (URL en st.secrets).",
    fila_encabezado=1,
    llave=("codigo_mp",),
    hoja="MP",
    campos=(
        Campo("codigo_mp", "Código MP", "codigo", "Código de la meta de producto (18 caracteres).", pos=0),
        Campo("meta_producto", "Meta Producto", "texto", "'<código> - <descripción>' de la meta de producto.", pos=1),
        Campo("entidad", "Entidad", "codigo_nombre", "'9999 - SECRETARÍA…': código y nombre en una celda.", pos=2),
        Campo("linea_estrategica", "Línea Estrategica", "codigo_nombre", "Línea estratégica del PDD.", pos=3),
        Campo("programa", "Línea Programa", "codigo_nombre", "Programa del PDD.", pos=4),
        Campo("meta_resultado", "Meta Resultado Asociada", "codigo_nombre", "MR a la que aporta la MP.", pos=5),
        Campo("subprograma", "Subprograma", "codigo_nombre", "Subprograma.", pos=6),
        Campo("indicador_principal", "Indicador Principal", "texto", "Indicador principal.", nulo=True, pos=7),
        Campo("unidad_medida", "Unidad de medida", "texto", "Unidad de medida.", pos=21),
        Campo("comportamiento", "Comportamiento", "texto", "Tipo de indicador.", pos=22,
              notas="Hay variantes de mayúsculas ('Incremento flujo'): se normalizan."),
        Campo("linea_base", "Valor Linea Base", "decimal", "Línea base.", nulo=True, pos=23,
              notas="Contiene 'NO DISPONIBLE' en algunas filas."),
        Campo("anio_linea_base", "Año Linea Base", "entero", "Año de línea base.", nulo=True, pos=24,
              notas="Contiene rangos ('2020-2023') que pasan a nulo."),
        Campo("periodicidad", "Periodicidad de medición", "texto", "Periodicidad.", pos=25,
              notas="Mayúsculas aquí ('ANUAL'); en EVAPLAN 'Anual'."),
        Campo("fecha_actualizacion_indicador", "Fecha Actualizacion Indicador", "fecha",
              "Fecha de última actualización de la ficha del indicador.", nulo=True, pos=26),
        Campo("meta_pg_original", "Meta PG", "decimal", "PG original del Plan de Desarrollo.", nulo=True, pos=27),
        Campo("variables", "VARIABLES", "texto", "Definición de variables.", nulo=True, pos=28),
        Campo("formula", "FÓRMULA", "texto", "Fórmula.", nulo=True, pos=29),
        Campo("pi_pg", "PG 2024-2027.", "valor_np", "PG del Plan Indicativo original.", pos=30,
              notas="Encabezado con punto final (distinto de 'PG 2024-2027' de la pos. 35)."),
        Campo("pi_2024", "2024.", "valor_np", "Programación original 2024.", pos=31),
        Campo("pi_2025", "2025.", "valor_np", "Programación original 2025.", pos=32),
        Campo("pi_2026", "2026.", "valor_np", "Programación original 2026.", pos=33),
        Campo("pi_2027", "2027.", "valor_np", "Programación original 2027.", pos=34),
        Campo("valor_pg", "PG 2024-2027", "valor_np", "PG vigente (reprogramado).", pos=35),
        *_valores_drive(36, marcados=(2024, 2025)),
        Campo("verificacion_comportamiento", "VERIFICACIÓN DEL COMPORTAMIENTO DE META EN REPROGRAMACIÓN", "texto",
              "Comportamiento verificado por fórmula del libro (ACUMULADO, FLUJO…).", nulo=True, pos=40,
              notas="Puede contener 'ERROR' (fórmula fallida)."),
        Campo("edt", "EDT", "si_no", "¿Meta con EDT? (el encabezado trae la fecha de corte).", nulo=True, pos=41,
              prefijo=True),
        Campo("estado_meta", "ESTADO DE LA META DE PRODUCTO", "texto", "EN EJECUCIÓN / CUMPLIDA.", nulo=True,
              pos=42),
        *_recursos_drive(),
    ),
    notas=(
        "Las 2 primeras filas son: 1) bandas de bloque (celdas combinadas), 2) encabezados.",
        "Solo se leen las 103 primeras columnas de las 276. Los bloques posteriores (fuentes de recurso por año, "
        "enfoques poblacionales y territoriales, políticas públicas, POTD, IPM) no se leen aún.",
        "Hay ~448 filas con un par de filas vacías al final.",
    ),
)

# ---------------------------------------------------------------- Drive: Plan Indicativo (hoja MR)
PI_DRIVE_MR = Esquema(
    nombre="pi_drive_mr",
    titulo="Drive · Plan Indicativo (hoja MR)",
    descripcion="Libro maestro: todas las metas de resultado de TODAS las entidades.",
    origen_datos="Mismo libro de Drive, hoja 'MR'.",
    fila_encabezado=1,
    llave=("codigo_mr",),
    hoja="MR",
    campos=(
        Campo("codigo_mr", "COD MR", "codigo", "'MR99001' → se guarda '99001'.", pos=0),
        Campo("meta_resultado", "Meta resultado", "codigo_nombre",
              "'99001 - 99001-TEXTO': el código aparece duplicado; se corrige.", pos=1),
        Campo("entidad", "Entidad", "codigo_nombre", "Código y nombre de la entidad.", pos=2),
        Campo("nombre_indicador", "Nombre del Indicador", "texto", "Indicador de resultado.", nulo=True, pos=3),
        Campo("linea_estrategica", "Linea Estratégica", "codigo_nombre", "Línea estratégica.", pos=4),
        Campo("programa", "Programa Plan", "codigo_nombre", "Programa.", pos=5),
        Campo("unidad_medida", "Unidad de medida", "texto", "Unidad de medida.", pos=12),
        Campo("linea_base", "Valor linea Base", "decimal", "Línea base.", nulo=True, pos=13),
        Campo("anio_linea_base", "Año linea Base", "entero", "Año de línea base.", nulo=True, pos=14),
        Campo("comportamiento", "Comportamiento del indicador", "texto", "Tipo de indicador.", pos=15,
              notas="Incluye 'Reducción Anual', que no existe en metas de producto."),
        Campo("meta_pg_original", "Meta PG", "decimal", "PG original.", nulo=True, pos=16),
        Campo("periodicidad", "Periodicidad de medición", "texto", "Periodicidad.", pos=17,
              notas="Contiene el error de digitación 'Semetral'."),
        Campo("fecha_actualizacion_indicador", "Fecha Actualización Indicador", "fecha", "Última actualización.",
              nulo=True, pos=18),
        Campo("variables", "VARIABLES", "texto", "Variables.", nulo=True, pos=19),
        Campo("formula", "FORMULA", "texto", "Fórmula.", nulo=True, pos=20),
        Campo("pi_pg", "PG", "valor_np", "PG original.", pos=21),
        Campo("pi_2024", "2024", "valor_np", "Programación original 2024.", pos=22),
        Campo("pi_2025", "2025", "valor_np", "Programación original 2025.", pos=23),
        Campo("pi_2026", "2026", "valor_np", "Programación original 2026.", pos=24),
        Campo("pi_2027", "2027", "valor_np", "Programación original 2027.", pos=25),
        Campo("valor_pg", "PG", "valor_np", "PG vigente (reprogramado).", pos=26),
        *_valores_drive(27, marcados=(2024,)),
        Campo("verificacion_comportamiento", "VERIFICACIÓN DEL COMPORTAMIENTO DE META EN REPROGRAMACIÓN", "texto",
              "Comportamiento verificado.", nulo=True, pos=31, notas="27 de 75 filas en 'ERROR'."),
    ),
    notas=("Encabezados repetidos (PG, 2024…2027 aparecen dos veces): por eso se lee por posición.",),
)

ESQUEMAS = {e.nombre: e for e in (PI_MP_EVAPLAN, PI_MR_EVAPLAN, CENTRALIZADAS, PI_DRIVE_MP, PI_DRIVE_MR)}
