# Feishu Multi-Model Bot

Supports two deployment styles:

- Multi bot: recommended. Multiple Feishu bots in the same group, each with its own avatar and callback path
- Single bot: optional legacy mode if you still want prefix routing

## Single-bot commands

- `gpt: ...` -> OpenAI text
- `gemini: ...` -> Gemini text
- `gemini-img: ...` -> Gemini image generation

## Multi-bot mode

Create multiple Feishu apps, for example:

- `菲菲`
- `小白`

Point each app to a different callback path:

- `https://bot.120061019.xyz/webhook/feishu/feifei`
- `https://bot.120061019.xyz/webhook/feishu/xiaobai`

Then configure matching environment variables:

- `BOT_FEIFEI_FEISHU_APP_ID`
- `BOT_FEIFEI_FEISHU_APP_SECRET`
- `BOT_FEIFEI_FEISHU_VERIFICATION_TOKEN`
- `BOT_XIAOBAI_*`

Recommended defaults:

- `BOT_FEIFEI_DEFAULT_PROVIDER=gemini`
- `BOT_XIAOBAI_DEFAULT_MODE=image`

In group chats, named bots only reply when they are `@` mentioned.

## Setup

```powershell
uv sync
Copy-Item .env.example .env
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Required env vars

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

For multi-bot mode:

- `FEISHU_BOTS=feifei,xiaobai`
- each `BOT_<NAME>_...` credential set

Legacy single-bot mode only:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_VERIFICATION_TOKEN`

## Example prompts

Single bot:

```text
gpt: summarize this discussion
gemini: give me a more aggressive plan
gemini-img: draw a shiba inu travel poster
```

Multi bot:

- `@菲菲 summarize this discussion`
- `@小白 draw a shiba inu travel poster`
