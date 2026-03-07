import os

import httpx


class TelegramService:
    """Optional Telegram notifier via Bot API (token from env TELEGRAM_BOT_TOKEN)."""

    def __init__(self) -> None:
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    def _send(self, chat_id: str, text: str) -> None:
        if not self.bot_token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            httpx.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
        except Exception:
            # Demo mode: ignore errors silently
            pass

    def send_event(self, chat_id: str | None, text: str) -> None:
        if not chat_id:
            return
        self._send(chat_id, text)
