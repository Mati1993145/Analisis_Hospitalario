# 📊 Conexión Power BI Desktop ↔ PostgreSQL (rem20_db) y construcción del dashboard

> Guía paso a paso para el Análisis Hospitalario REM20 (MINSAL, 2014–2026).
> Fuente de datos: 4 vistas analíticas del schema `rem20` + CSV de predicciones 2026.

## 0. Encabezado y propósito

Este documento guía la construcción manual de un dashboard en Power BI Desktop conectado a la base PostgreSQL `rem20_db`, schema `rem20`, usando cuatro vistas agregadas y un archivo CSV de predicciones 2026.

El dashboard tendrá 4 páginas:

1. Resumen Ejecutivo Nacional.
2. Efecto COVID.
3. Análisis por Establecimiento y Clusters.
4. Predicciones 2026.

Prerrequisitos:

1. PostgreSQL corriendo en Windows.
2. Base de datos `rem20_db` cargada.
3. Schema `rem20` creado.
4. Vistas creadas:
   - `rem20.v_resumen_anual`
   - `rem20.v_evolucion_mensual`
   - `rem20.v_ranking_establecimientos`
   - `rem20.v_letalidad_por_area`
5. Power BI Desktop instalado.
6. Archivo disponible:
   - `data/processed/rem20_predicciones_2026.csv`

## 1. Instalar driver Npgsql

1. Abrir el navegador y entrar a:
   - <https://github.com/npgsql/npgsql/releases>
2. Descargar la versión más reciente marcada como `Latest`.
3. Descargar el instalador `.msi`.
4. No descargar el paquete `.nupkg`, porque ese formato es para uso desde proyectos .NET.
5. Ejecutar el `.msi`.
6. Durante la instalación, seleccionar la opción que registra el driver en el GAC.
7. Finalizar la instalación.
8. Reiniciar el equipo antes de abrir Power BI Desktop.

## 2. Conectar desde Power BI Desktop

1. Abrir Power BI Desktop.
2. Ir a `Inicio` -> `Obtener datos` -> `Más`.
3. Seleccionar `Base de datos` -> `Base de datos de PostgreSQL`.
4. Completar los datos de conexión:
   - Servidor: `localhost`
   - Alternativa si se requiere puerto explícito: `localhost:5432`
   - Base de datos: `rem20_db`
   - Modo de conectividad de datos: `Importar`
5. No usar `DirectQuery` para este dashboard, ya que las vistas y el CSV se trabajarán como modelo importado.
6. En credenciales, seleccionar la pestaña `Base de datos`.
7. Ingresar el usuario y la contraseña de PostgreSQL.
8. En nivel de privacidad, se puede dejar `Organizacional`.

> Nota de seguridad: este documento no incluye credenciales reales. El usuario debe ingresarlas directamente en el diálogo de Power BI Desktop.

## 3. Seleccionar las 4 vistas

1. En el `Navegador`, expandir el schema `rem20`.
2. Marcar estas cuatro vistas:
   - `v_resumen_anual`
   - `v_evolucion_mensual`
   - `v_ranking_establecimientos`
   - `v_letalidad_por_area`
3. Si Power BI muestra el botón `Seleccionar elementos relacionados`, usarlo solo si ayuda a marcar las vistas necesarias.
4. Presionar `Transformar datos`.
5. No presionar `Cargar` directamente, porque primero se deben revisar tipos y crear columnas en Power Query.

## 4. Transformaciones en Power Query

Aplicar las siguientes transformaciones en Power Query, según corresponda a cada consulta.

1. Convertir `periodo` desde número entero a tipo `Texto`.
   - Esto permite usar `periodo` como filtro categórico y segmentador.
   - Aplicar en:
     - `v_resumen_anual`
     - `v_evolucion_mensual`
     - `v_ranking_establecimientos`
     - `v_letalidad_por_area`

