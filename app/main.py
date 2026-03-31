from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request

from app.config import BotProfile, get_default_bot, get_enabled_bot_slugs, get_named_bot, settings
from app.feishu import FeishuClient, extract_message, verify_token
from app.providers import ProviderError, ask_provider, generate_gemini_image

app = FastAPI(title="Feishu Multi-Model Bot")


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


def route_for_bot(bot: BotProfile, text: str) -> RouteResult:
    route = route_message(text)
    if route.prompt != text.strip():
        return route
    return RouteResult(kind=bot.default_mode, provider=bot.default_provider, prompt=text.strip())


def get_bot_or_404(bot_slug: str | None) -> BotProfile:
    if not bot_slug:
        return get_default_bot()

    bot = get_named_bot(bot_slug)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Unknown bot: {bot_slug}")
    return bot


@app.get("/")
async def index() -> dict:
    return {
        "ok": True,
        "service": "feishu-multi-model-bot",
        "providers": ["openai", "gemini"],
        "bots": ["default", *get_enabled_bot_slugs()],
    }


@app.post("/webhook/feishu")
@app.post("/webhook/feishu/{bot_slug}")
async def feishu_webhook(request: Request, bot_slug: str | None = None) -> dict:
    bot = get_bot_or_404(bot_slug)
    feishu_client = FeishuClient(bot)
    payload = await request.json()

    if payload.get("type") == "url_verification":
        if not verify_token(payload, bot.verification_token):
            raise HTTPException(status_code=401, detail="Invalid verification token.")
        return {"challenge": payload.get("challenge")}

    if not verify_token(payload, bot.verification_token):
        raise HTTPException(status_code=401, detail="Invalid verification token.")

    message = extract_message(payload)
    if not message:
        return {"ok": True, "ignored": True}

    if message.sender_type == "app":
        return {"ok": True, "ignored": "self_message"}

    if message.chat_type == "group" and bot.require_mention and bot.app_id not in message.mention_ids:
        return {"ok": True, "ignored": "mention_required"}

    route = route_for_bot(bot, message.text)
    if not route.prompt:
        return {"ok": True, "ignored": "empty_prompt"}

    try:
        if route.kind == "image":
            result = await generate_gemini_image(route.prompt, system_prompt=bot.system_prompt)
            image_key = await feishu_client.upload_image(result.image_bytes)
            await feishu_client.send_text_message(
                message.chat_id,
                f"[{result.provider}/{result.model}] image prompt: {route.prompt}",
            )
            await feishu_client.send_image_message(message.chat_id, image_key)
            return {"ok": True}

        result = await ask_provider(route.provider, route.prompt, system_prompt=bot.system_prompt)
        reply = f"[{result.provider}/{result.model}]\n{result.text}"
    except ProviderError as exc:
        reply = f"[error] {exc}"
    except Exception as exc:  # pragma: no cover
        reply = f"[error] Unexpected failure: {exc}"

    await feishu_client.send_text_message(message.chat_id, reply[:4000])
    return {"ok": True}
