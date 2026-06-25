# 📓 BITÁCORA — Análisis Hospitalario

> Registro de fases del proyecto. Datos hospitalarios REM20 (MINSAL Chile, 2014–2026).
> Flujo de trabajo: **Codex desarrolla → Claude Code (orquestador) revisa, corrige y ejecuta**.

---

## Roles

- **Codex (ejecutor):** desarrolla y escribe el código de cada fase en archivos del proyecto.
- **Claude Code (orquestador):** define la tarea, delega a Codex, analiza técnicamente el
  resultado, corrige errores y mejora la calidad, ejecuta y verifica, registra y commitea.

## Estructura del registro por fase

Cada fase documenta: **(1)** qué hizo Codex, **(2)** qué corrigió/mejoró Claude,
**(3)** estado final y verificación, **(4)** hash del commit.

---

## Estado del entorno

| Elemento | Estado | Detalle |
|---|---|---|
| Conector MCP Codex | ✅ Verificado | `mcp__codex__codex` disponible |
| Repositorio git | ✅ Inicializado | 2026-06-25 |
| Bitácora | ✅ Creada | Este archivo |
| Entorno virtual `venv/` | ✅ Creado | Python 3.12.3, deps instaladas (Fase 1) |

---

## Registro de fases

### Fase 1 — Configuración del entorno · ✅ Completada (2026-06-25)

**Objetivo:** estructura de carpetas, archivos de configuración y entorno virtual Python.

**Qué hizo Codex (ejecutor):**
- Creó la estructura de carpetas (`data/`, `sql/`, `python/`, `powerbi/`) con `.gitkeep`
  en cada carpeta hoja para que git las rastree pese a estar vacías.
- Generó `requirements.txt`, `.env` (placeholders), `.gitignore` y `README.md` en español
  con título, descripción (165.235 registros / 313 establecimientos), stack, inicio rápido,
  árbol del proyecto y sección de configuración.

**Qué revisó/corrigió Claude (orquestador):**
- Revisé contenido de los 4 archivos de config: todos correctos.
- Verifiqué con `git check-ignore` que `data/raw/.gitkeep` NO queda ignorado (las carpetas
  se rastrean) mientras `data/raw/*.csv` y `*.xlsx` sí se ignoran. Correcto.
- **Mejora añadida:** creé `.env.example` versionado, ya que el `.env` real está en
  `.gitignore` y un clon del repo no tendría plantilla de variables.

**Ejecución y verificación (Claude):**
- Python 3.12.3 detectado. Creé `venv/` con `python -m venv`.
- Instalé `requirements.txt` en el venv (pip exit code 0). Versiones clave: pandas 3.0.3,
  sqlalchemy 2.0.51, scikit-learn 1.9.0, psycopg2-binary 2.9.12.
- Smoke test de imports de las 10 librerías clave: OK (exit 0).

**Estado final:** entorno listo. Pendiente: el usuario completará credenciales reales en `.env`.

**Commit:** `e8a9aee`

---

### Fase 2 — Base de datos en PostgreSQL · ✅ Completada (2026-06-25)

**Objetivo:** crear la BD `rem20_db`, el modelo relacional, cargar los 165.235 registros
del CSV y construir 4 vistas analíticas para Power BI.

**Qué hizo Codex (ejecutor):** escribió 4 archivos —
`sql/ddl/01_create_database.sql`, `sql/ddl/02_create_tables.sql` (tabla `rem20.indicadores`
con tipos, PK compuesta, 5 índices y COMMENT en cada columna desde el diccionario),
`python/scripts/01_load_data.py` (carga con dotenv + SQLAlchemy, limpieza, validación de
duplicados) y `sql/ddl/03_create_views.sql` (4 vistas).

**Qué revisé/corregí Claude (orquestador):**
- **Bug corregido (crítico):** el cargador usaba `to_sql(method="multi", chunksize=5000)`.
  Con 20 columnas eso son 100.000 parámetros por INSERT y psycopg2/PostgreSQL limitan a
  **65.535 parámetros por sentencia** → la carga habría fallado. Reduje el chunksize interno
  a **1.000** (`INSERT_CHUNKSIZE`), dejando intacto el batch externo de 25.000 (reporte de
  progreso). `py_compile` OK.
