import re
import xml.etree.ElementTree as ET
import docx
import unicodedata
import pandas as pd
import streamlit as st

# ============================================================
# CONFIGURACIÓN INICIAL DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Revisión de Cadenas de Valor y MGA",
    page_icon="📐",
    layout="wide",
)

URL_DRIVE_EXCEL = "https://docs.google.com/spreadsheets/d/18z_tAg7RPvSTSRSTYoYtKgIV3ch3cQ-JbcAOTjQD8ss/export?format=xlsx"


# ============================================================
# FUNCIONES AUXILIARES Y DE CACHÉ
# ============================================================
def extraer_codigo_numerico(texto, prefijo=""):
    """Aísla la secuencia numérica de un texto (ej. 'MP24 - Nombre' -> '24')."""
    if pd.isna(texto) or str(texto).strip().lower() == "nan":
        return ""
    texto_str = str(texto).strip()
    if "-" in texto_str:
        texto_str = texto_str.split("-")[0].strip()
    digitos = re.sub(r"\D", "", texto_str)
    return f"{prefijo}{digitos}" if digitos else ""


@st.cache_data(show_spinner=False)
def leer_plan_indicativo_drive(url_excel):
    """Carga en caché la pestaña 'MP' del Plan Indicativo desde Drive."""
    return pd.read_excel(url_excel, sheet_name="MP", header=1, engine="openpyxl")


def cruzar_con_plan_indicativo(df_indicadores, url_excel):
    """Cruza la matriz de indicadores DOCX con la hoja 'MP' de Google Drive usando el código MP."""
    try:
        df_pi = leer_plan_indicativo_drive(url_excel)
        df_pi.columns = [str(col).strip() for col in df_pi.columns]

        col_mp_pi = next(
            (c for c in df_pi.columns if "meta" in c.lower() and "producto" in c.lower()),
            df_pi.columns[0],
        )

        df_pi["Codigo_MP_Clean"] = df_pi[col_mp_pi].apply(
            lambda x: extraer_codigo_numerico(x, "MP")
        )

        df_ind_copy = df_indicadores.copy()
        if "Código MP" in df_ind_copy.columns:
            df_ind_copy["Codigo_MP_Clean"] = df_ind_copy["Código MP"].apply(
                lambda x: extraer_codigo_numerico(x, "MP")
            )
        else:
            return df_indicadores, "No se encontró la columna 'Código MP' para realizar el cruce."

        df_cruzado = pd.merge(
            df_ind_copy,
            df_pi,
            on="Codigo_MP_Clean",
            how="left",
            suffixes=("", "_Drive"),
        )
        df_cruzado.drop(columns=["Codigo_MP_Clean"], inplace=True, errors="ignore")

        return df_cruzado, None
    except Exception as e:
        return df_indicadores, f"Error al procesar el Plan Indicativo de Drive: {e}"


# ============================================================
# FUNCIONES EXTRACTORAS: MGA DESDE XML (SIN FUENTE DE VERIFICACIÓN)
# ============================================================
def procesar_mga_xml(xml_buffer) -> pd.DataFrame:
    """
    Parsea el archivo XML de la MGA DNP relacionando Objetivos Específicos
    con sus Productos e Indicadores mediante SpecificObjectiveId.
    """
    tree = ET.parse(xml_buffer)
    root = tree.getroot()

    # 1. Mapear Objetivos Específicos por su <Id>
    mapa_objetivos = {}
    for cause in root.findall(".//Cause"):
        obj_node = cause.find("SpecificObjective")
        if obj_node is not None:
            obj_id = obj_node.findtext("Id", "").strip()
            obj_desc = obj_node.findtext("SpecificObjective", "").strip()
            if obj_id and obj_desc:
                mapa_objetivos[obj_id] = obj_desc

    # Fallback si el árbol no usa nodos Cause/SpecificObjective explícitos
    if not mapa_objetivos:
        for obj in root.findall(".//SpecificObjective"):
            obj_id = obj.findtext("Id", "").strip()
            obj_desc = obj.findtext("SpecificObjective", "").strip() or obj.findtext("Description", "").strip()
            if obj_id and obj_desc:
                mapa_objetivos[obj_id] = obj_desc

    # 2. Recorrer los Productos y vincular con su Objetivo Específico
    registros = []
    productos = root.findall(".//Product")

    for idx, prod in enumerate(productos):
        spec_obj_id = prod.findtext("SpecificObjectiveId", "").strip()
        objetivo_texto = mapa_objetivos.get(spec_obj_id, "Sin Objetivo Asociado")

        nombre_producto = prod.findtext("ProductName", "").strip()
        auto_indicador = prod.findtext("AutoIndicatorName", "").strip()
        
        # Meta / Cantidad
        amount = prod.findtext("Amount", "").strip()
        goal = prod.findtext("Goal", "").strip()
        meta = amount if amount and amount != "0.0000" else goal

        if nombre_producto or auto_indicador:
            registros.append({
                "No.": idx + 1,
                "ID Obj. Específico": spec_obj_id,
                "Objetivo Específico": objetivo_texto,
                "Producto MGA": nombre_producto,
                "Indicador MGA": auto_indicador,
                "Meta / Cantidad": meta,
            })

    # Fallback genérico en caso de estructura no estándar
    if not registros:
        for idx, node in enumerate(root.findall(".//*")):
            data = {child.tag.split("}")[-1]: child.text.strip() for child in node if child.text and child.text.strip()}
            if "ProductName" in data or "desProducto" in data or "NombreProducto" in data:
                registros.append({
                    "No.": len(registros) + 1,
                    "ID Obj. Específico": data.get("SpecificObjectiveId", "N/A"),
                    "Objetivo Específico": data.get("desObjetivo", data.get("Objetivo", "No detectado")),
                    "Producto MGA": data.get("ProductName", data.get("desProducto", data.get("NombreProducto", ""))),
                    "Indicador MGA": data.get("AutoIndicatorName", data.get("desIndicador", data.get("NombreIndicador", ""))),
                    "Meta / Cantidad": data.get("Amount", data.get("Goal", data.get("valMeta", "0"))),
                })

    df_resultado = pd.DataFrame(registros)
    return df_resultado.drop_duplicates() if not df_resultado.empty else df_resultado




# ============================================================
# FUNCIONES EXTRACTORAS: ARCHIVO WORD (PYTHON-DOCX)
# ============================================================

