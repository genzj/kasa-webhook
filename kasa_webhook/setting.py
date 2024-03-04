from functools import reduce
from operator import xor

from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlugSetting(BaseModel):
    name: str
    host: str

    def __hash__(self) -> int:
        # make it hashable to use the lru_cache
        return hash(self.name) & hash(self.host)


class ApiSettings(BaseSettings):
    plugs: list[PlugSetting]
    keys: dict[str, str]
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="KASA_WEBHOOK_",
        secrets_dir="/run/secrets",
    )

    @model_validator(mode="after")  # type: ignore[ArgumentType]
    def check_key_name_match(self) -> "ApiSettings":
        valid_names = {plug.name for plug in self.plugs}
        invalid_key_names = [
            (key, name) for key, name in self.keys.items() if name not in valid_names
        ]
        if not invalid_key_names:
            return self
        violates = ", ".join(f"{name=}({key=})" for key, name in invalid_key_names)
        raise ValueError(f"unknown plugs names in key map: {violates}.")

    def __hash__(self) -> int:
        # make it hashable to use the lru_cache
        return reduce(xor, map(hash, self.plugs)) & hash(tuple(self.keys.items()))
