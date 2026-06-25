# Análisis de Indicadores Hospitalarios — Chile 2014-2026

## Descripción

Proyecto orientado al análisis de 165.235 registros provenientes de 313 establecimientos públicos de salud de Chile, basados en los Resúmenes Estadísticos Mensuales (REM serie 20) del Ministerio de Salud (MINSAL).

El objetivo es organizar, procesar y analizar indicadores hospitalarios para apoyar la exploración estadística, modelamiento y visualización de datos sanitarios.

## Stack tecnológico

- PostgreSQL
- Python
- Power BI
- Claude Desktop (MCP)

## Inicio rápido

En Windows, desde la raíz del proyecto:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Estructura del proyecto

```text
Analisis_Hospitalario/
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       ├── graficos/
│       │   └── .gitkeep
│       └── modelos/
│           └── .gitkeep
├── sql/
│   ├── ddl/
│   │   └── .gitkeep
│   ├── queries/
│   │   └── .gitkeep
│   └── views/
│       └── .gitkeep
├── python/
│   ├── notebooks/
│   │   └── .gitkeep
│   └── scripts/
│       └── .gitkeep
├── powerbi/
│   └── .gitkeep
├── .env
├── .gitignore
├── BITACORA.md
├── README.md
└── requirements.txt
```

## Configuración

El archivo `.env` contiene placeholders para la conexión a PostgreSQL. Antes de ejecutar scripts o notebooks, se debe copiar o editar este archivo con las credenciales reales de la base de datos:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rem20_db
DB_USER=postgres
DB_PASSWORD=tu_password_aqui
```

No se deben versionar credenciales reales. El archivo `.env` está excluido por `.gitignore`.