- **Encoding:** verifiqué que CSV y archivos `.sql` están en UTF-8. Ejecuté psql forzando
  `PGCLIENTENCODING=UTF8` para que los COMMENT y textos con acentos no se corrompieran.
  Confirmado en BD: "Área de cuidados…", "Hospital Dr Juan Noé Crevanni".
- Mantuve la decisión de diseño `COD_SSS SMALLINT` (el origen trae "01" → se carga como 1).

**Ejecución y verificación (Claude):**
- Pre-requisitos verificados: PostgreSQL 18.3 (`C:\Program Files\PostgreSQL\18\bin`).
  El usuario completó las credenciales reales en `.env` (hubo que reintentar: la 1ª vez no
  se había guardado el archivo).
- Cadena ejecutada en orden: crear DB → tabla + índices + 21 COMMENT → carga → 4 vistas.
- Carga: **165.232 filas en 38,3 s**. `SELECT COUNT(*)` = 165.232. Periodos 2014–2026,
  208 establecimientos distintos. Las 4 vistas devuelven datos correctos.

**Hallazgo de calidad de datos:** el CSV trae 165.235 filas, pero **3 pares** comparten la
misma clave (PERIODO, MES, CODIGO_ESTABLECIMIENTO, COD_AREA_FUNCIONAL) con **cifras distintas**
(no son filas idénticas). Casos: Hospital de Teno (2014-12 área 401; 2014-06 área 407) y
Hospital Comunitario de Laja (2020-06 área 407). El cargador conservó el primer registro de
cada par (165.235 − 3 = **165.232**). Quedan documentados por si se requiere revisión manual.

**Estado final:** modelo relacional poblado y vistas operativas. Listo para Power BI / análisis.

**Commit:** `dc86337`

---

### Fase 3 — Análisis Exploratorio de Datos (EDA) · ✅ Completada (2026-06-25)

**Objetivo:** reporte de conflictos de calidad + notebook EDA con 4 secciones (validación,
índice ocupacional, letalidad, eficiencia) y exportación de gráficos PNG.

**Qué hizo Codex (ejecutor):** escribió `python/scripts/02_reporte_conflictos.py` (detección
y exportación de registros con PK en conflicto) y `python/notebooks/01_eda_rem20.ipynb`
(notebook nbformat 4.5, 20 celdas, consultas a la BD con columnas en minúscula, `matplotlib
Agg`, helper `guardar_grafico`, letalidad ponderada por egresos).

**Qué revisé/corregí Claude (orquestador):**
- Revisé la lógica de cálculo: letalidad **ponderada** por egresos (correcto, no promedio
  simple), filtros `numero_egresos>0`, recorte p99 en scatter, top-8 áreas + "Otras" para
  leyenda legible. Lógica correcta.
- **Mejora de legibilidad:** el título del histograma era una línea larguísima que se salía
  del gráfico; lo dividí en título corto + subtítulo aclaratorio (vía `ax.text`).
- Ejecuté el notebook con `nbconvert --execute` usando el kernel del venv (`EXITCODE=0`).

**Ejecución y verificación (Claude):**
- `02_reporte_conflictos.py` → `data/processed/conflictos_clave_primaria.csv` (3 grupos,
  6 filas, `utf-8-sig` para Excel). Coincide con el hallazgo de Fase 2.
- Notebook ejecutado completo; **8 PNG generados** en `data/processed/graficos/`.
- **Verifiqué visualmente** los gráficos clave (no solo su existencia) y extraje cifras
  exactas desde la BD para el informe (ver sección de hallazgos).

**Commit:** `ebe3ac8`

---

### Fase 4 — Análisis estadístico y predictivo · ✅ Completada (2026-06-25)