def extraer_texto_y_tablas_docx(file_buffer) -> str:
    """
    Lee el archivo .docx extrayendo texto de párrafos, tablas de primer nivel 
    y TABLAS ANIDADAS (dentro de celdas o contenedores).
    """
    doc = docx.Document(file_buffer)
    contenido_total = []

    def procesar_tabla(tabla):
        """Extrae filas y recursivamente procesa tablas anidadas dentro de celdas."""
        for fila in tabla.rows:
            textos_celdas = []
            for celda in fila.cells:
                # Texto plano de la celda
                texto_celda = celda.text.strip().replace("\n", " ")
                textos_celdas.append(texto_celda)
                
                # DETECCIÓN DE TABLAS ANIDADAS
                if celda.tables:
                    for tabla_anidada in celda.tables:
                        contenido_total.append("#")
                        procesar_tabla(tabla_anidada)

            if any(textos_celdas):
                contenido_total.append(" | ".join(textos_celdas))

    # Recorrido jerárquico de elementos del cuerpo
    for elemento in doc.element.body:
        if elemento.tag.endswith("p"):
            p = docx.text.paragraph.Paragraph(elemento, doc)
            if p.text.strip():
                contenido_total.append(p.text)
        elif elemento.tag.endswith("tbl"):
            tabla = docx.table.Table(elemento, doc)
            contenido_total.append("#")
            procesar_tabla(tabla)

    return "\n".join(contenido_total)


def extraer_encabezado_estandar(texto_bruto: str) -> dict:
    """Extrae las variables de identificación del encabezado."""
    metadatos = {
        "dependencia": "No detectada",
        "fecha": "No detectada",
        "nombre_proyecto_encabezado": "No detectado",
        "id_mga": "No detectado",
        "bpin": "No detectado",
        "codigo_pi": "No detectado",
    }

    match_fecha = re.search(r"Fecha:\s*([\d/:-]+)", texto_bruto, re.IGNORECASE)
    if match_fecha:
        metadatos["fecha"] = match_fecha.group(1)

    match_nom = re.search(r"PROYECTO INVERSIÓN:\s*[“\"']([^”\"']+)[”\"']", texto_bruto, re.IGNORECASE)
    if match_nom:
        metadatos["nombre_proyecto_encabezado"] = match_nom.group(1).strip()

    match_mga = re.search(r"ID-MGA:\s*(\w+)", texto_bruto, re.IGNORECASE)
    match_bpin = re.search(r"BPIN\s*(\d+)", texto_bruto, re.IGNORECASE)
    match_pi = re.search(r"(PI\d+-\d+)", texto_bruto, re.IGNORECASE)

    if match_mga: metadatos["id_mga"] = match_mga.group(1).strip()
    if match_bpin: metadatos["bpin"] = match_bpin.group(1).strip()
    if match_pi: metadatos["codigo_pi"] = match_pi.group(1).strip()

    return metadatos


def procesar_tablas_estandar(texto_bruto: str):
    """
    Procesa las tablas de la Cadena de Valor (DOCX) identificando
    específicamente cada sección sin conflictos de coincidencia.
    """
    bloques = [b.strip() for b in texto_bruto.split("#") if b.strip()]
    dicc_indicadores = {}
    lista_actividades_poai = []
    recurso_total_proyecto = "$0"
    nombre_proyecto_tabla = "No detectado"

    def normalizar_texto(texto: str) -> str:
        """Remueve tildes y convierte a minúsculas para comparaciones seguras."""
        texto_norm = unicodedata.normalize('NFD', texto)
        texto_norm = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
        return texto_norm.lower().strip()

    def descomponer_linea(l):
        return [p.strip() for p in l.split("|")]

    def obtener_valor(partes, indice, default=""):
        return partes[indice] if len(partes) > indice and indice >= 0 else default

    for bloque in bloques:
        lineas = [l for l in bloque.split("\n") if l.strip()]
        if not lineas:
            continue
        
        encabezado_norm = normalizar_texto(lineas[0])
        contexto_bloque = normalizar_texto(" ".join(lineas[:3]))

        # ----------------------------------------------------
        # TABLA 1: Datos Básicos y Objetivos
        # ----------------------------------------------------
        if "no.cv" in encabezado_norm and "objetivo general" in encabezado_norm:
            for l in lineas[1:]:
                partes = descomponer_linea(l)
                if partes and partes[0].isdigit():
                    idx = int(partes[0])
                    if idx not in dicc_indicadores:
                        dicc_indicadores[idx] = {}
                    
                    dicc_indicadores[idx]["No.CV"] = obtener_valor(partes, 1)
                    dicc_indicadores[idx]["Dependencia"] = obtener_valor(partes, 2)
                    dicc_indicadores[idx]["Nombre Proyecto"] = obtener_valor(partes, 3)
                    dicc_indicadores[idx]["Fecha CV"] = obtener_valor(partes, 4)
                    dicc_indicadores[idx]["Objetivo General Proyecto"] = obtener_valor(partes, 5)
                    dicc_indicadores[idx]["Objetivo Específico"] = obtener_valor(partes, 6)

                    if nombre_proyecto_tabla == "No detectado" and len(partes) > 3 and partes[3]:
                        nombre_proyecto_tabla = partes[3]

        # ----------------------------------------------------
        # TABLA 2: Alineación Estratégica
        # ----------------------------------------------------
        elif "sector mga-sap" in encabezado_norm and "subprograma plan" in encabezado_norm:
            for l in lineas[1:]:
                partes = descomponer_linea(l)
                if partes and partes[0].isdigit():
                    idx = int(partes[0])
                    if idx not in dicc_indicadores:
                        dicc_indicadores[idx] = {}
                    
                    dicc_indicadores[idx]["Sector MGA-SAP"] = obtener_valor(partes, 1)
                    dicc_indicadores[idx]["Línea Estratégica"] = obtener_valor(partes, 2)
                    dicc_indicadores[idx]["Programa Plan de Desarrollo"] = obtener_valor(partes, 3)
                    dicc_indicadores[idx]["Programa MGA"] = obtener_valor(partes, 4)
                    dicc_indicadores[idx]["Meta de Resultado"] = obtener_valor(partes, 5)
                    dicc_indicadores[idx]["Subprograma Plan"] = obtener_valor(partes, 6)

        # ----------------------------------------------------
        # TABLA 3: Metas, Productos e Indicadores
        # Detección específica evitando capturar la Tabla 5
        # ----------------------------------------------------
        elif "meta producto plan" in encabezado_norm or "meta total mga" in encabezado_norm:
            for l in lineas[1:]:
                partes = descomponer_linea(l)
                if partes and partes[0].isdigit():
                    idx = int(partes[0])
                    if idx not in dicc_indicadores:
                        dicc_indicadores[idx] = {}

                    meta_producto_texto = obtener_valor(partes, 1)
                    dicc_indicadores[idx]["Meta Producto Plan"] = meta_producto_texto

                    match_mp = re.search(r"(MP\d+)", meta_producto_texto)
                    dicc_indicadores[idx]["Código MP"] = match_mp.group(1) if match_mp else "Sin Código"

                    dicc_indicadores[idx]["P.G. PI"] = obtener_valor(partes, 2)
                    dicc_indicadores[idx]["2024 PI"] = obtener_valor(partes, 3)
                    dicc_indicadores[idx]["2025 PI"] = obtener_valor(partes, 4)
                    dicc_indicadores[idx]["2026 PI"] = obtener_valor(partes, 5)
                    dicc_indicadores[idx]["2027 PI"] = obtener_valor(partes, 6)
                    dicc_indicadores[idx]["Código y Nombre Producto Catalogo - MP"] = obtener_valor(partes, 7)
                    dicc_indicadores[idx]["Indicador de Producto Catalogo - MP"] = obtener_valor(partes, 8)
                    dicc_indicadores[idx]["Unidad de Medida"] = obtener_valor(partes, 9)
                    dicc_indicadores[idx]["Meta Total MGA"] = obtener_valor(partes, 10)
                    dicc_indicadores[idx]["2024 MGA"] = obtener_valor(partes, 11)
                    dicc_indicadores[idx]["2025 MGA"] = obtener_valor(partes, 12)
                    dicc_indicadores[idx]["2026 MGA"] = obtener_valor(partes, 13)
                    dicc_indicadores[idx]["2027 MGA"] = obtener_valor(partes, 14)

        # ----------------------------------------------------
        # TABLA 4: Observaciones y Tipificación
        # ----------------------------------------------------
        elif "observacion por indicador" in encabezado_norm or "producto cv - mga" in encabezado_norm:
            for l in lineas[1:]:
                partes = descomponer_linea(l)
                if partes and partes[0].isdigit():
                    idx = int(partes[0])
                    if idx not in dicc_indicadores:
                        dicc_indicadores[idx] = {}

                    dicc_indicadores[idx]["Observación por Indicador MGA - Formulador"] = obtener_valor(partes, 1)
                    dicc_indicadores[idx]["Producto CV - MGA"] = obtener_valor(partes, 2)
                    dicc_indicadores[idx]["Indicador de Producto CV - MGA"] = obtener_valor(partes, 3)
                    dicc_indicadores[idx]["Tipo prod."] = obtener_valor(partes, 4)
                    dicc_indicadores[idx]["Tipo prod2"] = obtener_valor(partes, 5)

        # ----------------------------------------------------
        # TABLA 5: Actividades y Presupuesto POAI
        # Identificación inequívoca por "poai" o presencia combinada de actividades y costo
        # ----------------------------------------------------
        elif any(term in contexto_bloque for term in ["poai", "costo total", "presupuesto poai", "fuente de financiacion"]) or \
             ("actividad" in contexto_bloque and ("recurso" in contexto_bloque or "valor" in contexto_bloque or "etapa" in contexto_bloque)):
            
            nombres_columnas = [c.strip() for c in lineas[0].split("|") if c.strip()]
            
            for l in lineas[1:]:
                partes = descomponer_linea(l)
                texto_linea = " ".join(partes).upper()
                texto_norm_linea = normalizar_texto(texto_linea)

                if "TOTAL" in texto_linea or "PROYECTO DE INVERSION" in texto_norm_linea:
                    recurso_total_proyecto = partes[-1] if partes else "$0"
                    continue

                if len(partes) >= 2 and "FIRMA" not in texto_linea:
                    actividad = {}
                    for idx_col, nombre_col in enumerate(nombres_columnas):
                        actividad[nombre_col] = obtener_valor(partes, idx_col)
                    
                    match_mp = re.search(r"(MP\d+)", texto_linea)
                    actividad["Código MP Extrayendo"] = match_mp.group(1) if match_mp else "Sin Código"
                    
                    lista_actividades_poai.append(actividad)

    # ----------------------------------------------------
    # CONSTRUCCIÓN DE DATAFRAMES FINALES
    # ----------------------------------------------------
    df_indicadores = pd.DataFrame.from_dict(dicc_indicadores, orient="index")
    if not df_indicadores.empty and "Código MP" in df_indicadores.columns:
        cols = list(df_indicadores.columns)
        cols.insert(0, cols.pop(cols.index("Código MP")))
        df_indicadores = df_indicadores[cols]

    df_poai = pd.DataFrame(lista_actividades_poai)
    return df_indicadores, df_poai, recurso_total_proyecto, nombre_proyecto_tabla







