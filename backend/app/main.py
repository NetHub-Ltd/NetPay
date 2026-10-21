"""Minimal NetPay ASGI application for the clean backend restart."""

from fastapi import FastAPI

app = FastAPI(title="NetPay API", version="0.1.0", description="NetPay payment gateway API.", docs_url="/docs", redoc_url=None)

@app.get("/health/live", tags=["health"], summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Return success when the application process can serve requests."""
    return {"status": "ok"}

@app.get("/health/ready", tags=["health"], summary="Readiness probe")
async def readiness() -> dict[str, str]:
    """Report process readiness; dependency checks will be added with database setup."""
    return {"status": "ok"}
