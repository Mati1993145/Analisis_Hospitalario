# Backend FastAPI REM20

Este backend expone indicadores hospitalarios REM20 desde PostgreSQL y archivos procesados como endpoints JSON.

## Levantar servidor

Desde la raiz del proyecto:

```powershell
uvicorn backend.main:app --reload --port 8000
```

La documentacion interactiva Swagger queda disponible en:

```text
http://localhost:8000/docs
```

## Endpoints

### GET /

Mensaje de bienvenida y lista de endpoints.

```json
{
  "mensaje": "Bienvenido a la API REM20 - Indicadores Hospitalarios",
  "endpoints": ["/api/resumen", "/api/evolucion?periodo=2025"]
}
```

### GET /api/resumen

KPIs nacionales del ultimo periodo disponible, calculados desde `rem20.indicadores`.

```json
[
  {
    "periodo": 2025,
    "indice_ocupacional_prom": 78.4,
    "total_egresos": 120000,
    "letalidad_nacional": 2.1,
    "promedio_dias_estada_prom": 5.8
  }
]
```

### GET /api/evolucion?periodo=2025

Evolucion mensual desde `rem20.v_evolucion_mensual`. El parametro `periodo` es opcional.

```json
[
  {
    "periodo": 2025,
    "mes": 1,
    "indice_ocupacional_prom": 76.2,
    "promedio_dias_estada_prom": 5.7,
    "letalidad_prom": 2.0,
    "numero_egresos": 9800,
    "egresos_fallecidos": 196
  }
]
```

### GET /api/covid

Serie 2018 a 2022 con ocupacion y letalidad mensual.

```json
[
  {
    "periodo": 2020,
    "mes": 6,
    "indice_ocupacional_prom": 70.5,
    "letalidad_prom": 3.2
  }
]
```

### GET /api/ranking?periodo=2025

Top 20 de establecimientos desde `rem20.v_ranking_establecimientos`.

```json
[
  {
    "periodo": 2025,
    "ranking": 1,
    "codigo_establecimiento": 123,
    "establecimiento": "Hospital Ejemplo",
    "idx_ocup_prom": 95.1,
    "numero_egresos": 4500
  }
]
```

### GET /api/letalidad-area?periodo=2025

Letalidad por area funcional desde `rem20.v_letalidad_por_area`. El parametro `periodo` es opcional.

```json
[
  {
    "area_funcional": "Medicina",
    "periodo": 2025,
    "egresos_fallecidos": 120,
    "numero_egresos": 4000,
    "letalidad_pct": 3.0
  }
]
```

### GET /api/clusters

Categorias de cluster. Si existe `data/processed/clusters.csv`, se lee ese archivo; si no, se entrega una clasificacion fija.

```json
[
  {
    "cluster": 0,
    "etiqueta": "Saturación crítica",
    "descripcion": "Establecimientos con índice ocupacional muy alto y presión sostenida sobre camas."
  }
]
```

### GET /api/predicciones

Predicciones 2026 desde `data/processed/rem20_predicciones_2026.csv`.

```json
[
  {
    "PERIODO": 2026,
    "MES": 1,
    "CODIGO_ESTABLECIMIENTO": 123,
    "ESTABLECIMIENTO": "Hospital Ejemplo",
    "AREA_FUNCIONAL": "Medicina",
    "INDICE_OCUPACIONAL_PREDICHO": 82.5,
    "VALOR_REAL": null
  }
]
```
