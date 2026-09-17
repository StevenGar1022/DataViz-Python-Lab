"""
Proyecto Final - Data Analytics Lab
"Análisis y presentación de datos utilizando APIs en Python"

Aplicación Streamlit que consulta datos abiertos del gobierno de Chile
(https://datos.gob.cl) a través de su API REST, usando
exclusivamente peticiones GET, permite explorar, analizar y visualizar
la información de forma interactiva.

Librerías usadas: requests, json (vía response.json()), pandas, matplotlib,
streamlit.

"""

import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Configuración general

API_BASE = "https://datos.gob.cl/api/3/action"

# Algunas búsquedas sugeridas dentro del catálogo de datos.gob.cl.
# El usuario puede escribir cualquier otro término en el campo de búsqueda.
BUSQUEDAS_SUGERIDAS = [
    "ejecucion presupuestaria",
    "precipitaciones",
    "vacunacion",
    "empleo",
    "educacion superior",
]

st.set_page_config(
    page_title="Data Analytics Lab",
    page_icon="📊",
    layout="wide",
)

# Funciones de acceso a la API (requests + json)

@st.cache_data(show_spinner=False, ttl=3600)
def buscar_datasets(termino: str, filas: int = 15) -> list:
    """Busca conjuntos de datos en datos.gob.cl mediante GET.

    """
    url = f"{API_BASE}/package_search"
    params = {"q": termino, "rows": filas}
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()  # equivalente a json.loads(resp.text)
    if not data.get("success"):
        return []
    return data["result"]["results"]


@st.cache_data(show_spinner=False, ttl=3600)
def contar_registros_recurso(resource_id: str) -> int:
    """Cuenta la cantidad de registros de un recurso publicado en el
    DataStore de CKAN, usando el endpoint 'datastore_search'.
    """
    url = f"{API_BASE}/datastore_search"
    params = {"resource_id": resource_id, "limit": 0}
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException:
        return 0
    if not data.get("success"):
        return 0
    return data["result"].get("total", 0)


@st.cache_data(show_spinner=False, ttl=3600)
def obtener_recursos_con_datos(dataset: dict) -> list:
    """Filtra, de un dataset, sólo los recursos que tienen 'datastore_active'
    en True Y que además tienen al menos un registro real, es decir, los
    que se pueden consultar y analizar como tabla vía API. Devuelve una
    lista de tuplas (recurso, total_registros) ordenada de mayor a menor
    cantidad de registros.
    """
    recursos = dataset.get("resources", [])
    candidatos = [r for r in recursos if r.get("datastore_active")]

    con_datos = []
    for r in candidatos:
        total = contar_registros_recurso(r["id"])
        if total > 0:
            con_datos.append((r, total))

    con_datos.sort(key=lambda par: par[1], reverse=True)
    return con_datos


@st.cache_data(show_spinner=False, ttl=3600)
def descargar_datos_recurso(resource_id: str, limite_maximo: int = 5000) -> pd.DataFrame:
    """Descarga (paginando) los registros de un recurso publicado en el
    DataStore de CKAN, usando el endpoint 'datastore_search'.
    """
    url = f"{API_BASE}/datastore_search"
    registros = []
    offset = 0
    tamano_pagina = 500

    while True:
        params = {"resource_id": resource_id, "limit": tamano_pagina, "offset": offset}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            break

        nuevos = data["result"]["records"]
        if not nuevos:
            break

        registros.extend(nuevos)
        offset += tamano_pagina

        if len(registros) >= limite_maximo or len(registros) >= data["result"].get("total", 0):
            break

    df = pd.DataFrame(registros)
    # La columna interna de CKAN no aporta valor analítico
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    return df


# Interfaz

st.title("📊 Análisis y presentación de resultados")
st.caption(
    "Fuente: portal de datos abiertos del Estado de Chile — "
    "[datos.gob.cl](https://datos.gob.cl/group)."
)

with st.sidebar:
    st.header("1. Buscar conjunto de datos")
    termino = st.selectbox(
        "Elige una búsqueda sugerida",
        options=BUSQUEDAS_SUGERIDAS,
        index=0,
    )
    termino_libre = st.text_input("...o escribe tu propia búsqueda", value="")
    termino_final = termino_libre.strip() if termino_libre.strip() else termino

    buscar = st.button("Buscar en datos.gob.cl", type="primary")

if "datasets" not in st.session_state:
    st.session_state["datasets"] = []

if buscar or not st.session_state["datasets"]:
    try:
        with st.spinner("Consultando la API de datos.gob.cl..."):
            st.session_state["datasets"] = buscar_datasets(termino_final)
    except requests.exceptions.RequestException as e:
        st.error(f"No fue posible conectar con la API: {e}")
        st.session_state["datasets"] = []

datasets = st.session_state["datasets"]

if not datasets:
    st.info("No se encontraron conjuntos de datos para esa búsqueda. Prueba con otro término.")
    st.stop()

