-- Crear vistas analiticas del esquema REM20.
-- Ejecutar conectado a rem20_db:
--   psql -U postgres -d rem20_db -f sql/ddl/03_create_views.sql

CREATE OR REPLACE VIEW rem20.v_resumen_anual AS
SELECT
    periodo,
    glosa_sss,
    ROUND(AVG(indice_ocupacional)::numeric, 2) AS indice_ocupacional_prom,
    ROUND(AVG(promedio_dias_estada)::numeric, 2) AS promedio_dias_estada_prom,
    ROUND(AVG(letalidad)::numeric, 2) AS letalidad_prom,
    ROUND(AVG(indice_rotacion)::numeric, 2) AS indice_rotacion_prom,
    SUM(numero_egresos) AS numero_egresos,
    SUM(egresos_fallecidos) AS egresos_fallecidos
FROM rem20.indicadores
GROUP BY periodo, glosa_sss
ORDER BY periodo, glosa_sss;

CREATE OR REPLACE VIEW rem20.v_evolucion_mensual AS
SELECT
    periodo,
    mes,
    ROUND(AVG(indice_ocupacional)::numeric, 2) AS indice_ocupacional_prom,
    ROUND(AVG(promedio_dias_estada)::numeric, 2) AS promedio_dias_estada_prom,
    ROUND(AVG(letalidad)::numeric, 2) AS letalidad_prom,
    SUM(numero_egresos) AS numero_egresos,
    SUM(egresos_fallecidos) AS egresos_fallecidos
FROM rem20.indicadores
GROUP BY periodo, mes
ORDER BY periodo, mes;

CREATE OR REPLACE VIEW rem20.v_ranking_establecimientos AS
WITH ranking_anual AS (
    SELECT
        periodo,
        codigo_establecimiento,
        establecimiento,
        ROUND(AVG(indice_ocupacional)::numeric, 2) AS idx_ocup_prom,
        SUM(numero_egresos) AS numero_egresos,
        ROW_NUMBER() OVER (
            PARTITION BY periodo
            ORDER BY AVG(indice_ocupacional) DESC
        ) AS ranking
    FROM rem20.indicadores
    GROUP BY periodo, codigo_establecimiento, establecimiento
)
SELECT
    periodo,
    ranking,
    codigo_establecimiento,
    establecimiento,
    idx_ocup_prom,
    numero_egresos
FROM ranking_anual
WHERE ranking <= 20
ORDER BY periodo, ranking;

CREATE OR REPLACE VIEW rem20.v_letalidad_por_area AS
SELECT
    area_funcional,
    periodo,
    SUM(egresos_fallecidos) AS egresos_fallecidos,
    SUM(numero_egresos) AS numero_egresos,
    ROUND(100.0 * SUM(egresos_fallecidos) / NULLIF(SUM(numero_egresos), 0), 2) AS letalidad_pct
FROM rem20.indicadores
GROUP BY area_funcional, periodo
HAVING SUM(numero_egresos) > 100
ORDER BY periodo, letalidad_pct DESC;
