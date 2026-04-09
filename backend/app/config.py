from __future__ import annotations

from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        case_sensitive=False,
    )

    app_name: str = "Tarifas Moviles API"
    csv_path: Path = Path("../05_tarifas_servicios_moviles_febrero26_gustavo.csv")
    parquet_path: Path = Path("./cache/tarifas_servicios_moviles.parquet")
    allowed_statuses_raw: str = Field(default="VIGENTE")
    include_por_iniciar: bool = False
    cors_allow_origins: str = "*"
    default_page_size: int = 20
    max_page_size: int = 100

    @cached_property
    def allowed_statuses(self) -> list[str]:
        statuses = [
            item.strip().upper()
            for item in self.allowed_statuses_raw.split(",")
            if item.strip()
        ]
        if self.include_por_iniciar and "POR-INICIAR-VIGENCIA" not in statuses:
            statuses.append("POR-INICIAR-VIGENCIA")
        return statuses or ["VIGENTE"]

    @cached_property
    def cors_origins(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_origins.split(",") if item.strip()]


settings = Settings()
