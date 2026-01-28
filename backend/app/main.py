from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.news import router as news_router
from app.api.agents import router as agents_router
from app.api.portfolio import router as portfolio_router
from app.core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(title="ETF Portfolio Advisor Backend", lifespan=lifespan)

app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ETF Portfolio Advisor Backend"}
