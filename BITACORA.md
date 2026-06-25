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

**Commit:** `(siguiente)`

---
