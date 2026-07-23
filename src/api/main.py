"""FastAPI entry point for the ArabamFiyat.com web application."""

from __future__ import annotations

import logging
from contextlib import closing

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import DatabaseUnavailable, ListingRepository
from .routes import catalog, listings, market, valuation
from .schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ArabamFiyat.com API", version="0.1.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(catalog.router)
app.include_router(market.router)
app.include_router(valuation.router)
app.include_router(listings.router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    repository = ListingRepository()
    try:
        with closing(repository.connect()) as connection:
            table = repository.listing_table(connection)
            count = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return HealthResponse(status="ok", database_available=True, table=table, listing_count=count)
    except DatabaseUnavailable as exc:
        return HealthResponse(status="unavailable", database_available=False, message=str(exc))
    except Exception:
        logger.exception("Health check failed")
        return HealthResponse(status="unavailable", database_available=False, message="Veritabanı okunamadı.")
