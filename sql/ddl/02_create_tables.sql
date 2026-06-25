-- Crear tablas del esquema REM20.
-- Ejecutar conectado a rem20_db:
--   psql -U postgres -d rem20_db -f sql/ddl/02_create_tables.sql

CREATE SCHEMA IF NOT EXISTS rem20;

CREATE TABLE IF NOT EXISTS rem20.indicadores (
    PERIODO INTEGER,
    TIPO_PERTENENCIA SMALLINT,
    COD_SSS SMALLINT,
    GLOSA_SSS VARCHAR(50),
    CODIGO_ESTABLECIMIENTO INTEGER,
    ESTABLECIMIENTO VARCHAR(100),
    COD_AREA_FUNCIONAL SMALLINT,
    AREA_FUNCIONAL VARCHAR(100),
    MES SMALLINT,
    DIAS_CAMAS_OCUPADAS INTEGER,
    DIAS_CAMAS_DISPONIBLES INTEGER,
    DIAS_ESTADA INTEGER,
    NUMERO_EGRESOS INTEGER,
    EGRESOS_FALLECIDOS INTEGER,
    TRASLADOS INTEGER,
    INDICE_OCUPACIONAL NUMERIC(8,2),
    PROMEDIO_CAMAS_DISPONIBLE NUMERIC(8,2),
    PROMEDIO_DIAS_ESTADA NUMERIC(8,2),
    LETALIDAD NUMERIC(8,2),
    INDICE_ROTACION NUMERIC(8,2),
    PRIMARY KEY (PERIODO, MES, CODIGO_ESTABLECIMIENTO, COD_AREA_FUNCIONAL)
);

CREATE INDEX IF NOT EXISTS idx_indicadores_periodo ON rem20.indicadores (PERIODO);
CREATE INDEX IF NOT EXISTS idx_indicadores_mes ON rem20.indicadores (MES);
CREATE INDEX IF NOT EXISTS idx_indicadores_cod_sss ON rem20.indicadores (COD_SSS);
CREATE INDEX IF NOT EXISTS idx_indicadores_codigo_establecimiento ON rem20.indicadores (CODIGO_ESTABLECIMIENTO);
CREATE INDEX IF NOT EXISTS idx_indicadores_area_funcional ON rem20.indicadores (AREA_FUNCIONAL);

COMMENT ON TABLE rem20.indicadores IS 'Indicadores hospitalarios REM20 del Ministerio de Salud de Chile, por periodo, mes, establecimiento y area funcional.';

COMMENT ON COLUMN rem20.indicadores.PERIODO IS 'Año del registro.';
COMMENT ON COLUMN rem20.indicadores.TIPO_PERTENENCIA IS 'Pertenencia al Sistema Nacional de Servicios de Salud (1 = Perteneciente, 2 = No perteneciente).';
COMMENT ON COLUMN rem20.indicadores.COD_SSS IS 'Identificador único del Servicio de Salud o SEREMI, vigente para el año del PERIODO.';
COMMENT ON COLUMN rem20.indicadores.GLOSA_SSS IS 'Dependencia jerárquica superior del establecimiento (Servicio de Salud o SEREMI).';
COMMENT ON COLUMN rem20.indicadores.CODIGO_ESTABLECIMIENTO IS 'Identificador único del establecimiento (prestador).';
COMMENT ON COLUMN rem20.indicadores.ESTABLECIMIENTO IS 'Denominación nominal del establecimiento.';
COMMENT ON COLUMN rem20.indicadores.COD_AREA_FUNCIONAL IS 'Identificador único del área funcional.';
COMMENT ON COLUMN rem20.indicadores.AREA_FUNCIONAL IS 'Área de cuidados de las camas hospitalarias según nivel de complejidad.';
COMMENT ON COLUMN rem20.indicadores.MES IS 'Mes del registro.';
COMMENT ON COLUMN rem20.indicadores.DIAS_CAMAS_OCUPADAS IS 'Cantidad de días en que una cama del área funcional está ocupada.';
COMMENT ON COLUMN rem20.indicadores.DIAS_CAMAS_DISPONIBLES IS 'Cantidad de días en que una cama del área funcional está disponible.';
COMMENT ON COLUMN rem20.indicadores.DIAS_ESTADA IS 'Total de días en que los pacientes hacen uso de una cama del área funcional.';
COMMENT ON COLUMN rem20.indicadores.NUMERO_EGRESOS IS 'Total de egresos (alta, derivación o fallecimiento).';
COMMENT ON COLUMN rem20.indicadores.EGRESOS_FALLECIDOS IS 'Egresos en condición de fallecido.';
COMMENT ON COLUMN rem20.indicadores.TRASLADOS IS 'Movimiento del paciente a otra área funcional del establecimiento; no constituye egreso.';
COMMENT ON COLUMN rem20.indicadores.INDICE_OCUPACIONAL IS 'Días camas ocupadas respecto a disponibles, en porcentaje.';
COMMENT ON COLUMN rem20.indicadores.PROMEDIO_CAMAS_DISPONIBLE IS 'Promedio de días que una cama del área funcional permanece disponible.';
COMMENT ON COLUMN rem20.indicadores.PROMEDIO_DIAS_ESTADA IS 'Promedio de días que un paciente permanece en el área funcional.';
COMMENT ON COLUMN rem20.indicadores.LETALIDAD IS 'Porcentaje de egresos fallecidos sobre el total de egresos.';
COMMENT ON COLUMN rem20.indicadores.INDICE_ROTACION IS 'Número de pacientes que pasan por una cama hospitalaria en el período.';
