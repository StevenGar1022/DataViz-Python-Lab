# DataViz-Python-Lab

# Proyecto Final — DataViz Python Lab
### "Análisis y presentación de datos utilizando APIs en Python"

Aplicación web en **Streamlit** que consulta datos abiertos del Estado de Chile
publicados en **[datos.gob.cl](https://datos.gob.cl/group)**, usando su API REST
(basada en CKAN) exclusivamente mediante peticiones **GET**.

## ¿Cómo funciona?

1. **Búsqueda (`requests` + `json`)**: el usuario elige o escribe un término
   (por ejemplo *"ejecucion presupuestaria"*, *"precipitaciones"*,
   *"vacunacion"*) y la app llama al endpoint `package_search` del API de
   CKAN para listar los conjuntos de datos (*datasets*) disponibles sobre ese
   tema.
2. **Selección de recurso**: de cada dataset se filtran sólo los recursos que
   tienen `datastore_active = true`, es decir, los que CKAN permite consultar
   como tabla estructurada vía API (no solo descargar el archivo).
3. **Descarga de datos (`datastore_search`)**: se pagina la consulta GET al
   endpoint `datastore_search` hasta reunir los registros del recurso, y se
   cargan en un **DataFrame de pandas**.
4. **Análisis y filtros**: se detectan automáticamente columnas numéricas y
   categóricas, se permite filtrar por categoría y descargar el subconjunto
   filtrado en CSV.
5. **Visualización (`matplotlib` embebido en Streamlit)**: histograma de la
   columna numérica elegida y gráfico de barras agrupado por una columna
   categórica (top 15).

## Requisitos técnicos cumplidos

- Lenguaje: Python.
- Librerías: `requests`, `json` (vía `response.json()`), `pandas`,
  `matplotlib`, `streamlit`.
- Fuente de datos: API REST pública de `datos.gob.cl`, consultada solo con
  método **GET** (`package_search` y `datastore_search`).
- Conjunto de datos: de libre elección — el buscador integrado permite
  explorar cualquier tema publicado en el portal (económicos, salud,
  climáticos, etc.) sin modificar el código.
- Interfaz web interactiva desarrollada con **Streamlit**, con filtros y
  gráficos dinámicos.

## Instalación y ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Luego abre en el navegador la URL que indica la terminal (por defecto
`http://localhost:8501`).

## Notas para completar antes de entregar

- Reemplazar en el encabezado de `app.py` el nombre y apellido de los
  integrantes del grupo.
- Si se despliega la app (por ejemplo en Streamlit Community Cloud), incluir
  el enlace público en la entrega, como pide la pauta.
- El código requiere conexión a Internet para consultar `datos.gob.cl` en
  tiempo real; no incluye datos de respaldo "offline" porque el enunciado
  exige que la obtención sea siempre vía API (GET).
