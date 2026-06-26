# CONFIG.md

Guía de parametrización y reutilización del proyecto `Analisis_Hospitalario`.

Este documento explica qué controla `backend/config.py` y qué otros archivos deben modificarse cuando se adapta el pipeline REM20 a otra fuente de datos, otro esquema PostgreSQL o nuevos artefactos procesados.

## Configuración central: `backend/config.py`

`backend/config.py` concentra los nombres lógicos usados por el backend para evitar literales repartidos en consultas, rutas y endpoints.

### `SCHEMA`

Nombre del esquema PostgreSQL donde viven la tabla principal y las vistas analíticas.

Valor actual:

```python
SCHEMA = "rem20"
```

Cambiarlo si la base nueva usa otro esquema, por ejemplo uno propio para otro proyecto o dominio de datos.

### `TABLE_INDICADORES`

Nombre de la tabla principal de indicadores.

Valor actual:

```python
TABLE_INDICADORES = "indicadores"
```

Debe coincidir con la tabla creada en `sql/ddl/02_create_tables.sql`.

### `VIEW_EVOLUCION_MENSUAL`

Nombre de la vista que alimenta la evolución mensual de indicadores.

Valor actual:

```python
VIEW_EVOLUCION_MENSUAL = "v_evolucion_mensual"
```

Debe existir en `sql/ddl/03_create_views.sql` y entregar los campos esperados por `backend/queries.py` y el dashboard.

### `VIEW_RANKING`

Nombre de la vista usada para rankings de establecimientos.

Valor actual:

```python
VIEW_RANKING = "v_ranking_establecimientos"
```

Debe mantenerse alineada con los endpoints que consultan rankings y con los componentes del frontend que los visualizan.

### `VIEW_LETALIDAD_AREA`

Nombre de la vista usada para análisis de letalidad por área.

Valor actual:

```python
VIEW_LETALIDAD_AREA = "v_letalidad_por_area"
```

Cambiarla solo si se renombra o rediseña la vista correspondiente en el DDL.

### Nombres completamente calificados

El archivo también construye nombres `esquema.objeto` para las consultas SQL:

```python
TABLA_INDICADORES = f"{SCHEMA}.{TABLE_INDICADORES}"
VISTA_EVOLUCION_MENSUAL = f"{SCHEMA}.{VIEW_EVOLUCION_MENSUAL}"
VISTA_RANKING = f"{SCHEMA}.{VIEW_RANKING}"
VISTA_LETALIDAD_AREA = f"{SCHEMA}.{VIEW_LETALIDAD_AREA}"
```

Normalmente no se editan directamente. Se actualizan solos al cambiar `SCHEMA`, `TABLE_INDICADORES` o las constantes `VIEW_*`.

### `PREDICCIONES_CSV`

Ruta al CSV procesado con predicciones.

Valor actual:

```python
PREDICCIONES_CSV = DATA_PROCESSED_DIR / "rem20_predicciones_2026.csv"
```

Cambiar si el modelo genera otro nombre de archivo, otro periodo o una estructura distinta de salida.

### `CLUSTERS_CSV`

Ruta al CSV procesado con clusters.

Valor actual:

```python
CLUSTERS_CSV = DATA_PROCESSED_DIR / "clusters.csv"
```

Cambiar si se modifica el nombre del archivo de clustering o si se reemplaza por otro artefacto equivalente.

### `FRONTEND_DIR`

Ruta del frontend servido por FastAPI.

Valor actual:

```python
FRONTEND_DIR = PROJECT_ROOT / "frontend"
```

Modificar solo si se mueve el dashboard a otra carpeta.

### `DEFAULT_PERIODO_RANKING`

Año usado por defecto en endpoints de ranking cuando no se informa un periodo.

Valor actual:

```python
DEFAULT_PERIODO_RANKING = 2025
```

Actualizar si el análisis base cambia de año de referencia.

### `REQUIRED_ENV_VARS`

Lista de variables obligatorias para conectar a PostgreSQL desde `.env`.

Valor actual:

```python
REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
```

Estas variables deben existir en `.env`. La plantilla pública está en `.env.example` y no debe contener secretos reales.

## Qué cambiar para adaptar el proyecto a otra fuente de datos

### 1. DDL de PostgreSQL

Editar:

- `sql/ddl/02_create_tables.sql`
- `sql/ddl/03_create_views.sql`

Ahí se define la estructura de la tabla principal y las vistas analíticas. Si cambian columnas, tipos de dato, nombres de campos o llaves, estos archivos deben ser el primer punto de ajuste.

### 2. Carga del CSV de origen

Editar:

- `python/scripts/01_load_data.py`

Este script debe reflejar las columnas esperadas del CSV crudo, el mapeo hacia la tabla PostgreSQL y cualquier transformación necesaria antes de insertar los datos.

### 3. Configuración del backend

Editar:

- `backend/config.py`

Ajustar `SCHEMA`, `TABLE_INDICADORES`, `VIEW_EVOLUCION_MENSUAL`, `VIEW_RANKING`, `VIEW_LETALIDAD_AREA`, `PREDICCIONES_CSV`, `CLUSTERS_CSV` y, si corresponde, `DEFAULT_PERIODO_RANKING`.

### 4. Consultas de API

Editar:

- `backend/queries.py`

Si las vistas devuelven campos distintos, si cambian nombres de columnas o si se agregan nuevas métricas, las consultas del backend deben actualizarse para mantener contratos claros con la API.

### 5. Dashboard

Editar:

- `frontend/dashboard.js`

Si cambian los campos devueltos por los endpoints, también deben cambiar los nombres consumidos por Plotly.js y las transformaciones del frontend.

## Checklist de reutilización

Antes de ejecutar el pipeline con otra base de datos:

- Confirmar que `.env` contiene `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Crear o ajustar la tabla principal en `sql/ddl/02_create_tables.sql`.
- Crear o ajustar las vistas en `sql/ddl/03_create_views.sql`.
- Adaptar `python/scripts/01_load_data.py` al CSV de origen.
- Actualizar constantes en `backend/config.py`.
- Revisar `backend/queries.py` si cambian campos o métricas.
- Revisar `frontend/dashboard.js` si cambian las respuestas de la API.
- Regenerar artefactos procesados si cambian predicciones, clusters, gráficos o informe.

## Alcance

`CONFIG.md` documenta parametrización y puntos de reutilización. Para instalación, reproducción completa y contexto del estudio, ver [README.md](README.md).
