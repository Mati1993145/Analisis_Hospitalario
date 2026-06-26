from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from backend import queries


app = FastAPI(title="API REM20 - Indicadores Hospitalarios", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "*",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _handle_errors(action: Callable[[], Any]) -> Any:
    try:
        return action()
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error al consultar la base de datos: {exc}"},
        )
    except FileNotFoundError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": f"Error interno: {exc}"})


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "mensaje": "Bienvenido a la API REM20 - Indicadores Hospitalarios",
        "endpoints": [
            "/api/resumen",
            "/api/evolucion?periodo=2025",
            "/api/covid",
            "/api/ranking?periodo=2025",
            "/api/letalidad-area?periodo=2025",
            "/api/clusters",
            "/api/predicciones",
        ],
    }


@app.get("/api/resumen")
def api_resumen() -> Any:
    return _handle_errors(queries.resumen_nacional)


@app.get("/api/evolucion")
def api_evolucion(periodo: int | None = Query(default=None)) -> Any:
    return _handle_errors(lambda: queries.evolucion_mensual(periodo))


@app.get("/api/covid")
def api_covid() -> Any:
    return _handle_errors(queries.efecto_covid)


@app.get("/api/ranking")
def api_ranking(periodo: int = Query(default=2025)) -> Any:
    return _handle_errors(lambda: queries.ranking_establecimientos(periodo))


@app.get("/api/letalidad-area")
def api_letalidad_area(periodo: int | None = Query(default=None)) -> Any:
    return _handle_errors(lambda: queries.letalidad_por_area(periodo))


@app.get("/api/clusters")
def api_clusters() -> Any:
    return _handle_errors(queries.clusters)


@app.get("/api/predicciones")
def api_predicciones() -> Any:
    return _handle_errors(queries.predicciones_2026)
