class TelegramService:
    """Demo sender: prints code. Replace with real Telegram Bot API later."""

    def send_confirmation_code(self, chat_id: str | None, card_id: str, code: str) -> None:
        destination = chat_id or "NO_CHAT_ID"
        print(f"[TELEGRAM] to={destination} card={card_id} code={code}")
