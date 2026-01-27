from fastapi import FastAPI

app = FastAPI(title="ETF Portfolio Advisor Backend")

@app.get("/")
def read_root():
    return {"message": "Welcome to ETF Portfolio Advisor Backend"}
