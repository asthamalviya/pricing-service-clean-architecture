"""
v1 FastAPI application using clean architecture.

Key improvements over v0:
- Service layer separates business logic from HTTP
- Repository pattern abstracts data access
- Strategy pattern for pricing rules
- Dependency injection via constructor
- Proper input validation with Pydantic
- Testable without HTTP infrastructure
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from v1.pricing_service import PricingService
from v1.clock import SystemClock
from v1.repositories import FileConfigRepository, FileInvoiceRepository
from v1.models import QuoteRequest, Quote
from v1.pricing_rules import UnknownPlanError, UnknownRegionError

app = FastAPI(title="QuickQuote Pricing API (v1)")

# Initialize dependencies
clock = SystemClock()
config_repo = FileConfigRepository("pricing_config.json")
invoice_repo = FileInvoiceRepository("invoices.json")
pricing_service = PricingService(clock, config_repo, invoice_repo)


@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "version": "v1"}


@app.post("/quote", response_model=Quote)
def quote(request: QuoteRequest):
    """
    Calculate a price quote and save an invoice.

    Validates input automatically via Pydantic.
    Returns proper HTTP status codes on errors.
    """
    try:
        return pricing_service.calculate_quote(request)
    except UnknownPlanError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnknownRegionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """
    Custom handler for Pydantic validation errors.
    Returns clear error messages for invalid input.
    """
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid input", "errors": exc.errors()},
    )
