from fastapi import FastAPI
from app.api.news import router as news_router

app = FastAPI(title="ETF Portfolio Advisor Backend")

app.include_router(news_router, prefix="/api/news", tags=["news"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ETF Portfolio Advisor Backend"}
