from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import analysis, auth, blockchain, documents, properties, reports

Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(blockchain.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "components": {
            "api": "ready",
            "database": "connected",
            "ocr_pipeline": "stub",
            "rule_engine": "stub",
            "blockchain": "mock" if settings.blockchain_mock_mode else "evm",
        },
    }
