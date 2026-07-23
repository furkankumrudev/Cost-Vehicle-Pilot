"""Valuation endpoint backed by the existing market-analysis engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..database import ListingRepository
from ..dependencies import safe_repository
from ..schemas import ValuationRequest, ValuationResponse
from ..services.market_service import valuation

router = APIRouter(prefix="/api", tags=["valuation"])


@router.post("/valuation", response_model=ValuationResponse)
def create_valuation(payload: ValuationRequest, repository: ListingRepository = Depends(safe_repository)) -> ValuationResponse:
    return ValuationResponse(**valuation(repository, payload.model_dump()))
