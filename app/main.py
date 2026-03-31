from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request

from app.config import settings
from app.feishu import FeishuClient, extract_message, verify_token
from app.providers import ProviderError, ask_provider, generate_gemini_image

app = FastAPI(title="Feishu Multi-Model Bot")
feishu_client = FeishuClient()


@dataclass
class RouteResult:
    kind: str
    provider: str
    prompt: str


def route_message(text: str) -> RouteResult:
    raw = text.strip()
    lowered = raw.lower()

    prefixes = [
        ("gemini-img:", "image"),
        ("/gemini-img ", "image"),
        ("gpt:", "openai"),
        ("/gpt ", "openai"),
        ("gemini:", "gemini"),
        ("/gemini ", "gemini"),
    ]
    for prefix, provider in prefixes:
        if lowered.startswith(prefix):
            kind = "image" if provider == "image" else "text"
            actual_provider = "gemini" if provider == "image" else provider
            return RouteResult(kind=kind, provider=actual_provider, prompt=raw[len(prefix) :].strip())

    return RouteResult(kind="text", provider=settings.bot_default_provider, prompt=raw)


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

    route = route_message(message.text)
    if not route.prompt:
        return {"ok": True, "ignored": "empty_prompt"}

    try:
        if route.kind == "image":
            result = await generate_gemini_image(route.prompt)
            image_key = await feishu_client.upload_image(result.image_bytes)
            await feishu_client.send_text_message(
                message.chat_id,
                f"[{result.provider}/{result.model}] image prompt: {route.prompt}",
            )
            await feishu_client.send_image_message(message.chat_id, image_key)
            return {"ok": True}

        result = await ask_provider(route.provider, route.prompt)
        reply = f"[{result.provider}/{result.model}]\n{result.text}"
    except ProviderError as exc:
        reply = f"[error] {exc}"
    except Exception as exc:  # pragma: no cover
        reply = f"[error] Unexpected failure: {exc}"

    await feishu_client.send_text_message(message.chat_id, reply[:4000])
    return {"ok": True}