**Objetivo:** corregir los 3 conflictos de PK en BD (trazable), descomposición STL, modelo
predictivo (Random Forest) de índice ocupacional y clustering de establecimientos.

**Qué hizo Codex (ejecutor):** `python/scripts/03_corrige_conflictos.py` (UPDATE parametrizado
con transacción) y `python/notebooks/02_analisis_estadistico.ipynb` (STL, RF con lags por serie,
KMeans + PCA).

**Qué revisé/corregí Claude (orquestador):**
- **Criterio de plausibilidad (definido por el orquestador, no heurística ciega):** evalué los
  3 conflictos uno por uno. En Hospital de Teno (2 casos) la fila cargada tenía índice ~0 con el
  hospital activo → se corrigió a la fila con actividad (índices 71,74 y 72,13). En Hospital de
  Laja la fila vigente ya era la correcta (la otra eran ceros absolutos) → sin cambio.
- **Bug corregido (STL):** el coeficiente de variación de la componente estacional dividía por su
  media (≈0 en STL) → daba infinito y la comparación siempre concluía "estacionalidad". Lo cambié
  a un denominador común (media de la serie observada) para que ambas componentes sean comparables.
- **Verifiqué la ausencia de fuga de datos:** lags por serie `(establecimiento, área)` con
  `shift(1)`, `shift(12)` y `shift(1).rolling(3)`; split temporal train≤2023 / test 2024-2025.
  Correcto. La importancia de `lag_1` (0,73, no ≈1) confirma que no hay leakage del valor actual.
- **Mejora (almacenamiento):** el RF sin podar pesaba ~955 MB; añadí `compress=3` a `joblib.dump`
  → 209 MB sin alterar el modelo ni las métricas.
- Afiné la celda de interpretación de clusters con los datos reales.

**Ejecución y verificación (Claude):**
- Corrección de conflictos aplicada (2 UPDATE, 1 sin cambio); COUNT sigue 165.232; 3 registros
  verificados.
- Notebook ejecutado (`nbconvert`, `EXITCODE=0`). **5 PNG** nuevos + 2 modelos `.pkl`.
- Verifiqué visualmente codo (k=4 confirmado), feature importance y clusters PCA.

**Commit:** `fabdde0`

---

### Fase 5 — Paso 0: Exportación de predicciones 2026 para Power BI

**Qué hizo Codex (ejecutor):** `python/scripts/02_export_predictions.py` — carga el bundle
`rf_indice_ocupacional.pkl`, selecciona los 5 establecimientos de mayor suma histórica de
`numero_egresos`, pronostica el índice ocupacional de los 12 meses de 2026 por serie
`(establecimiento, área)` y exporta a `data/processed/rem20_predicciones_2026.csv`.

**Qué revisé/corregí Claude (orquestador):**
- **Validación anti-leakage (el punto crítico):** verifiqué que para predecir el mes *M* solo se
  usan meses estrictamente anteriores — `lag_1`=M-1, `lag_12`=M-12, `rolling_3`=media de M-1/M-2/M-3.
  El valor real del propio mes *M* nunca entra como feature; solo se adjunta como `VALOR_REAL` para
  comparar y como lag de meses posteriores. Correcto.
- **Features idénticas al entrenamiento:** el script valida el orden exacto de `EXPECTED_FEATURES`
  contra el bundle y **reusa el `LabelEncoder`** del `.pkl` (no re-entrena); omite con aviso las
  series cuya área no fue vista por el encoder. Consistente con Fase 4.
- **Pronóstico recursivo verificado:** `value_for_period` prefiere el real sobre el predicho, de
  modo que ene–may 2026 (con dato real) son pronóstico *1-step-ahead* genuino y jun–dic 2026 son
  recursivos puros (la predicción de un mes alimenta el lag del siguiente). Diseño sólido.
- **Verifiqué las 7 series omitidas por "memoria insuficiente":** consulté la BD y son áreas
  **genuinamente discontinuadas** (último dato 2017, 2021 o 2024), sin continuidad hacia 2026 → es
  correcto NO pronosticarlas, no es un bug del lag por calendario.

