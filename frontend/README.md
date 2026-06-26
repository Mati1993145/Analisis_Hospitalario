# Dashboard de Indicadores Hospitalarios

Este dashboard se sirve desde el propio backend FastAPI. Desde la raíz del proyecto, levanta la API con:

```bash
uvicorn backend.main:app --reload --port 8000
```

Luego abre http://localhost:8000.

El frontend consume las rutas `/api/*` del mismo origen, por lo que requiere que el backend y la base de datos PostgreSQL estén disponibles. La documentación interactiva de la API sigue publicada en `/docs`.

La interfaz actualiza todos los indicadores automáticamente cada 5 minutos y muestra el sello de "Última actualización" con la hora local de la última carga.
