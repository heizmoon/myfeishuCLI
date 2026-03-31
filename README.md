# Feishu Multi-Model Bot

一个最小可用的飞书群机器人服务，支持文本对话和 Gemini 生图。

## 支持的群指令

- `gpt: 你的问题` 或 `/gpt 你的问题` -> OpenAI 文本回复
- `gemini: 你的问题` 或 `/gemini 你的问题` -> Gemini 文本回复
- `gemini-img: 你的提示词` 或 `/gemini-img 你的提示词` -> Gemini 生图并发到群里
- 不带前缀时走 `.env` 里的 `BOT_DEFAULT_PROVIDER`

## 安装

```powershell
uv sync
```

## 环境变量

先复制模板：

```powershell
Copy-Item .env.example .env
```

至少填好这些值：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_VERIFICATION_TOKEN`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

Gemini 生图默认使用：

- `GEMINI_IMAGE_MODEL=gemini-2.5-flash-image`

## 启动

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 飞书配置

在飞书开放平台中：

1. 开启事件订阅
2. 请求地址填 `https://你的域名/webhook/feishu`
3. `Verification Token` 与 `.env` 中保持一致
4. 添加事件 `im.message.receive_v1`
5. 开通消息相关权限
6. 把机器人拉进测试群

## 群里怎么用

```text
gpt: 帮我总结今天的讨论
gemini: 给我一个更激进的方案
gemini-img: 画一只戴墨镜的柴犬，像旅行海报
```

## 说明

当前实现是“一个飞书机器人，背后接多个模型”。如果你想让群里出现多个不同头像的机器人，需要在飞书开放平台再创建多个应用。
