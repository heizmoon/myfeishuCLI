# Feishu Multi-Model Bot

一个最小可用的飞书群机器人服务，支持把群消息路由到不同模型：

- `gpt: 你的问题` 或 `/gpt 你的问题` -> OpenAI
- `gemini: 你的问题` 或 `/gemini 你的问题` -> Gemini
- 不带前缀时走 `.env` 里的 `BOT_DEFAULT_PROVIDER`

这个项目和 `lark-cli` 不冲突。`lark-cli` 负责帮你快速验证飞书权限、查 API、调试消息能力；这个服务负责长期在线接群消息并转发给模型。

## 1. 安装依赖

推荐用 `uv`：

```powershell
uv sync
```

也可以用 `pip`：

```powershell
pip install -e .
```

## 2. 配置环境变量

先复制一份环境变量模板：

```powershell
Copy-Item .env.example .env
```

必填项：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_VERIFICATION_TOKEN`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

可选项：

- `OPENAI_MODEL`
- `GEMINI_MODEL`
- `BOT_DEFAULT_PROVIDER`
- `BOT_SYSTEM_PROMPT`

## 3. 启动服务

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后本地健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

## 4. 飞书开放平台配置

在你的飞书应用里做这些事：

1. 开启事件订阅
2. 请求地址填 `https://你的域名/webhook/feishu`
3. Verification Token 填到 `.env` 的 `FEISHU_VERIFICATION_TOKEN`
4. 订阅事件 `im.message.receive_v1`
5. 给应用开通发送消息所需权限
6. 把应用机器人拉进你的测试群

建议先不要开加密，先把最小链路跑通。

## 5. 群里怎么用

在群里发：

```text
gpt: 帮我总结今天这段对话
gemini: 给我一个更激进的方案
```

机器人会把对应模型的结果发回群里。

## 6. 重要说明

当前实现是“一个飞书机器人，背后接多个模型”。如果你想要“GPT 和 Gemini 各自是群里的独立机器人身份”，需要在飞书里创建多个应用，或者再加一层消息分发服务。

另外，公开群里接入模型前，建议先只在测试群验证，严格控制飞书权限和模型 API Key 的使用范围。
