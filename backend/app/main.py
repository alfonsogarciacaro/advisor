from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.news import router as news_router
from app.api.agents import router as agents_router
from app.api.portfolio import router as portfolio_router
from app.api.plans import router as plans_router
from app.api.auth import router as auth_router
from app.api.strategies import router as strategies_router
from app.api.admin import router as admin_router
from app.core.logging import setup_logging
from app.core.dependencies import get_config_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Initialize ConfigService (load from Storage/YAML)
    config_service = get_config_service()
    await config_service.initialize()
    yield

app = FastAPI(title="ETF Portfolio Advisor Backend", lifespan=lifespan)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(plans_router, prefix="/api", tags=["plans"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(strategies_router, prefix="/api", tags=["strategies", "config"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ETF Portfolio Advisor Backend"}
