# Claw Cloud 部署指南

目标：把当前项目部署到 Ubuntu 24.04 VPS，并通过 `https://120061019.xyz/webhook/feishu` 给飞书开放平台回调。

## 0. 前提

- 服务器系统：Ubuntu 24.04
- 域名：`120061019.xyz`
- 服务器 IP：`47.251.64.101`
- 运行用户：`root`

建议先把 Cloudflare 中该域名的 DNS `A` 记录指向 `47.251.64.101`。

## 1. 服务器初始化

```bash
apt update
apt install -y git curl nginx python3 python3-venv python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

为避免每次手动加 PATH：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 2. 上传项目

如果你已经把项目放到 Git 仓库：

```bash
cd /opt
git clone <你的仓库地址> feishu-bot
cd /opt/feishu-bot
```

如果还没有仓库，也可以本地打包后上传到服务器，再解压到 `/opt/feishu-bot`。

## 3. 配置环境变量

复制模板：

```bash
cd /opt/feishu-bot
cp .env.example .env
```

编辑 `.env`：

```env
FEISHU_APP_ID=你的AppID
FEISHU_APP_SECRET=你的AppSecret
FEISHU_VERIFICATION_TOKEN=feishu-bot-demo-2026
FEISHU_BASE_URL=https://open.feishu.cn

OPENAI_API_KEY=你的OpenAIKey
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini

GEMINI_API_KEY=你重新生成后的GeminiKey
GEMINI_MODEL=gemini-2.5-flash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com

BOT_DEFAULT_PROVIDER=openai
BOT_SYSTEM_PROMPT=You are a helpful assistant in a Feishu group. Keep replies concise and practical.

HOST=127.0.0.1
PORT=8000
```

## 4. 安装依赖并本地启动验证

```bash
cd /opt/feishu-bot
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

新开一个 SSH 窗口测试：

```bash
curl http://127.0.0.1:8000/
```

看到 `{"ok":true,...}` 说明服务正常。

## 5. 配置 systemd 常驻

创建服务文件：

```bash
cat >/etc/systemd/system/feishu-bot.service <<'EOF'
[Unit]
Description=Feishu Multi Model Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/feishu-bot
Environment=PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/root/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启动并设置开机自启：

```bash
systemctl daemon-reload
systemctl enable --now feishu-bot
systemctl status feishu-bot
```

看日志：

```bash
journalctl -u feishu-bot -f
```

## 6. 配置 Nginx

创建站点配置：

```bash
cat >/etc/nginx/sites-available/feishu-bot <<'EOF'
server {
    listen 80;
    server_name 120061019.xyz;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

启用配置：

```bash
ln -sf /etc/nginx/sites-available/feishu-bot /etc/nginx/sites-enabled/feishu-bot
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

## 7. Cloudflare 配置

在 Cloudflare 里：

- 添加或修改 `A` 记录：`120061019.xyz -> 47.251.64.101`
- 先保持橙云开启也可以
- SSL/TLS 建议设为 `Full` 或 `Full (strict)`

如果源站暂时没配证书，也可以先用 `Flexible` 临时验证，但长期不推荐。

## 8. 验证域名访问

```bash
curl http://127.0.0.1:8000/
curl http://120061019.xyz/
curl https://120061019.xyz/
```

正常时首页会返回 JSON。

回调地址就是：

```text
https://120061019.xyz/webhook/feishu
```

## 9. 飞书开放平台配置

在你的飞书应用里：

1. 打开事件订阅
2. 请求地址填 `https://120061019.xyz/webhook/feishu`
3. Verification Token 填 `.env` 里的 `FEISHU_VERIFICATION_TOKEN`
4. 添加事件 `im.message.receive_v1`
5. 打开机器人能力并把机器人拉进测试群
6. 配置消息相关权限

## 10. 测试

群里发：

```text
gpt: 你好，介绍一下你自己
gemini: 用三句话总结今天的重点
```

## 11. 常用运维命令

重启服务：

```bash
systemctl restart feishu-bot
```

看服务状态：

```bash
systemctl status feishu-bot
```

看日志：

```bash
journalctl -u feishu-bot -n 100 --no-pager
```

测试 Nginx：

```bash
nginx -t
```
