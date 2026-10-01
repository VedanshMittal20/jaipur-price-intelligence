"""FastAPI application for the Jaipur Real Estate Price Intelligence Platform."""

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import (
    CounterfactualResponse,
    DealSummary,
    LocalitySummary,
    ModelMetaResponse,
    PricePredictionResponse,
    PropertyRequest,
)
from api.services.model_service import ModelService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context loading machine learning artifacts into application state."""
    app.state.service = ModelService()
    yield
    # Cleanup if needed
    del app.state.service


app = FastAPI(
    title="Jaipur Real Estate Price Intelligence API",
    description=(
        "Production ML API estimating fair asking prices for Jaipur residential properties, "
        "with calibrated Mondrian conformal intervals and exact multiplicative factor explanations."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service(request: Request) -> ModelService:
    """Dependency provider for the warm ModelService singleton."""
    return request.app.state.service


@app.get("/health", tags=["System"])
def health_check(service: ModelService = Depends(get_service)):
    """Liveness and readiness health check."""
    return {
        "status": "healthy",
        "service": "jaipur-price-intelligence",
        "model_version": "2.0.0",
        "features_loaded": service.booster.num_feature(),
    }


@app.get("/meta/model", response_model=ModelMetaResponse, tags=["Metadata"])
def get_model_metadata(service: ModelService = Depends(get_service)):
    """Retrieve model training metadata, spatial CV metrics, and conformal coverage."""
    return service.get_metadata()


@app.get("/localities", response_model=List[LocalitySummary], tags=["Geospatial"])
def list_localities(service: ModelService = Depends(get_service)):
    """List all canonical Jaipur residential micro-markets with coordinates, medians, and DLC rates."""
    return service.get_localities()


@app.get("/deals", response_model=List[DealSummary], tags=["Intelligence"])
def list_deals(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of deals to return"),
    service: ModelService = Depends(get_service),
):
    """List market listings priced at least 15% below predicted fair algorithmic valuation."""
    return service.get_deals(limit=limit)


@app.post("/predict", response_model=PricePredictionResponse, tags=["Inference"])
def predict_price(
    request: PropertyRequest,
    service: ModelService = Depends(get_service),
):
    """Predict fair asking price with 80% conformal interval and exact factor breakdown."""
    return service.predict_property(request)


@app.post("/counterfactual", response_model=CounterfactualResponse, tags=["Inference"])
def evaluate_counterfactuals(
    request: PropertyRequest,
    service: ModelService = Depends(get_service),
):
    """Evaluate hypothetical what-if property modifications against baseline fair value."""
    return service.compute_counterfactuals(request)


# Mount static production web app if built
from pathlib import Path
from fastapi.staticfiles import StaticFiles

dist_dir = Path(__file__).resolve().parent.parent / "web" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

