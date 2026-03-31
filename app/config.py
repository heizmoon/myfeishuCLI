import os
from dataclasses import dataclass

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class BotProfile:
    slug: str
    app_id: str
    app_secret: str
    verification_token: str
    default_provider: str
    default_mode: str
    system_prompt: str
    require_mention: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_base_url: str = "https://open.feishu.cn"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    bot_default_provider: str = "openai"
    bot_system_prompt: str = (
        "You are a helpful assistant in a Feishu group. Keep replies concise and practical."
    )

    host: str = "0.0.0.0"
    port: int = 8000

    feishu_bots: str = ""


settings = Settings()
dotenv_map = {
    str(key): str(value)
    for key, value in dotenv_values(".env").items()
    if key is not None and value is not None
}


def _env_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return dotenv_map.get(name, default)


def _env_bool(name: str, default: bool) -> bool:
    value = _env_value(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_default_bot() -> BotProfile | None:
    if not (settings.feishu_app_id and settings.feishu_app_secret and settings.feishu_verification_token):
        return None
    return BotProfile(
        slug="default",
        app_id=settings.feishu_app_id,
        app_secret=settings.feishu_app_secret,
        verification_token=settings.feishu_verification_token,
        default_provider=settings.bot_default_provider,
        default_mode="text",
        system_prompt=settings.bot_system_prompt,
        require_mention=False,
    )


def get_named_bot(slug: str) -> BotProfile | None:
    key = slug.strip().upper().replace("-", "_")
    app_id = _env_value(f"BOT_{key}_FEISHU_APP_ID", "").strip()
    app_secret = _env_value(f"BOT_{key}_FEISHU_APP_SECRET", "").strip()
    verification_token = _env_value(f"BOT_{key}_FEISHU_VERIFICATION_TOKEN", "").strip()
    if not (app_id and app_secret and verification_token):
        return None

    default_provider = _env_value(f"BOT_{key}_DEFAULT_PROVIDER", "").strip() or settings.bot_default_provider
    default_mode = _env_value(f"BOT_{key}_DEFAULT_MODE", "").strip() or "text"
    system_prompt = _env_value(f"BOT_{key}_SYSTEM_PROMPT", "").strip() or settings.bot_system_prompt
    require_mention = _env_bool(f"BOT_{key}_REQUIRE_MENTION", True)

    return BotProfile(
        slug=slug,
        app_id=app_id,
        app_secret=app_secret,
        verification_token=verification_token,
        default_provider=default_provider,
        default_mode=default_mode,
        system_prompt=system_prompt,
        require_mention=require_mention,
    )


def get_enabled_bot_slugs() -> list[str]:
    raw = settings.feishu_bots.strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]
