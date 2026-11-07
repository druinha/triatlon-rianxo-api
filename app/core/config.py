from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    site_url: str = "http://localhost:4321"
    allowed_origins: str = "http://localhost:4321"
    cookie_secure: bool = True
    # Só en desenvolvemento (web en localhost:4321 e API en localhost:8001). En produción, baleiro.
    cors_origins: str = ""

    cookie_name: str = "tr_session"
    session_days: int = 30
    invitation_days: int = 7
    reset_hours: int = 48
    consent_version: str = "2026-11"

    login_window_minutes: int = 15
    login_max_email_failures: int = 5
    login_max_ip_failures: int = 30

    password_min_length: int = 8

    # Fotos de perfil (no disco do servidor, fóra da web pública: sérveas a API só a membros)
    media_dir: str = "./media"
    # A web xa a comprime antes de enviala; este límite só cobre navegadores que non poden
    photo_max_mb: int = 25

    @property
    def cors_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def origins(self) -> set[str]:
        return {o.strip().rstrip("/") for o in self.allowed_origins.split(",") if o.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