# ============================================================
# INTERFAZ STREAMLIT
# ============================================================
st.title("📐 Control Previo y Revisión Técnica de Proyectos")
st.write("Módulo integral para el análisis de Cadenas de Valor (.docx), Archivos XML MGA DNP (.xml) y Plan Indicativo.")
st.markdown("---")

tab_cv, tab_mga, tab_cruce = st.tabs([
    "📄 Cadena de Valor (DOCX)",
    "📑 Reporte MGA DNP (XML) / Comparativa",
    "🔍 Análisis y Cruce de Información",
])

# TAB 1: CADENA DE VALOR (DOCX)
with tab_cv:
    st.subheader("Carga y Procesamiento de Cadena de Valor (.docx)")
    archivo_word = st.file_uploader("📂 Sube aquí la Cadena de Valor en Word", type=["docx"], key="uploader_docx")

    if archivo_word is not None:
        if "ultimo_archivo_word" not in st.session_state or st.session_state["ultimo_archivo_word"] != archivo_word.name:
            with st.spinner("⏳ Procesando Word..."):
                try:
                    texto_extraido = extraer_texto_y_tablas_docx(archivo_word)
                    metadatos = extraer_encabezado_estandar(texto_extraido)
                    df_ind, df_poai, total_presupuesto, proyecto_nombre_tabla = procesar_tablas_estandar(texto_extraido)

                    st.session_state["df_indicadores_estandar"] = df_ind
                    st.session_state["df_poai_estandar"] = df_poai
                    st.session_state["total_presupuesto_poai"] = total_presupuesto
                    st.session_state["proyecto_nombre_tabla"] = proyecto_nombre_tabla
                    st.session_state["metadatos"] = metadatos
                    st.session_state["ultimo_archivo_word"] = archivo_word.name
                    st.success("✅ Cadena de Valor procesada.")
                except Exception as e:
                    st.error(f"🚨 Error al procesar Word: {e}")

    if "df_indicadores_estandar" in st.session_state:
        st.markdown("### 📌 Identificación del Proyecto")
        c1, c2, c3 = st.columns(3)
        c1.text_input("Proyecto (Tabla):", value=st.session_state.get("proyecto_nombre_tabla", ""), disabled=True)
        c2.text_input("Código PI:", value=st.session_state.get("metadatos", {}).get("codigo_pi", ""), disabled=True)
        c3.text_input("Código BPIN:", value=st.session_state.get("metadatos", {}).get("bpin", ""), disabled=True)

        st.markdown("### 📊 Matriz de Indicadores (Tablas 1-4)")
        st.dataframe(st.session_state["df_indicadores_estandar"], use_container_width=True)

        st.markdown("### 💰 Actividades POAI 2027")
        st.dataframe(st.session_state["df_poai_estandar"], use_container_width=True)
        st.metric("💰 TOTAL 2027", st.session_state.get("total_presupuesto_poai", "$0"))