2. En `v_evolucion_mensual`, crear una columna personalizada llamada `ANIO_MES`.

   Fórmula M:

   ```powerquery
   = Text.From([periodo]) & "-" & Text.PadStart(Text.From([mes]), 2, "0")
   ```

3. Reemplazar valores nulos en columnas numéricas por `0`.
   - Usar `Transformar` -> `Reemplazar valores`.
   - Esto aplica a métricas agregadas como:
     - `indice_ocupacional_prom`
     - `promedio_dias_estada_prom`
     - `letalidad_prom`
     - `indice_rotacion_prom`
     - `numero_egresos`
     - `egresos_fallecidos`
     - `idx_ocup_prom`
     - `letalidad_pct`

4. Verificar tipos de datos:
   - Métricas: decimal o número entero según corresponda.
   - `periodo`: texto.
   - `mes`: número entero en `v_evolucion_mensual`.
   - `ranking`: número entero en `v_ranking_establecimientos`.
   - `codigo_establecimiento`: texto o número entero, pero debe ser consistente entre tablas relacionadas.

5. Presionar `Cerrar y aplicar`.

## 5. Importar predicciones

1. En Power BI Desktop, ir a `Inicio` -> `Obtener datos` -> `Texto/CSV`.
2. Seleccionar el archivo:
   - `data/processed/rem20_predicciones_2026.csv`
3. En el diálogo de importación, configurar:
   - `Origen de archivo`: `65001: Unicode (UTF-8)`
   - Delimitador: `Punto y coma`
4. Confirmar que los acentos se visualicen correctamente.
5. Cargar la tabla con el nombre:
   - `Predicciones2026`

Columnas esperadas en `Predicciones2026`:

1. `PERIODO`
2. `MES`
3. `CODIGO_ESTABLECIMIENTO`
4. `ESTABLECIMIENTO`
5. `AREA_FUNCIONAL`
6. `INDICE_OCUPACIONAL_PREDICHO`
7. `VALOR_REAL`

## 6. Modelo de relaciones

Esta sección es crítica. Las vistas están agregadas a granos distintos, por lo que relacionarlas directamente entre sí puede crear relaciones muchos-a-muchos ambiguas.

La práctica correcta en Power BI es crear tablas dimensión y armar un esquema estrella.

### 6.1 Crear `Dim_Periodo`

1. Ir a `Modelado` -> `Nueva tabla`.
2. Crear la tabla calculada:

```DAX
Dim_Periodo =
DISTINCT(
    UNION(
        VALUES(v_resumen_anual[periodo]),
        VALUES(v_evolucion_mensual[periodo]),
        VALUES(v_ranking_establecimientos[periodo]),
        VALUES(v_letalidad_por_area[periodo])
    )
)
```

3. Relacionar:
   - `Dim_Periodo[periodo]` lado `1` con `v_resumen_anual[periodo]` lado muchos.
   - `Dim_Periodo[periodo]` lado `1` con `v_evolucion_mensual[periodo]` lado muchos.
   - `Dim_Periodo[periodo]` lado `1` con `v_ranking_establecimientos[periodo]` lado muchos.
   - `Dim_Periodo[periodo]` lado `1` con `v_letalidad_por_area[periodo]` lado muchos.

Así, `periodo` conecta todas las vistas sin ambigüedad.

### 6.2 Crear `Dim_Establecimiento`

`Dim_Establecimiento` debe crearse desde `v_ranking_establecimientos`, porque esa vista sí contiene `codigo_establecimiento` y `establecimiento`.

1. Ir a `Modelado` -> `Nueva tabla`.
2. Crear la tabla calculada:

```DAX
Dim_Establecimiento =
DISTINCT(
    SELECTCOLUMNS(
        v_ranking_establecimientos,
        "codigo_establecimiento", v_ranking_establecimientos[codigo_establecimiento],
        "establecimiento", v_ranking_establecimientos[establecimiento]
    )
)
```

