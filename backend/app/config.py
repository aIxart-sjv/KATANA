from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "KATANA"
    APP_VERSION: str = "0.1.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()