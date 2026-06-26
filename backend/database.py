from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine


_ENGINE: Engine | None = None


def load_config(root: Path) -> dict[str, str]:
    """Lee la configuracion de conexion desde el archivo .env del proyecto."""
    load_dotenv(root / ".env")

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    config = {key: os.getenv(key) for key in required}
    missing = [key for key, value in config.items() if not value]

    if missing:
        raise ValueError(
            "Faltan variables obligatorias en .env: " + ", ".join(missing)
        )

    return {key: value for key, value in config.items() if value is not None}


def database_url(config: dict[str, str]) -> str:
    """Construye la URL de SQLAlchemy sin exponer credenciales por consola."""
    user = quote_plus(config["DB_USER"])
    password = quote_plus(config["DB_PASSWORD"])
    host = config["DB_HOST"]
    port = config["DB_PORT"]
    name = config["DB_NAME"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def get_engine() -> Engine:
    """Retorna un engine singleton para reutilizar el pool de conexiones."""
    global _ENGINE

    if _ENGINE is None:
        root = Path(__file__).resolve().parents[1]
        config = load_config(root)
        _ENGINE = create_engine(database_url(config), pool_pre_ping=True)

    return _ENGINE


@contextmanager
def get_connection() -> Iterator[Connection]:
    """Entrega una conexion reutilizable dentro de un bloque with."""
    with get_engine().connect() as connection:
        yield connection