# TAB 2: REPORTE MGA (XML) Y COMPARATIVA PARALELA
with tab_mga:
    st.subheader("📑 Reporte MGA DNP (XML) y Verificación en Paralelo")
    archivo_xml = st.file_uploader("📂 Sube el archivo XML de la MGA DNP", type=["xml"], key="uploader_xml")

    if archivo_xml is not None:
        if "ultimo_archivo_xml" not in st.session_state or st.session_state["ultimo_archivo_xml"] != archivo_xml.name:
            with st.spinner("⏳ Parseando archivo XML de la MGA..."):
                try:
                    df_mga = procesar_mga_xml(archivo_xml)
                    st.session_state["df_mga_productos"] = df_mga
                    st.session_state["ultimo_archivo_xml"] = archivo_xml.name
                    st.success("✅ Archivo XML parseado correctamente.")
                except Exception as e:
                    st.error(f"🚨 Error al parsear el XML: {e}")

    # Si hay información del XML parseada
    if "df_mga_productos" in st.session_state:
        df_mga = st.session_state["df_mga_productos"]
        df_docx = st.session_state.get("df_indicadores_estandar", pd.DataFrame())

        st.markdown("---")
        
        # Si el usuario ya subió el Word, mostramos ambas tablas LADO A LADO
        if not df_docx.empty:
            st.info("💡 **Vista de verificación paralela:** Compara los datos del Word contra los del XML.")
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("### 📄 Cadena de Valor (DOCX)")
                # Mostramos columnas clave del Word para la comparación rápida
                cols_visibles = [c for c in ["Objetivo Específico", "Código y Nombre Producto Catalogo - MP", "Indicador de Producto Catalogo - MP", "Meta Total MGA"] if c in df_docx.columns]
                st.dataframe(df_docx[cols_visibles] if cols_visibles else df_docx, use_container_width=True)

            with col_right:
                st.markdown("### 📑 Sistema MGA DNP (XML)")
                st.dataframe(df_mga, use_container_width=True, hide_index=True)

        else:
            # Si solo ha subido el XML, mostramos la tabla completa del XML a ancho completo
            st.warning("ℹ️ Sube la Cadena de Valor (.docx) en la Pestaña 1 para habilitar la vista comparativa lado a lado.")
            st.markdown("### 📋 Resumen MGA desde XML")
            st.dataframe(df_mga, use_container_width=True, hide_index=True)

        # Botón de descarga
        csv_mga = df_mga.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Resumen XML en CSV",
            data=csv_mga,
            file_name="resumen_mga_xml.csv",
            mime="text/csv",
        )

# ============================================================
# TAB 3: ANÁLISIS Y CRUCE DE INFORMACIÓN (CON ESTILIZADO AZUL)
# ============================================================
with tab_cruce:
    st.subheader("🔗 Cruce de Cadena de Valor con Plan Indicativo (Drive)")

    if "df_indicadores_estandar" in st.session_state:
        df_ind = st.session_state["df_indicadores_estandar"]

        if not df_ind.empty:
            with st.spinner("⏳ Conectando con Google Drive y realizando cruce..."):
                df_cruzado, err = cruzar_con_plan_indicativo(df_ind, URL_DRIVE_EXCEL)

            if err:
                st.error(f"🚨 {err}")
            else:
                st.success("✅ Cruce realizado correctamente.")
                
                # Identificamos las columnas que vienen del Word
                cols_originales = set(df_ind.columns)
                
                # Función para aplicar el fondo azul claro a las columnas traídas de Drive
                def destacar_columnas_drive(val, col_name):
                    # Si la columna no estaba en el df original de Word, viene de Drive
                    if col_name not in cols_originales:
                        return "background-color: #E8F4F8; color: #1E3A8A;"
                    return ""

                # Aplicamos el estilo por columna al DataFrame
                df_estilizado = df_cruzado.style.apply(
                    lambda col: [destacar_columnas_drive(v, col.name) for v in col],
                    axis=0
                )

                st.markdown("### 📊 Matriz Consolidada")
                st.caption("🟦 *Las columnas con fondo azul claro corresponden a los datos extraídos del Plan Indicativo (Google Drive).*")
                
                # Renderizamos la tabla estilizada
                st.dataframe(df_estilizado, use_container_width=True)

                # Para la descarga mantenemos el DataFrame plano (sin CSS)
                csv_cruzado = df_cruzado.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Descargar Matriz Cruzada en CSV",
                    data=csv_cruzado,
                    file_name="matriz_cruzada_plan_indicativo.csv",
                    mime="text/csv",
                )
        else:
            st.warning("La matriz del DOCX está vacía.")
    else:
        st.info("💡 Procesa primero una Cadena de Valor (.docx) en la pestaña 1 para habilitar el cruce.")
        
# ============================================================
# COMPONENTE DE AUDITORÍA: WORD VS. PLAN INDICATIVO (PI)
# ============================================================

st.markdown("---")
st.subheader("🔍 Auditoría de Coherencia: Word vs. Plan Indicativo (PI)")

