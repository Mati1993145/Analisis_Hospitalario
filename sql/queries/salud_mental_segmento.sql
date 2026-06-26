-- =====================================================================
-- Fase 9 - Sub-estudio COVID y hospitalizacion psiquiatrica
-- Definicion del SEGMENTO de salud mental / psiquiatria
-- Fuente: rem20.indicadores (MINSAL REM20, 2014-2026)
-- =====================================================================
--
-- DECISION METODOLOGICA (rigor Jack):
-- 1. El segmento se define por COD_AREA_FUNCIONAL, no por el texto de
--    AREA_FUNCIONAL. El texto tiene mojibake y variantes ("Area de" vs
--    "Area", "Dr" vs "Dr.") que duplican glosas; el codigo es estable.
-- 2. El segmento se define por AREA FUNCIONAL (la unidad psiquiatrica),
--    NO por establecimiento. La hospitalizacion psiquiatrica ocurre tanto
--    en hospitales especializados como en unidades psiquiatricas de
--    hospitales generales; segmentar por area captura TODO el sistema.
-- 3. SALVEDAD: REM20 mide volumen/flujo (camas, egresos, dias estada),
--    NO diagnostico clinico por patologia. La granularidad disponible es
--    estructural (Adulto/Infanto, Corta/Mediana/Larga estadia, Forense,
--    Cuidados Intensivos), no por enfermedad. El estudio analiza
--    hospitalizacion psiquiatrica AGREGADA.
--
-- TRES definiciones (decision validada por el usuario 2026-06-26: analizar
-- segmento clinico y total POR SEPARADO):
--   * CLINICO (base) = 418,419,420,421,422,428,429   (sin forense)
--   * FORENSE        = 423,424,425,426                (flujo judicial, aparte)
--   * TOTAL          = CLINICO + FORENSE = rango 418-429 EXCEPTO 427
--
-- EXCLUIDO: 427 'Area Sociosanitaria Adulto' -> cuidado de larga estancia
--   social, no psiquiatria. Candidato a analisis de sensibilidad, no al
--   segmento base.
--
-- Razon de separar la forense: la psiquiatria forense responde a flujos del
-- sistema judicial, no a demanda epidemiologica de salud mental; mezclarla
-- contaminaria la prueba de si el COVID altero la demanda psiquiatrica.
-- =====================================================================

-- (A) Areas funcionales que componen el segmento psiquiatrico
SELECT cod_area_funcional,
       MIN(area_funcional)            AS glosa,
       COUNT(*)                       AS filas,
       SUM(numero_egresos)            AS egresos_totales,
       MIN(periodo)                   AS desde,
       MAX(periodo)                   AS hasta
FROM rem20.indicadores
WHERE cod_area_funcional IN (418,419,420,421,422,423,424,425,426,428,429)
GROUP BY cod_area_funcional
ORDER BY cod_area_funcional;

-- (B) Establecimientos psiquiatricos especializados (CONTEXTO / validacion,
--     no se usan para segmentar la demanda)
--     108105 Hospital Psiquiatrico Dr. Philippe Pinel (Putaendo)
--     113170 Hospital Psiquiatrico El Peral (Santiago, Puente Alto)
--     109102 Instituto Psiquiatrico Dr. Jose Horwitz Barak (Santiago, Recoleta)
SELECT codigo_establecimiento,
       MIN(establecimiento) AS establecimiento,
       COUNT(*)             AS filas
FROM rem20.indicadores
WHERE codigo_establecimiento IN (108105, 113170, 109102)
GROUP BY codigo_establecimiento
ORDER BY establecimiento;

-- (C) Serie mensual del segmento CLINICO (demanda agregada, base Secc. 1-3).
--     Para el TOTAL, agregar 423,424,425,426 al IN. El notebook itera sobre
--     ambas definiciones (clinico y total) por separado.
SELECT make_date(periodo, mes, 1)        AS fecha,
       SUM(numero_egresos)               AS egresos,
       SUM(dias_camas_ocupadas)          AS dias_camas_ocupadas,
       SUM(dias_camas_disponibles)       AS dias_camas_disponibles,
       CASE WHEN SUM(dias_camas_disponibles) > 0
            THEN 100.0 * SUM(dias_camas_ocupadas) / SUM(dias_camas_disponibles)
            ELSE NULL END                AS indice_ocupacional_pct
FROM rem20.indicadores
WHERE cod_area_funcional IN (418,419,420,421,422,428,429)
GROUP BY make_date(periodo, mes, 1)
ORDER BY fecha;

-- (D) Serie mensual del RESTO del sistema (grupo de control, Seccion 4).
--     Todo lo NO psiquiatrico (excluye el rango 418-429 completo, incluida
--     la forense y el 427 sociosanitario, para un control no-psiquiatrico
--     limpio).
SELECT make_date(periodo, mes, 1)        AS fecha,
       SUM(numero_egresos)               AS egresos,
       SUM(dias_camas_ocupadas)          AS dias_camas_ocupadas,
       SUM(dias_camas_disponibles)       AS dias_camas_disponibles,
       CASE WHEN SUM(dias_camas_disponibles) > 0
            THEN 100.0 * SUM(dias_camas_ocupadas) / SUM(dias_camas_disponibles)
            ELSE NULL END                AS indice_ocupacional_pct
FROM rem20.indicadores
WHERE cod_area_funcional NOT BETWEEN 418 AND 429
GROUP BY make_date(periodo, mes, 1)
ORDER BY fecha;
