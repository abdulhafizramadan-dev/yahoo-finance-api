from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from routers import stocks, news, index, sectors

app = FastAPI(title="Yahoo Finance API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(news.router)
app.include_router(index.router)
app.include_router(sectors.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Yahoo Finance API",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