if "df_indicadores_estandar" in st.session_state and not st.session_state["df_indicadores_estandar"].empty:
    df_word = st.session_state["df_indicadores_estandar"].copy()

    # ------------------------------------------------------------
    # 1. BOTÓN DE PROCESAMIENTO (CÁLCULO Y PERSISTENCIA)
    # ------------------------------------------------------------
    if st.button("🚀 Ejecutar Cruce y Comparación con PI"):
        with st.spinner("⏳ Conectando con Plan Indicativo y auditando comportamiento de metas..."):
            try:
                df_drive = leer_plan_indicativo_drive(URL_DRIVE_EXCEL)
                
                columnas_reales = list(df_drive.columns)
                col_codigo_mp = None
                col_indicador_drive = None
                col_pg = None
                col_val_2024 = None
                col_val_2025 = None
                col_prog_2026 = None
                col_prog_2027 = None
                col_comportamiento = None
                
                coincidencias_pg = []
                for idx, col in enumerate(columnas_reales):
                    col_limpia = str(col).strip().upper().replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
                    
                    if "CODIGO MP" in col_limpia:
                        col_codigo_mp = col
                    elif "INDICADOR" in col_limpia and "PRODUCTO" in col_limpia:
                        col_indicador_drive = col
                    elif "PG 2024-2027" in col_limpia or "PROGRAMACION GENERAL" in col_limpia:
                        coincidencias_pg.append(col)
                    elif "VAL ALC 2024" in col_limpia:
                        col_val_2024 = col
                    elif "VAL ALC 2025" in col_limpia:
                        col_val_2025 = col
                        if idx + 1 < len(columnas_reales):
                            col_prog_2026 = columnas_reales[idx + 1]
                        if idx + 2 < len(columnas_reales):
                            col_prog_2027 = columnas_reales[idx + 2]
                    elif "VERIFICACION DEL COMPORTAMIENTO DE META" in col_limpia or "COMPORTAMIENTO" in col_limpia:
                        col_comportamiento = col

                if len(coincidencias_pg) >= 2:
                    col_pg = coincidencias_pg[1]
                elif len(coincidencias_pg) == 1:
                    col_pg = coincidencias_pg[0]

                if col_codigo_mp and col_indicador_drive:
                    dict_pi_datos = {}
                    
                    for _, fila in df_drive.iterrows():
                        mp_raw = fila[col_codigo_mp]
                        mp_llave = extraer_codigo_numerico(mp_raw)
                        
                        if mp_llave:
                            ind_pi_raw = str(fila[col_indicador_drive]).strip() if pd.notna(fila[col_indicador_drive]) else "S/N"
                            cod_prod_pi = extraer_codigo_numerico(ind_pi_raw)
                            
                            val_pg = fila[col_pg] if col_pg and pd.notna(fila[col_pg]) else 0.0
                            val_2024 = fila[col_val_2024] if col_val_2024 and pd.notna(fila[col_val_2024]) else "NP"
                            val_2025 = fila[col_val_2025] if col_val_2025 and pd.notna(fila[col_val_2025]) else "NP"
                            val_2026 = fila[col_prog_2026] if col_prog_2026 and pd.notna(fila[col_prog_2026]) else "NP"
                            val_2027 = fila[col_prog_2027] if col_prog_2027 and pd.notna(fila[col_prog_2027]) else "NP"
                            comportamiento = str(fila[col_comportamiento]).strip().upper() if col_comportamiento and pd.notna(fila[col_comportamiento]) else "S/D"
                            
                            dict_pi_datos[mp_llave] = {
                                "ind_texto": ind_pi_raw,
                                "cod_prod_pi": cod_prod_pi,
                                "pg": val_pg,
                                "val_2024": val_2024,
                                "val_2025": val_2025,
                                "prog_2026": val_2026,
                                "prog_2027": val_2027,
                                "comportamiento": comportamiento
                            }

                    logs_diagnostico = []
                    resultados_validacion = []
                    textos_pi_encontrados = []
                    codigos_word_extraidos = []
                    codigos_pi_extraidos = []
                    
                    list_pg = []
                    list_2024 = []
                    list_2025 = []
                    list_2026 = []
                    list_2027 = []
                    list_comportamiento = []
                    list_ejecutado_hasta_2026 = []
                    list_sugerencia_poai = []

                    def convertir_a_numero(val):
                        if pd.isna(val):
                            return 0.0
                        val_str = str(val).strip().upper().replace(",", ".")
                        if val_str in ["NP", "N/A", "S/D", ""]:
                            return 0.0
                        try:
                            return round(float(val_str), 2)
                        except ValueError:
                            return 0.0

                    def formatear_valor(val):
                        if pd.isna(val):
                            return "0.00"
                        val_str = str(val).strip().upper()
                        if val_str in ["NP", "N/A", "S/D"]:
                            return val_str
                        try:
                            num = float(val_str.replace(",", "."))
                            return f"{num:.2f}"
                        except ValueError:
                            return val_str

                    for i, fila_word in df_word.iterrows():
                        mp_word_raw = fila_word.get("Código MP", "")
                        mp_llave_word = extraer_codigo_numerico(mp_word_raw)
                        
                        ind_word_raw = fila_word.get("Indicador de Producto CV - MGA", "")
                        cod_prod_word = extraer_codigo_numerico(ind_word_raw)
                        
                        codigos_word_extraidos.append(cod_prod_word if cod_prod_word else "No detectado")
                        
                        if not mp_llave_word or mp_llave_word not in dict_pi_datos:
                            resultados_validacion.append("🔴 MP no existe en PI" if mp_llave_word else "🔴 MP ausente en Word")
                            textos_pi_encontrados.append("NO EXISTE META EN PI")
                            codigos_pi_extraidos.append("N/A")
                            list_pg.append("N/A")
                            list_2024.append("N/A")
                            list_2025.append("N/A")
                            list_2026.append("N/A")
                            list_2027.append("N/A")
                            list_comportamiento.append("N/A")
                            list_ejecutado_hasta_2026.append("0.00")
                            list_sugerencia_poai.append("⚠️ Revisar MP")
                            logs_diagnostico.append(f"❌ Fila {i}: La meta '{mp_word_raw}' no se encontró en el PI.")
                        else:
                            datos_meta = dict_pi_datos[mp_llave_word]
                            
                            cod_prod_pi = datos_meta["cod_prod_pi"]
                            texto_pi = datos_meta["ind_texto"]
                            
                            codigos_pi_extraidos.append(cod_prod_pi if cod_prod_pi else "No detectado")
                            textos_pi_encontrados.append(texto_pi)
                            
                            pg_val = datos_meta["pg"]
                            v_2024 = datos_meta["val_2024"]
                            v_2025 = datos_meta["val_2025"]
                            v_2026 = datos_meta["prog_2026"]
                            v_2027 = datos_meta["prog_2027"]
                            comp_val = datos_meta["comportamiento"]
                            
                            list_pg.append(formatear_valor(pg_val))
                            list_2024.append(formatear_valor(v_2024))
                            list_2025.append(formatear_valor(v_2025))
                            list_2026.append(formatear_valor(v_2026))
                            list_2027.append(formatear_valor(v_2027))
                            list_comportamiento.append(comp_val)
                            
                            num_2024 = convertir_a_numero(v_2024)
                            num_2025 = convertir_a_numero(v_2025)
                            num_2026 = convertir_a_numero(v_2026)
                            
                            suma_2026 = round(num_2024 + num_2025 + num_2026, 2)
                            pg_num = convertir_a_numero(pg_val)
                            
                            list_ejecutado_hasta_2026.append(f"{suma_2026:.2f}")
                            
                            if comp_val == "ACUMULADO":
                                if suma_2026 < pg_num:
                                    sugerencia = "🟢 Se sugiere Programación"
                                else:
                                    sugerencia = "🔴 Meta Cumplida (Prohibido aforar)"
                            else:
                                sugerencia = "🟢 Se sugiere Programación"
                                
                            list_sugerencia_poai.append(sugerencia)
                            
                            if cod_prod_word and cod_prod_pi and cod_prod_word == cod_prod_pi:
                                resultados_validacion.append("🟢 Corresponde al PI")
                                logs_diagnostico.append(f"✅ Fila {i} (Llave MP: {mp_llave_word}): Coincidencia exacta de indicador.")
                            else:
                                resultados_validacion.append("🔴 Código no coincide")
                                logs_diagnostico.append(f"❌ Fila {i} (Llave MP: {mp_llave_word}): Discrepancia. Word: '{cod_prod_word}' vs PI: '{cod_prod_pi}'.")

                    df_word["Cod Indicador Word"] = codigos_word_extraidos
                    df_word["Cod Indicador PI"] = codigos_pi_extraidos
                    df_word["Indicador en PI"] = textos_pi_encontrados
                    df_word["PG 2024-2027"] = list_pg
                    df_word["VAL ALC 2024"] = list_2024
                    df_word["VAL ALC 2025"] = list_2025
                    df_word["2026"] = list_2026
                    df_word["2027"] = list_2027
                    df_word["Acumulado a 2026"] = list_ejecutado_hasta_2026
                    df_word["COMPORTAMIENTO"] = list_comportamiento
                    df_word["Sugerencia POAI 2027"] = list_sugerencia_poai
                    df_word["Resultado Validación"] = resultados_validacion
                    
                    # Persistencia de auditoría
                    st.session_state["df_auditoria_pi_resultado"] = df_word
                    st.session_state["logs_diagnostico_pi"] = logs_diagnostico

            except Exception as e:
                st.error(f"❌ Error al ejecutar la validación con el Plan Indicativo: {e}")

    # ------------------------------------------------------------
    # 2. RENDERIZADO ÚNICO Y PERSISTENTE
    # ------------------------------------------------------------
    if "df_auditoria_pi_resultado" in st.session_state:
        df_res_pi = st.session_state["df_auditoria_pi_resultado"]
        
        st.warning("🛠️ **Consola de Diagnóstico: Comparación Indicador de Producto (Word) vs. PI**")
        with st.expander("👁️ Ver trazabilidad del cruce con el Plan Indicativo", expanded=False):
            st.code("\n".join(st.session_state.get("logs_diagnostico_pi", [])), language="text")
            
        def color_semaforo(val):
            val_str = str(val)
            if "🟢" in val_str:
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            elif "🔴" in val_str:
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            return "background-color: #fff3cd; color: #856404; font-weight: bold;"

        df_final_render = df_res_pi[[
            "Código MP", 
            "Cod Indicador Word",
            "Cod Indicador PI",
            "Resultado Validación",
            "PG 2024-2027",
            "VAL ALC 2024",
            "VAL ALC 2025",
            "2026",
            "Acumulado a 2026",
            "2027",
            "COMPORTAMIENTO",
            "Sugerencia POAI 2027"
        ]].copy()
        
        st.markdown("##### 📈 Reporte de Inconsistencias y Regla de Cumplimiento de Metas PI")
        st.dataframe(
            df_final_render.style.map(color_semaforo, subset=["Resultado Validación", "Sugerencia POAI 2027"]),
            use_container_width=True
        )
        
        conteo_alertas = df_res_pi["Resultado Validación"].str.contains("🔴").sum()
        conteo_meta_cumplida = df_res_pi["Sugerencia POAI 2027"].str.contains("🔴 Meta Cumplida").sum()
        
        if conteo_alertas > 0 or conteo_meta_cumplida > 0:
            st.error(f"⚠️ Se detectaron {conteo_alertas} discordancias de código y {conteo_meta_cumplida} meta(s) que ya alcanzaron cumplimiento antes de 2027.")
        else:
            st.success("🎉 ¡Validación correcta! Todos los indicadores corresponden al PI y están habilitados para asignación POAI 2027.")