**Ejecución y verificación (Claude):**
- Script ejecutado (venv, `PGCLIENTENCODING=UTF8`). Salida: **5 establecimientos, 91 series
  evaluadas, 84 con pronóstico completo, 1.008 filas** (84 × 12 meses), **420 con `VALOR_REAL`**
  (84 series × 5 meses reales ene–may 2026).
- CSV verificado: BOM `utf-8-sig`, separador `;`, 7 columnas en orden exacto, acentos íntegros
  ("Área Cuidados Intensivos Adultos"), rango predicho 5,9–99,0 (plausible).

**Commit:** `46c8469`

---

### Fase 5 — Documentación Power BI

**Qué hizo Codex (ejecutor):** `powerbi/README_powerbi.md` — guía paso a paso para instalar el
driver Npgsql, conectar Power BI Desktop a `rem20_db`, transformar en Power Query, importar el CSV
de predicciones, armar el modelo de relaciones y construir las 4 páginas del dashboard.

**Qué revisé/corregí Claude (orquestador):**
- **Corrección de modelo de datos (lo crítico):** el plan original pedía relaciones imposibles
  contra el esquema real. Inspeccioné las 4 vistas y entregué a Codex el inventario exacto de
  columnas + el modelo corregido, evitando documentar relaciones que no existen:
  - `v_resumen_anual` se agrega por `glosa_sss` y **no tiene** `codigo_establecimiento` → no puede
    unirse a las predicciones por establecimiento; la unión se hace vía `v_ranking_establecimientos`.
  - `v_ranking_establecimientos` **no tiene** `glosa_sss` → solo comparte `periodo` con el resumen.
  - Las vistas están a granos distintos → relaciones directas serían muchos-a-muchos ambiguas.
    Solución documentada: **esquema estrella** con `Dim_Periodo` y `Dim_Establecimiento` (tablas
    calculadas DAX) como puentes.
- **Honestidad sobre clusters:** la asignación establecimiento→cluster vive en el `.pkl`, no en
  ninguna vista ni en el CSV → no puede ser filtro interactivo. Se documenta como tarjetas de
  referencia estáticas, con la mejora futura de exportar un CSV establecimiento→cluster.
- **Retoques propios:** añadí título H1 al documento (empezaba en `## 0`) y precisé en la Página 4
  que la agregación real-vs-predicho sea **Promedio** (no Suma), porque hay 84 series y sin filtrar
  se promediarían todas.

**Verificación (Claude):** revisé que todos los nombres de columnas del documento coincidan con
el DDL real de las vistas y con las columnas del CSV; advertencias de relaciones y de clusters
correctas. Documento listo para construcción manual del dashboard.

**Commit:** `3715f1f`

---

### Fase 5 — Documentación MCP Claude Desktop

**Qué hizo Codex (ejecutor):** `powerbi/README_mcp.md` — guía para conectar Claude Desktop a
`rem20_db` vía servidor MCP de PostgreSQL: requisito Node.js, ubicación del
`claude_desktop_config.json`, JSON del servidor, reinicio, 6 ejemplos de consultas en lenguaje
natural y aclaración de que MCP y Power BI son canales independientes.

**Qué revisé/corregí Claude (orquestador):**
- **Seguridad (lo crítico):** verifiqué que la única cadena de conexión use el placeholder
  `PASSWORD` y no la contraseña real (`grep` sobre `powerbi/`), y que el documento advierta que el
  `claude_desktop_config.json` es local y no debe subirse a GitHub.
- **Ejemplos fieles a los datos:** me aseguré de que los 6 ejemplos usen dimensiones reales
  (Servicio de Salud vía `glosa_sss`, establecimiento, `area_funcional`, `letalidad`, etc.) y no
  una columna "Región" inexistente. Aprovechan hallazgos reales (efecto COVID 2019→2021,
  psiquiátricos en días de estada, caída de ocupación 2020).
- **Retoque propio:** añadí título H1 al documento (coherencia con `README_powerbi.md`).