3. Relacionar:
   - `Dim_Establecimiento[codigo_establecimiento]` lado `1` con `Predicciones2026[CODIGO_ESTABLECIMIENTO]` lado muchos.
   - `Dim_Establecimiento[codigo_establecimiento]` lado `1` con `v_ranking_establecimientos[codigo_establecimiento]` lado muchos.

> Advertencia: no se puede relacionar `v_resumen_anual` con `Predicciones2026` por `CODIGO_ESTABLECIMIENTO`, porque `v_resumen_anual` está agregada por `glosa_sss` y no contiene `codigo_establecimiento`. La conexión con predicciones se hace vía `v_ranking_establecimientos` / `Dim_Establecimiento`.
>
> Advertencia: no se puede relacionar `v_resumen_anual` con `v_ranking_establecimientos` por `glosa_sss`, porque `v_ranking_establecimientos` no tiene `glosa_sss`. Solo comparten `periodo`, usando `Dim_Periodo`.
>
> Mejora futura: si se necesita cruzar `glosa_sss` con establecimiento, se debería ampliar la vista del ranking para incluir `glosa_sss`.

## 7. Las 4 páginas del dashboard

### 7.1 Página 1: Resumen Ejecutivo Nacional

Objetivo: mostrar el estado nacional agregado y permitir lectura rápida por período, Servicio de Salud y área funcional.

1. Crear 4 tarjetas KPI:
   - Índice ocupacional promedio:
     - Tabla: `v_evolucion_mensual`
     - Columna: `indice_ocupacional_prom`
     - Agregación: promedio
   - Total egresos:
     - Tabla: `v_evolucion_mensual`
     - Columna: `numero_egresos`
     - Agregación: suma
   - Letalidad nacional:
     - Crear una medida DAX ponderada sobre `v_evolucion_mensual`:

```DAX
Letalidad Nacional % =
DIVIDE(
    SUM(v_evolucion_mensual[egresos_fallecidos]),
    SUM(v_evolucion_mensual[numero_egresos])
) * 100
```

   - Promedio días de estada:
     - Tabla: `v_evolucion_mensual`
     - Columna: `promedio_dias_estada_prom`
     - Agregación: promedio

2. Crear gráfico de líneas para evolución mensual 2014-2026:
   - Tabla: `v_evolucion_mensual`
   - Eje X: `ANIO_MES`
   - Valor: `indice_ocupacional_prom`
   - Agregación: promedio

3. Crear gráfico de barras para egresos por Servicio de Salud:
   - Tabla: `v_resumen_anual`
   - Eje: `glosa_sss`
   - Valor: `numero_egresos`
   - Agregación: suma

4. Crear segmentadores:
   - `Dim_Periodo[periodo]`
   - `v_resumen_anual[glosa_sss]`
   - `v_letalidad_por_area[area_funcional]`

> Nota: por los granos distintos, algunos segmentadores solo afectarán a las visuales de su propia tabla, salvo que estén conectados mediante dimensiones. `Dim_Periodo` sí puede filtrar las cuatro vistas conectadas por `periodo`.

### 7.2 Página 2: Efecto COVID

Objetivo: mostrar el cambio de ocupación y letalidad durante la pandemia.

1. Crear gráfico de líneas con doble eje usando `v_evolucion_mensual`.
2. Configurar:
   - Eje X: `ANIO_MES`
   - Eje Y1: `indice_ocupacional_prom`
   - Eje Y2: `letalidad_prom`
3. Agregar líneas de referencia o cuadros de texto con estos hallazgos:
   - La ocupación cae a su mínimo en abril de 2020: `45,61`.
   - La letalidad sube desde aproximadamente `2,8%` en 2014-2019 a `4,31%` en 2020.
   - La letalidad alcanza un pico de `4,67%` en 2021.
   - La meseta post-pandemia queda alrededor de `3,2%` en 2023-2026.
4. Usar títulos y anotaciones breves para separar visualmente:
   - Período prepandemia.
   - Año 2020.
   - Pico 2021.
   - Meseta post-pandemia.

### 7.3 Página 3: Análisis por Establecimiento y Clusters

