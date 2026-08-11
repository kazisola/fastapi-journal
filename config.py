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

    reset_token_expire_minutes: int = 60
    # Email config
    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@fastapiblog.com"
    mail_use_tls: bool = True

    frontend_url: str = "http://127.0.0.1:8000"

settings = Settings() # type: ignore