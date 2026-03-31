from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from app.config import settings
from app.feishu import FeishuClient, extract_message, verify_token
from app.providers import ProviderError, ask_provider

app = FastAPI(title="Feishu Multi-Model Bot")
feishu_client = FeishuClient()


def route_message(text: str) -> tuple[str, str]:
    raw = text.strip()
    lowered = raw.lower()

    prefixes = [
        ("gpt:", "openai"),
        ("/gpt ", "openai"),
        ("gemini:", "gemini"),
        ("/gemini ", "gemini"),
    ]
    for prefix, provider in prefixes:
        if lowered.startswith(prefix):
            return provider, raw[len(prefix) :].strip()

    return settings.bot_default_provider, raw


@app.get("/")
async def index() -> dict:
    return {
        "ok": True,
        "service": "feishu-multi-model-bot",
        "providers": ["openai", "gemini"],
    }


@app.post("/webhook/feishu")
async def feishu_webhook(request: Request) -> dict:
    payload = await request.json()

    if payload.get("type") == "url_verification":
        if not verify_token(payload):
            raise HTTPException(status_code=401, detail="Invalid verification token.")
        return {"challenge": payload.get("challenge")}

    if not verify_token(payload):
        raise HTTPException(status_code=401, detail="Invalid verification token.")

    message = extract_message(payload)
    if not message:
        return {"ok": True, "ignored": True}

    if message.sender_type == "app":
        return {"ok": True, "ignored": "self_message"}

    provider, prompt = route_message(message.text)
    if not prompt:
        return {"ok": True, "ignored": "empty_prompt"}

    try:
        result = await ask_provider(provider, prompt)
        reply = f"[{result.provider}/{result.model}]\n{result.text}"
    except ProviderError as exc:
        reply = f"[error] {exc}"
    except Exception as exc:  # pragma: no cover
        reply = f"[error] Unexpected failure: {exc}"

    await feishu_client.send_text_message(message.chat_id, reply[:4000])
    return {"ok": True}
