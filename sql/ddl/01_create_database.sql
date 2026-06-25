-- Crea la base de datos del proyecto REM20.
-- IMPORTANTE: CREATE DATABASE no puede ejecutarse dentro de una transaccion.
-- Este script debe ejecutarse conectado a la base "postgres" por defecto, no a rem20_db.
-- Ejemplo:
--   psql -U postgres -d postgres -f sql/ddl/01_create_database.sql

CREATE DATABASE rem20_db;

\c rem20_db

CREATE SCHEMA IF NOT EXISTS rem20;
