from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings


class FeishuAPIError(RuntimeError):
    pass


@dataclass
class FeishuMessage:
    message_id: str
    chat_id: str
    text: str
    sender_type: str


class FeishuClient:
    def __init__(self) -> None:
        self._tenant_token = ""
        self._tenant_token_expires_at = datetime.min.replace(tzinfo=timezone.utc)

    async def _refresh_tenant_access_token(self) -> str:
        payload = {
            "app_id": settings.feishu_app_id,
            "app_secret": settings.feishu_app_secret,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.feishu_base_url.rstrip('/')}/open-apis/auth/v3/tenant_access_token/internal",
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise FeishuAPIError(f"Failed to fetch tenant_access_token: {data}")

        self._tenant_token = data["tenant_access_token"]
        expires_in = int(data.get("expire", 7200))
        self._tenant_token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=max(expires_in - 300, 60)
        )
        return self._tenant_token

    async def get_tenant_access_token(self) -> str:
        if self._tenant_token and datetime.now(timezone.utc) < self._tenant_token_expires_at:
            return self._tenant_token
        return await self._refresh_tenant_access_token()

    async def send_text_message(self, chat_id: str, text: str) -> None:
        token = await self.get_tenant_access_token()
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.feishu_base_url.rstrip('/')}/open-apis/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise FeishuAPIError(f"Failed to send message: {data}")


def verify_token(payload: dict) -> bool:
    token = payload.get("token")
    if token:
        return token == settings.feishu_verification_token

    header = payload.get("header") or {}
    event = payload.get("event") or {}
    if event.get("tenant_key") or header:
        return True
    return False


def extract_message(payload: dict) -> FeishuMessage | None:
    header = payload.get("header") or {}
    if header.get("event_type") != "im.message.receive_v1":
        return None

    event = payload.get("event") or {}
    sender = event.get("sender") or {}
    message = event.get("message") or {}
    if message.get("message_type") != "text":
        return None

    try:
        content = json.loads(message.get("content") or "{}")
    except json.JSONDecodeError:
        content = {}

    text = (content.get("text") or "").strip()
    if not text:
        return None

    return FeishuMessage(
        message_id=message.get("message_id", ""),
        chat_id=message.get("chat_id", ""),
        text=text,
        sender_type=sender.get("sender_type", ""),
    )
