from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PropChain-AI"
    database_url: str = "sqlite:///./propchain.db"
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    storage_path: str = "./storage"
    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    blockchain_mock_mode: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    # Phase 2 — document intelligence. "fake" keeps a fresh machine bootable
    # without Tesseract; dev machines select the real engines in backend/.env
    # (see the repo-root .env.example for the Tesseract paths on this box).
    ocr_engine: str = "fake"
    doc_classifier_engine: str = "fake"
    nlp_extractor_engine: str = "fake"
    cross_validator_engine: str = "fake"
    ownership_builder_engine: str = "fake"
    rule_engine: str = "fake"
    # Tesseract wiring — the binary is not on PATH on this machine.
    tesseract_cmd: str | None = None
    tessdata_prefix: str | None = None
    ocr_dpi: int = 300
    ocr_langs: str = "eng+mar"
    # Upload validation (Specs p.1: "exact upload limits are configurable").
    max_upload_mb: int = 25

    class Config:
        env_file = ".env"


settings = Settings()
