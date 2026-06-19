from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    profile_pic_max_bytes: int = 5 * 1024 * 1024

    posts_per_page: int = 10

settings = Settings() # type: ignore