**Verificación (Claude):** `grep` confirma que la única cadena `postgresql://` usa `PASSWORD`;
aclaración MCP≠Power BI al inicio; nombres de columnas dentro del esquema real.

**Commit:** _(ver abajo)_

---

## HALLAZGOS PARA INFORME FINAL

> Registro acumulativo, fase a fase, de todo lo publicable para el reporte profesional.

### Calidad de datos (Fases 2–4)
- **Conflictos de clave primaria:** 3 grupos (6 filas) en el CSV comparten
  (PERIODO, MES, CODIGO_ESTABLECIMIENTO, COD_AREA_FUNCIONAL) con cifras distintas →
  `data/processed/conflictos_clave_primaria.csv`. Casos: Hospital de Teno (2014-12 área 401;
  2014-06 área 407) y Hospital Comunitario de Laja (2020-06 área 407).
- **Sesgo del criterio `keep="first"` y su corrección (Fase 4):** en Hospital de Teno, la fila
  conservada inicialmente era la de cifras **anómalamente bajas** (2014-12 área 401: índice 7,53)
  mientras la descartada tenía los datos sustantivos (775 días-cama disp., índice 71,74). En
  Fase 4 se corrigió en BD conservando la fila plausible, **caso por caso**:
  - Teno 2014-12 área 401: 7,53 → **71,74** (UPDATE).
  - Teno 2014-06 área 407: 2,22 → **72,13** (UPDATE).
  - Laja 2020-06 área 407: se mantuvo 15,0 (la alternativa eran ceros absolutos = registro vacío).
  El CSV de conflictos preserva los 6 registros crudos para trazabilidad. Total estable: 165.232.
- **Cobertura:** datos 2014–2026 (2026 parcial: ~417 mil egresos vs ~1 millón/año completo),
  **208 establecimientos** distintos. Valores de `indice_ocupacional > 120` (camas prestadas
  entre servicios) son válidos y marginales: **380 registros (0,23%)**.
- **Decisión técnica:** `COD_SSS` se modeló como `SMALLINT` (el origen trae "01" → 1).

### Impacto COVID-19 (efecto doble, 2020–2021)
- **Ocupación ↓:** el índice ocupacional mensual cayó a su mínimo histórico en **abril 2020
  (45,61)** vs rango habitual 60–70, por la suspensión de cirugías electivas y atención no-COVID.
- **Letalidad ↑:** la tasa nacional anual ponderada saltó de ~2,8% (estable 2014–2019) a
  **4,31% (2020)** y pico de **4,67% (2021)** — pacientes hospitalizados más graves.
- **Sin retorno a la línea base:** tras la pandemia la letalidad se estabilizó en una meseta
  de **~3,2% (2023–2026)**, por encima del ~2,8% pre-pandemia; la ocupación se recuperó a
  niveles **superiores** a los previos (picos ~71), señal de presión por listas de espera.

### Patrones operacionales
- **Estacionalidad:** ocupación máxima en invierno austral (jun–ago, ~66) y mínima en
  verano (feb/dic, ~62); amplitud modesta (~4 pts), consistente con demanda respiratoria invernal.
- **Días de estada por tipo de establecimiento:** el `promedio_dias_estada` está dominado por
  hospitales **psiquiátricos** (Philippe Pinel 493 días, El Peral 388, Horwitz 344 en 2025),
  frente a hospitales de agudos. La métrica refleja el modelo de atención, no ineficiencia.
- **Letalidad por establecimiento:** los líderes en letalidad 2025 son hospitales de
  **larga estadía / crónicos** (San José de Maipo 18,3%), que también encabezan días de estada
  — alta letalidad asociada a perfil de paciente crónico/terminal, no necesariamente a calidad.
- **Correlaciones débiles:** entre las 5 métricas principales la correlación máxima es 0,29
  (ocupación–camas disponibles); cada indicador aporta información independiente (sin
  multicolinealidad), relevante para el modelado de fases posteriores.