Objetivo: revisar el ranking de establecimientos y dejar documentada la interpretación de clusters.

1. Crear tabla top 20 ocupación:
   - Tabla: `v_ranking_establecimientos`
   - Columnas:
     - `ranking`
     - `establecimiento`
     - `idx_ocup_prom`
     - `numero_egresos`
2. Agregar segmentador:
   - `Dim_Periodo[periodo]`
3. Configurar una página de detalle para drill-through por establecimiento:
   - Crear una nueva página de detalle.
   - En el área de drill-through, usar `Dim_Establecimiento[establecimiento]`.
   - Agregar visuales filtrados por el establecimiento seleccionado.

> Advertencia de clusters: la asignación establecimiento -> cluster vive en el modelo `kmeans_establecimientos.pkl` y no está exportada a ninguna vista ni al CSV. Por lo tanto, todavía no puede usarse como filtro interactivo en Power BI.
>
> Usar los clusters como tarjetas o cuadros de referencia estáticos:
>
> C0 Baja complejidad/baja demanda: 120 establecimientos, aproximadamente 57%, ocupación 43,7%, estada 9,8 días, letalidad 2,7%.
>
> C1 Alta complejidad/agudos: 82 establecimientos, aproximadamente 39%, ocupación 73,4%, estada 17,8 días, letalidad 10,8%, la más alta.
>
> C2 Larga estadía/psiquiátricos: 4 establecimientos, aproximadamente 2%, estada 343 días, ocupación 81,8%, letalidad 2,2%.
>
> C3 Atípicos/altísima rotación: 2 establecimientos, aproximadamente 1%, rotación 30,4, estada 4,5 días, ocupación mayor a 100%.
>
> Mejora futura: exportar un CSV establecimiento -> cluster para permitir filtros interactivos por cluster.

### 7.4 Página 4: Predicciones 2026

Objetivo: comparar valores reales disponibles con la predicción del índice ocupacional 2026.

1. Crear gráfico de líneas real vs predicho usando `Predicciones2026`.
2. Configurar:
   - Eje X: `MES`
   - Serie 1: `INDICE_OCUPACIONAL_PREDICHO`
   - Serie 2: `VALOR_REAL`
   - Agregación de ambas series: `Promedio` (no `Suma`). Como hay 84 series área-establecimiento, sin filtrar el gráfico promedia todas; al elegir un establecimiento y un área en los segmentadores se aísla la serie individual.
3. Agregar segmentadores:
   - `Predicciones2026[ESTABLECIMIENTO]`
   - `Predicciones2026[AREA_FUNCIONAL]`
4. Explicar visualmente el tramo real y el tramo pronosticado:
   - `VALOR_REAL` solo existe para enero-mayo 2026.
   - Ese tramo corresponde a 420 filas con valor real.
   - Junio-diciembre 2026 es pronóstico puro.
5. Sugerencia visual:
   - Usar color sólido para enero-mayo.
   - Usar una anotación o sombreado para junio-diciembre.
   - Agregar un cuadro de texto que indique: `Desde junio de 2026, el valor mostrado corresponde a pronóstico sin valor real observado`.

6. Agregar tarjetas de texto estático con métricas del modelo de Fase 4:
   - `R2 = 0,636`
   - `MAE = 8,13`

> Nota: `R2` y `MAE` son métricas de validación del modelo. No se recalculan en Power BI con las columnas disponibles.

## 8. Cierre y actualización de datos

1. Para actualizar el dashboard, usar `Inicio` -> `Actualizar`.
2. Power BI reconsultará las vistas de PostgreSQL y volverá a leer el CSV importado.
3. Antes de actualizar, verificar que:
   - PostgreSQL esté corriendo.
   - `rem20_db` esté disponible.
   - Las vistas del schema `rem20` existan.
   - `data/processed/rem20_predicciones_2026.csv` mantenga el separador `;` y encoding `utf-8-sig`.
4. Guardar el archivo `.pbix` dentro de la carpeta:
   - `powerbi/`

