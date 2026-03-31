from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_base_url: str = "https://open.feishu.cn"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    bot_default_provider: str = "openai"
    bot_system_prompt: str = (
        "You are a helpful assistant in a Feishu group. Keep replies concise and practical."
    )

    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