### Series de tiempo y modelo predictivo (Fase 4)
- **Descomposición STL** (índice ocupacional nacional, period=12, robust): la **tendencia**
  presenta mayor variabilidad relativa (std/media 0,0357) que la **estacionalidad** (0,0328),
  porque la disrupción COVID afectó sobre todo la tendencia. Mes peak estacional: **agosto**
  (invierno austral), coherente con el patrón de demanda respiratoria.
- **Modelo Random Forest** (predicción de índice ocupacional, 116.443 filas train ≤2023,
  26.185 test 2024-2025): **R² = 0,636 · MAE = 8,13 · RMSE = 19,95**. La diferencia MAE↔RMSE
  indica buen ajuste típico pero con errores grandes en casos extremos (áreas con camas
  prestadas / valores atípicos).
- **Driver dominante:** la ocupación es **altamente autorregresiva** — `lag_1` (mes anterior)
  concentra el **0,73** de la importancia, seguido de `rolling_3` (0,12) y `lag_12` (0,06,
  estacionalidad). Las variables de calendario aportan poco una vez conocidos los lags.

### Segmentación de establecimientos (Fase 4, KMeans k=4)
- **Cluster 0 — Baja complejidad/baja demanda (120 estab, ~57%):** ocupación 43,7%, estada 9,8 d,
  letalidad 2,7%, rotación 2,2. Grupo mayoritario (hospitales pequeños/comunitarios).
- **Cluster 1 — Alta complejidad/agudos (82 estab, ~39%):** ocupación 73,4%, estada 17,8 d,
  **letalidad 10,8%** (la más alta), rotación 2,7. Mayor presión asistencial del sistema.
- **Cluster 2 — Larga estadía/psiquiátricos (4 estab, ~2%):** estada **343 días**, ocupación
  81,8%, letalidad 2,2% (El Peral, Horwitz, Philippe Pinel). Larga estadía = modelo de atención.
- **Cluster 3 — Altísima rotación/corta estadía (2 estab, ~1%):** rotación 30,4, estada 4,5 d,
  ocupación >100% (camas prestadas). Perfil atípico (Llanquihue, CESFAM Río Negro).
- *k=4 validado por el método del codo* (caída marcada hasta k=4, aplanamiento posterior).

### Pronóstico operativo 2026 para Power BI (Fase 5)
- **Entregable:** `data/processed/rem20_predicciones_2026.csv` — predicción del índice ocupacional
  para los **12 meses de 2026** de los **5 hospitales de mayor egreso histórico**: Barros Luco
  Trudeau, Complejo Sótero del Río, Guillermo Grant Benavente (Concepción), Víctor Ríos Ruiz
  (Los Ángeles) y Hernán Henríquez Aravena (Temuco). 84 series área-establecimiento, 1.008 filas.
- **Método:** pronóstico recursivo con el Random Forest de Fase 4 (ene–may = *1-step-ahead* con
  lag real; jun–dic = recursivo puro). Incluye `VALOR_REAL` para los meses con dato observado
  (ene–may 2026), habilitando un panel de **real vs predicho** en Power BI.
- **Cobertura del modelo:** solo se pronostican áreas con continuidad hasta fin de 2025; **7 áreas
  discontinuadas** (cerradas en 2017/2021/2024) se excluyen explícitamente — el modelo no
  extrapola servicios sin actividad reciente.

### Decisiones / bugs técnicos relevantes
- **Bug de carga corregido:** `to_sql(method="multi", chunksize=5000)` excedía el límite de
  65.535 parámetros de psycopg2 (20 cols × 5.000); reducido a 1.000.
- **Bug STL corregido (Fase 4):** el CV de la componente estacional (media ≈0) era degenerado;
  se usó un denominador común (media de la serie) para comparar variabilidad de componentes.
- **Modelo RF comprimido:** `joblib` `compress=3` redujo el `.pkl` de ~955 MB a 209 MB.
- **Encoding:** todo el pipeline fuerza UTF-8 (CSV, `.sql` con `PGCLIENTENCODING=UTF8`,
  export con `utf-8-sig`); acentos verificados íntegros en BD.

---