#  Selección de dataset 
titulos = [d.get("title", "(sin título)") for d in datasets]
idx_dataset = st.sidebar.selectbox(
    "2. Elige un conjunto de datos",
    options=range(len(titulos)),
    format_func=lambda i: titulos[i],
)
dataset_elegido = datasets[idx_dataset]

st.subheader(dataset_elegido.get("title", ""))
st.write(dataset_elegido.get("notes", "Sin descripción disponible.")[:600])

with st.spinner("Verificando qué recursos tienen datos disponibles..."):
    recursos_con_datos = obtener_recursos_con_datos(dataset_elegido)

if not recursos_con_datos:
    st.warning(
        "Este conjunto de datos no tiene, por ahora, recursos con datos "
        "reales consultables vía API (aunque figuren como 'datastore_active', "
        "pueden estar vacíos). Elige otro conjunto de datos en el panel lateral."
    )
    st.stop()

nombres_recursos = [
    f"{(r.get('name') or r.get('id'))}  —  {total:,} registros"
    for r, total in recursos_con_datos
]
idx_recurso = st.sidebar.selectbox(
    "3. Elige el recurso (tabla) a analizar",
    options=range(len(nombres_recursos)),
    format_func=lambda i: nombres_recursos[i],
)
recurso_elegido, total_recurso = recursos_con_datos[idx_recurso]

with st.spinner("Descargando datos desde la API (datastore_search)..."):
    try:
        df = descargar_datos_recurso(recurso_elegido["id"])
    except requests.exceptions.RequestException as e:
        st.error(f"Error al descargar los datos: {e}")
        st.stop()

if df.empty:
    st.warning("El recurso no devolvió registros.")
    st.stop()

st.success(f"Se obtuvieron {len(df):,} registros y {df.shape[1]} columnas.")

#  Análisis de datos con pandas

st.header("Exploración y filtros")

def _es_columna_numerica(serie: pd.Series, umbral: float = 0.8) -> bool:
    """Considera una columna 'numérica' si al menos 'umbral' de sus valores
    no nulos se pueden convertir a número.
    """
    no_nulos = serie.dropna()
    if no_nulos.empty:
        return False
    convertidos = pd.to_numeric(no_nulos, errors="coerce")
    return convertidos.notna().mean() >= umbral


columnas = list(df.columns)
columnas_numericas = [c for c in columnas if _es_columna_numerica(df[c])]
columnas_categoricas = [c for c in columnas if c not in columnas_numericas]

col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.markdown("**Filtrar por columna categórica**")
    df_filtrado = df.copy()
    if columnas_categoricas:
        col_filtro = st.selectbox("Columna", options=["(ninguna)"] + columnas_categoricas)
        if col_filtro != "(ninguna)":
            valores = sorted(df[col_filtro].dropna().astype(str).unique().tolist())
            seleccion = st.multiselect("Valores a incluir", options=valores, default=valores[:10])
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col_filtro].astype(str).isin(seleccion)]
    else:
        st.caption("No se detectaron columnas categóricas.")

with col_der:
    st.markdown("**Vista previa de los datos filtrados**")
    st.dataframe(df_filtrado.head(200), use_container_width=True)

st.download_button(
    " Descargar datos filtrados (CSV)",
    data=df_filtrado.to_csv(index=False).encode("utf-8"),
    file_name="datos_filtrados.csv",
    mime="text/csv",
)

# Presentación de resultados: gráficos con matplotlib

st.header("Visualización")

if columnas_numericas:
    col_num = st.selectbox("Columna numérica a graficar", options=columnas_numericas)
    serie = pd.to_numeric(df_filtrado[col_num], errors="coerce").dropna()

    tab1, tab2 = st.tabs(["Histograma", "Top categorías (si aplica)"])

    with tab1:
        fig, ax = plt.subplots()
        ax.hist(serie, bins=20, color="#4C72B0", edgecolor="white")
        ax.set_xlabel(col_num)
        ax.set_ylabel("Frecuencia")
        ax.set_title(f"Distribución de {col_num}")
        st.pyplot(fig)

    with tab2:
        if columnas_categoricas:
            col_cat = st.selectbox("Agrupar por", options=columnas_categoricas, key="agrupar_por")
            resumen = (
                df_filtrado.assign(**{col_num: serie})
                .groupby(col_cat)[col_num]
                .sum(numeric_only=True)
                .sort_values(ascending=False)
                .head(15)
            )
            fig2, ax2 = plt.subplots()
            resumen.plot(kind="bar", ax=ax2, color="#55A868")
            ax2.set_ylabel(f"Suma de {col_num}")
            ax2.set_title(f"{col_num} por {col_cat} (top 15)")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig2)
        else:
            st.caption("No hay columnas categóricas para agrupar.")
else:
    st.info("El recurso no tiene columnas numéricas para graficar automáticamente.")

st.markdown("---")
st.caption(
    "Datos obtenidos en tiempo real mediante  la API pública "
    "de datos.gob.cl."
)