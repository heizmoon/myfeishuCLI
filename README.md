# Feishu Multi-Model Bot

Supports two deployment styles:

- Single bot: one Feishu bot, route by message prefix such as `gpt:` or `gemini:`
- Multi bot: multiple Feishu bots in the same group, each with its own avatar and callback path

## Single-bot commands

- `gpt: ...` -> OpenAI text
- `gemini: ...` -> Gemini text
- `gemini-img: ...` -> Gemini image generation

## Multi-bot mode

Create multiple Feishu apps, for example:

- `GPT`
- `Gemini`
- `Painter`

Point each app to a different callback path:

- `https://bot.120061019.xyz/webhook/feishu/gpt`
- `https://bot.120061019.xyz/webhook/feishu/gemini`
- `https://bot.120061019.xyz/webhook/feishu/painter`

Then configure matching environment variables:

- `BOT_GPT_FEISHU_APP_ID`
- `BOT_GPT_FEISHU_APP_SECRET`
- `BOT_GPT_FEISHU_VERIFICATION_TOKEN`
- `BOT_GEMINI_*`
- `BOT_PAINTER_*`

Recommended defaults:

- `BOT_GPT_DEFAULT_PROVIDER=openai`
- `BOT_GEMINI_DEFAULT_PROVIDER=gemini`
- `BOT_PAINTER_DEFAULT_MODE=image`

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

For single-bot mode:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_VERIFICATION_TOKEN`

For multi-bot mode:

- `FEISHU_BOTS=gpt,gemini,painter`
- each `BOT_<NAME>_...` credential set

## Example prompts

Single bot:

```text
gpt: summarize this discussion
gemini: give me a more aggressive plan
gemini-img: draw a shiba inu travel poster
```

Multi bot:

- `@GPT summarize this discussion`
- `@Gemini give me a more aggressive plan`
- `@Painter draw a shiba inu travel poster`
