from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin,
    admin_rules,
    analysis,
    auth,
    blockchain,
    documents,
    properties,
    reports,
    review,
    rules,
)

Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
# Schema is owned by Alembic: run `python -m alembic upgrade head` (no create_all here).

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
app.include_router(admin.router)
app.include_router(admin_rules.router)
app.include_router(rules.router)
app.include_router(review.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "components": {
            "api": "ready",
            "database": "connected",
            # Engine selection is read from backend/.env; report the same names
            # the pipeline resolves so the running configuration is visible.
            "ocr_pipeline": settings.ocr_engine,
            "doc_classifier": settings.doc_classifier_engine,
            "nlp_extractor": settings.nlp_extractor_engine,
            "cross_validator": settings.cross_validator_engine,
            "ownership_builder": settings.ownership_builder_engine,
            "rule_engine": settings.rule_engine,
            "blockchain": "mock" if settings.blockchain_mock_mode else "evm",
        },
    }
