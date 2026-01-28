from fastapi import FastAPI
from app.api.news import router as news_router
from app.api.agents import router as agents_router

app = FastAPI(title="ETF Portfolio Advisor Backend")

app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ETF Portfolio Advisor Backend"}
