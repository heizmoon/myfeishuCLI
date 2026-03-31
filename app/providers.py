from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import settings


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderResult:
    provider: str
    model: str
    text: str


async def ask_openai(prompt: str) -> ProviderResult:
    if not settings.openai_api_key:
        raise ProviderError("OPENAI_API_KEY is not configured.")

    payload = {
        "model": settings.openai_model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": settings.bot_system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/responses",
            headers=headers,
            json=payload,
        )

    response.raise_for_status()
    data = response.json()
    text = data.get("output_text", "").strip()
    if not text:
        raise ProviderError("OpenAI returned an empty response.")
    return ProviderResult(provider="openai", model=settings.openai_model, text=text)


async def ask_gemini(prompt: str) -> ProviderResult:
    if not settings.gemini_api_key:
        raise ProviderError("GEMINI_API_KEY is not configured.")

    payload = {
        "system_instruction": {"parts": [{"text": settings.bot_system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            (
                f"{settings.gemini_base_url.rstrip('/')}/v1beta/models/"
                f"{settings.gemini_model}:generateContent"
            ),
            params={"key": settings.gemini_api_key},
            json=payload,
        )

    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates") or []
    parts = []
    for candidate in candidates:
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            text = (part.get("text") or "").strip()
            if text:
                parts.append(text)
    text = "\n".join(parts).strip()
    if not text:
        raise ProviderError("Gemini returned an empty response.")
    return ProviderResult(provider="gemini", model=settings.gemini_model, text=text)


async def ask_provider(provider: str, prompt: str) -> ProviderResult:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return await ask_openai(prompt)
    if normalized == "gemini":
        return await ask_gemini(prompt)
    raise ProviderError(f"Unsupported provider: {provider}")