else:
    st.info("💡 Primero carga el archivo Word para habilitar el cruce contra el Plan Indicativo.")
    
    
# ============================================================
# MÓDULO DE VERIFICACIÓN Z023: PROYECTOS VIGENCIA 2026
# ============================================================

st.markdown("---")
st.subheader("📦 Auditoría Z023: Proyectos Asociados a la Meta de Producto (Vigencia 2026)")

uploaded_z023 = st.file_uploader(
    "Carga el archivo Z023 Consolidado (.xlsm o .xlsx)", 
    type=["xlsm", "xlsx", "xls"], 
    key="z023_uploader"
)

if "df_indicadores_estandar" in st.session_state and not st.session_state["df_indicadores_estandar"].empty:
    df_word = st.session_state["df_indicadores_estandar"].copy()
    
    if uploaded_z023 is not None:
        if st.button("🚀 Analizar Proyectos Aportantes (Z023 - 2026)"):
            with st.spinner("⏳ Procesando Hoja1 de Z023, filtrando vigencia 2026 y agrupando proyectos..."):
                try:
                    df_z023 = pd.read_excel(uploaded_z023, sheet_name="Hoja1", engine="openpyxl")
                    columnas_z023 = {str(c).strip(): c for c in df_z023.columns}
                    
                    def buscar_columna(patron, diccionario_cols):
                        for c_limpia, c_real in diccionario_cols.items():
                            if patron.lower() in c_limpia.lower():
                                return c_real
                        return None

                    col_vigencia = buscar_columna("Vigencia", columnas_z023)
                    col_cod_mp = buscar_columna("Codigo Meta Producto", columnas_z023) or buscar_columna("Meta Producto", columnas_z023)
                    col_ppm_proj = buscar_columna("PPM: Proyecto", columnas_z023) or buscar_columna("Proyecto", columnas_z023)
                    col_desc_proj = buscar_columna("Descripción PROYECTO", columnas_z023) or buscar_columna("Descripcion", columnas_z023)
                    col_bpin = buscar_columna("Cod.BPIN DNP", columnas_z023) or buscar_columna("BPIN", columnas_z023)

                    if not (col_vigencia and col_cod_mp and col_ppm_proj and col_desc_proj):
                        st.error("🚨 No se encontraron todas las columnas requeridas en la 'Hoja1' del Z023.")
                    else:
                        df_z023_2026 = df_z023[df_z023[col_vigencia].astype(str).str.contains("2026", na=False)].copy()
                        
                        if df_z023_2026.empty:
                            st.warning("⚠️ El archivo Z023 no contiene registros para la vigencia 2026 en la 'Hoja1'.")
                        else:
                            dict_z023_proyectos = {}
                            
                            for _, fila in df_z023_2026.iterrows():
                                # Formateo con la letra 'V' concatenada
                                mp_key = extraer_codigo_numerico(fila[col_cod_mp], prefijo="V")
                                if not mp_key:
                                    continue
                                
                                ppm = str(fila[col_ppm_proj]).strip() if pd.notna(fila[col_ppm_proj]) else "S/C"
                                desc = str(fila[col_desc_proj]).strip() if pd.notna(fila[col_desc_proj]) else "Sin Descripción"
                                bpin = str(fila[col_bpin]).strip() if (col_bpin and pd.notna(fila[col_bpin])) else "No registra"

                                if mp_key not in dict_z023_proyectos:
                                    dict_z023_proyectos[mp_key] = {}

                                dict_z023_proyectos[mp_key][ppm] = {
                                    "PPM": ppm,
                                    "Descripcion": desc,
                                    "BPIN": bpin
                                }

                            conteo_proyectos = []
                            listado_codigos_ppm = []
                            resumen_detallado_proyectos = []
                            
                            for i, fila_word in df_word.iterrows():
                                mp_word_raw = fila_word.get("Código MP", "")
                                mp_key_word = extraer_codigo_numerico(mp_word_raw, prefijo="V")
                                
                                if mp_key_word in dict_z023_proyectos:
                                    proyectos_map = dict_z023_proyectos[mp_key_word]
                                    conteo_proyectos.append(len(proyectos_map))
                                    
                                    codigos_ppm = list(proyectos_map.keys())
                                    listado_codigos_ppm.append(", ".join(codigos_ppm))
                                    
                                    detalles = [
                                        f"• **[{p['PPM']}]** {p['Descripcion']}" + (f" *(BPIN: {p['BPIN']})*" if p['BPIN'] not in ["No registra", "nan", ""] else "")
                                        for p in proyectos_map.values()
                                    ]
                                    resumen_detallado_proyectos.append("\n".join(detalles))
                                else:
                                    conteo_proyectos.append(0)
                                    listado_codigos_ppm.append("Sin proyectos 2026")
                                    resumen_detallado_proyectos.append("🔴 No se registraron proyectos asociados en la vigencia 2026 (Z023).")

                            df_word["Variable MP"] = [extraer_codigo_numerico(r.get("Código MP", ""), prefijo="V") for _, r in df_word.iterrows()]
                            df_word["Cant. Proyectos (2026)"] = conteo_proyectos
                            df_word["Códigos PPM"] = listado_codigos_ppm
                            df_word["Detalle Proyectos Z023"] = resumen_detallado_proyectos
                            
                            # Persistencia de auditoría Z023 en sesión
                            st.session_state["df_z023_resultado"] = df_word.copy()

                except Exception as e:
                    st.error(f"❌ Error al procesar la 'Hoja1' del archivo Z023: {e}")
    else:
        st.info("📌 Carga el archivo **Z023 Consolidado** para ejecutar el análisis de proyectos 2026.")
    
    # RENDERIZADO PERSISTENTE DE Z023 CON DESPLEGABLES INTERACTIVOS
    if "df_z023_resultado" in st.session_state and not st.session_state["df_z023_resultado"].empty:
        st.markdown("##### 📊 Consolidado de Proyectos Aportantes a Metas de Producto (2026)")
        
        df_resultados = st.session_state["df_z023_resultado"]
        
        df_resumen_tabla = df_resultados[[
            "Código MP",
            "Variable MP", 
            "Cant. Proyectos (2026)", 
            "Códigos PPM"
        ]].copy()
        
        st.dataframe(
            df_resumen_tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Código MP": st.column_config.TextColumn("Código MP", width="small"),
                "Variable MP": st.column_config.TextColumn("Variable MP", width="small"),
                "Cant. Proyectos (2026)": st.column_config.NumberColumn("Cant. Proyectos", width="small"),
                "Códigos PPM": st.column_config.TextColumn("Códigos PPM", width="medium")
            }
        )
        
        st.markdown("---")
        st.markdown("##### 🔍 Desglose Detallado por Meta de Producto (Acordeones Interactivos)")

        # Desglose interactivo por Meta de Producto mediante st.expander
        for idx, fila in df_resultados.iterrows():
            codigo_mp = fila.get("Código MP", f"Meta {idx+1}")
            cant_p = fila.get("Cant. Proyectos (2026)", 0)
            ppms = fila.get("Códigos PPM", "Sin proyectos")
            detalle_txt = fila.get("Detalle Proyectos Z023", "")
            
            # Formato de la cabecera del expander
            if cant_p > 0:
                label_expander = f"🟢 [{codigo_mp}] — {cant_p} Proyecto(s) Aportante(s) | PPM: {ppms}"
            else:
                label_expander = f"🔴 [{codigo_mp}] — Sin proyectos asignados para 2026"
                
            with st.expander(label_expander, expanded=False):
                if cant_p > 0:
                    lineas = detalle_txt.split("\n")
                    for l in lineas:
                        if l.strip():
                            st.markdown(l)
                else:
                    st.warning("No se registraron proyectos asociados en la vigencia 2026 dentro del archivo Z023.")

        # Resumen global de alertas para Z023
        sin_proyectos = (df_resultados["Cant. Proyectos (2026)"] == 0).sum()
        if sin_proyectos > 0:
            st.warning(f"⚠️ Hay {sin_proyectos} Meta(s) de Producto del Word que NO presentan proyectos en la vigencia 2026 del Z023.")
        else:
            st.success("🎉 Todas las Metas de Producto del Word cuentan con al menos un proyecto asignado en la vigencia 2026.")
