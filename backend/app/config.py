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

    class Config:
        env_file = ".env"


settings = Settings()
