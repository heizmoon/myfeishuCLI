import asyncio
import os
from unittest.mock import AsyncMock

from app.main import get_bot_or_404, route_for_bot
from app.feishu import extract_message, FeishuClient
from app.config import BotProfile

os.environ["BOT_FEIFEI_FEISHU_APP_ID"] = "cli_feifei"
os.environ["BOT_FEIFEI_FEISHU_APP_SECRET"] = "feifei_secret"
os.environ["BOT_FEIFEI_FEISHU_VERIFICATION_TOKEN"] = "feifei_token"
os.environ["BOT_FEIFEI_REQUIRE_MENTION"] = "true"

os.environ["BOT_XIAOBAI_FEISHU_APP_ID"] = "cli_xiaobai"
os.environ["BOT_XIAOBAI_FEISHU_APP_SECRET"] = "xiaobai_secret"
os.environ["BOT_XIAOBAI_FEISHU_VERIFICATION_TOKEN"] = "xiaobai_token"
os.environ["BOT_XIAOBAI_REQUIRE_MENTION"] = "true"

async def test():
    # Simulate Feishu event where ONLY feifei is mentioned
    payload = {
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "message": {
                "chat_type": "group",
                "message_type": "text",
                "content": '{"text": "@feifei hello"}',
                "mentions": [
                    {
                        "key": "@feifei",
                        "id": {"union_id": "on_feifei", "open_id": "ou_feifei"}
                    }
                ]
            }
        }
    }
    message = extract_message(payload)
    print(f"Extracted mention IDs: {message.mention_ids}")

    # Test Xiaobai's logic
    bot = get_bot_or_404("xiaobai")
    print(f"Xiaobai require_mention? {bot.require_mention}")
    
    feishu_client = FeishuClient(bot)
    feishu_client.get_bot_info = AsyncMock(return_value={"open_id": "ou_xiaobai", "union_id": "on_xiaobai"})
    
    if message.chat_type == "group" and bot.require_mention:
        bot_info = await feishu_client.get_bot_info()
        valid_ids = {bot.app_id, bot_info.get("open_id"), bot_info.get("union_id")}
        
        match = any(vid in message.mention_ids for vid in valid_ids if vid)
        print(f"valid_ids: {valid_ids}")
        print(f"Xiaobai Match result: {match}")
        if not match:
            print("Xiaobai successfully IGNORED the message.")
        else:
            print("ERROR: Xiaobai processed the message!")

asyncio.run(test())