else:
    st.info("💡 Carga el archivo Word en la sección principal para habilitar el cruce con Z023.")

# ============================================================
# GENERACIÓN DE PROMPT INTEGRADO Y ENLACES A CHATGPT / GEMINI (POAI 2027)
# ============================================================

st.markdown("---")
st.subheader("🤖 Generación de Prompt AI para Análisis POAI 2027")

# Verificamos la carga general del documento sin supeditarlo a la Tabla 5
if "texto_word_extraido" in st.session_state or ("df_indicadores_estandar" in st.session_state and not st.session_state["df_indicadores_estandar"].empty):
    
    # Extraer metadatos de sesión (con valores por defecto en caso de no encontrarse)
    nombre_proyecto = st.session_state.get("proyecto_nombre_tabla", "No detectado en tabla (Revisar adjunto)")
    codigo_pi = st.session_state.get("metadatos", {}).get("codigo_pi", "No detectado")
    bpin = st.session_state.get("metadatos", {}).get("bpin", "No detectado")
    total_recursos = st.session_state.get("total_presupuesto_poai", "$0")
    
    # Formatear actividades si existen en la sesión
    lineas_actividades = []
    if "df_poai_estandar" in st.session_state and not st.session_state["df_poai_estandar"].empty:
        df_poai_prompt = st.session_state["df_poai_estandar"].copy()
        for idx, fila in df_poai_prompt.iterrows():
            cod_mp = fila.get("COD. META DE PRODUCTO", "S/C")
            prod_mga = fila.get("PRODUCTO MGA (COD+TEXTO)", "S/N")
            actividad = fila.get("ACTIVIDAD DEL PROYECTO", "S/N")
            recurso = fila.get("RECURSO TOTAL 2027", "$0")
            
            lineas_actividades.append(
                f"  * [Meta: {cod_mp}] | Producto MGA: {prod_mga} | Actividad: {actividad} | Asignación 2027: {recurso}"
            )
    
    if lineas_actividades:
        bloque_actividades_txt = "\n".join(lineas_actividades)
    else:
        bloque_actividades_txt = "(No se estructuraron actividades automáticamente desde la Tabla 5. Por favor revisar/pegar el contenido del documento Word adjunto)."
    
    # Construcción completa del prompt
    prompt_poai = f"""Actúa como un experto en Planeación Pública, Formulación de Proyectos de Inversión (Metodología MGA) y Presupuesto Público.

Tu tarea es revisar de manera exhaustiva la "Cadena de Valor" y el documento técnico para la radicación inicial de un proyecto de inversión. Tu evaluación debe ser estricta, objetiva y estructurada.

A continuación, te proporcionaré los datos del proyecto y los soportes. Debes analizar la información y entregar un informe de revisión evaluando los siguientes 4 criterios, indicando claramente qué cumple, qué no cumple y qué debe ajustarse:

DATOS DEL PROYECTO
- Nombre del Proyecto: {nombre_proyecto}
- Código PS-SAP / PI: {codigo_pi}
- Código BPIN: {bpin}
- Presupuesto Total POAI 2027: {total_recursos}

ACTIVIDADES Y RECURSOS PROGRAMADOS (POAI 2027):
{bloque_actividades_txt}

CRITERIOS DE EVALUACIÓN:

1. Alineación Estratégica, Programática y Articulación
- Articulación Perfecta: Verifica que exista una articulación exacta entre la cadena de valor del proyecto y la del Plan de Desarrollo (productos asociados, indicador exacto, y forma de acumulación idéntica).
- REGLA DE ORO (Tercer Año de Gobierno): Revisa y pega en tu respuesta el estado actual de la meta. Si la meta está "cerrada" o está programada para cerrarse/cumplirse totalmente en 2026, ESTÁ ESTRICTAMENTE PROHIBIDO aforar recursos para la vigencia 2027.
- Observación de Indicadores (Obligatorio): Debes verificar que se indique expresamente si la meta se cumple con recursos de gestión, de Regalías u otro proyecto de inversión, y especificar numéricamente cuánto aporta cada fuente.
- Reglas de Programación POAI 2027: Es indispensable programar recursos para metas de SERVICIOS (capacitación, asistencia técnica, documentos de planeación, servicios de orientación, difusión, etc.) que se pueden cumplir con prestación de servicios para el POAI 2027, siempre que la meta esté programada para ese año. Distinguir claramente esto de las metas de "apoyo financiero" o "entrega de bienes", las cuales solo se cumplen con la entrega efectiva de los mismos que sea coherente con el PPI aprobado.
*(Si no puedes leer en el archivo Word la programación de la meta PI, pide que te copien el dato para que valides la programación).*

2. Coherencia Lógica y Sintaxis de Actividades
- Lógica de la cadena de valor: Verifica que la sumatoria y ejecución de las actividades conduzcan ineludiblemente a la obtención del producto.
- Sintaxis obligatoria: Revisa que todas las actividades comiencen con un verbo fuerte en infinitivo y expresen una acción concreta y medible.
- Nivel estratégico: Las actividades deben ser "estratégicas". Rechaza actividades que sean simples "tareas" operativas o que estén redactadas como "objetos del gasto" diseñados exclusivamente para justificar una contratación (ej. "Comprar computadores").
- Longitud adecuada: La redacción de la actividad no debe ser un párrafo extenso y confuso, pero tampoco una frase tan corta que carezca de contexto. Debe ser precisa.
*(Si no puedes leer los documentos pide que te peguen los textos para que puedas validar).*

3. Evaluación de las Justificaciones
3.1. Justificación Técnica indicada para proyectos POAI:
- Debe identificar la importancia de ejecutar el proyecto para el cumplimiento del Plan de Desarrollo y las acciones estratégicas que se cumplirán.
- Obligatorio: Indicar numéricamente con cuánto contribuye el proyecto al alcance de la meta o metas de producto.
- Si la contribución del proyecto no es igual al 100% de lo programado en la vigencia, debe especificar si existen otros proyectos complementarios y cuánto aportan.
- Debe concluir si es necesario reprogramar la meta. En caso de no requerirlo (a pesar de haber brechas), debe existir una justificación técnica contundente de por qué no se reprograma.
- Justificación Financiera: Debe presentar la trazabilidad financiera indicando: Meta -> Producto -> Actividades -> Valores asignados. Si el proyecto desglosa las tareas que componen cada actividad, estas deben estar costeadas y justificadas aquí.
- Checklist de Soportes Obligatorios: Confirma que el documento hace referencia o cuenta con los anexos obligatorios para la radicación: Documento MGA (solo radicación inicial o actualización POAI), Presupuesto detallado

FORMATO DE SALIDA ESPERADO:
- Entrega tu revisión utilizando viñetas y separando el análisis por cada uno de los 4 bloques mencionados.
- Usa negritas para resaltar las [Aprobaciones] o los [Hallazgos/Errores] encontrados.
- Debes redactar el Visto Bueno respetando las siguientes pautas:
  
  * Estructura del Visto Bueno: indicar el trámite, el valor, la fuente, la meta de producto asociada (código y descripción),breve resumen de la importancia del trámite y su aporte al Plan de Desarrollo, y los documentos soporte.
  * Conclusión obligatoria: debe incluir la salvedad de que "es responsabilidad de la dependencia [Nombre Dependencia] realizar los trámites respectivos para culminar el trámite y su correcta ejecución, y que el visto bueno otorgado por la Subdirección de Ordenamiento y Desarrollo Regional se suscribe a verificar la correcta alineación de la cadena de valor del Plan de Desarrollo con la cadena de valor del proyecto, y su contribución a la implementación del Plan de Desarrollo"."""

    # 📋 Paso 1: Bloque de copiado rápido
    st.markdown("🚀 **Paso 1:** Copia el prompt generado a continuación:")
    st.code(prompt_poai, language="markdown", wrap_lines=True)

    st.markdown("---")
    
    # 🚀 Paso 2: Botones de enlace rápido
    st.markdown("🚀 **Paso 2:** Ve directo a la Inteligencia Artificial a pegar tu prompt:")
    
    col_gem, col_gpt = st.columns(2)
    with col_gem:
        st.link_button("🌐 Ir a Google Gemini Web", "https://gemini.google.com/", use_container_width=True, type="primary")
    with col_gpt:
        st.link_button("💬 Ir a ChatGPT (Alternativo)", "https://chatgpt.com/", use_container_width=True)

else:
    st.info("💡 Carga un archivo Word en la parte superior para generar automáticamente el prompt con los datos del proyecto.")
