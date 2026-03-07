from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from starterminal_py.models import (
    BalanceResponse,
    NfcScanRequest,
    RegisterCardRequest,
    TerminalCodeVerifyRequest,
    TopUpRequest,
    WithdrawRequest,
)
from starterminal_py.storage import Storage
from starterminal_py.telegram_service import TelegramService

app = FastAPI(title="Starterminal Python API", version="1.2.0")
storage = Storage()
telegram = TelegramService()

BASE_DIR = Path(__file__).resolve().parent
UI_FILE = BASE_DIR / "ui" / "index.html"


def normalize_card_id(card_id: str) -> str:
    return card_id.replace(" ", "").replace("_", "")


@app.get("/")
def ui_home():
    return FileResponse(UI_FILE)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/terminal/start")
def terminal_start():
    code = storage.start_terminal_session()
    return {"ok": True, "code": code, "message": "Код терміналу згенеровано"}


@app.post("/terminal/verify")
def terminal_verify(payload: TerminalCodeVerifyRequest):
    ok, message = storage.verify_terminal_code(payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": True, "message": message}


@app.post("/card/register")
def register_card(payload: RegisterCardRequest):
    card_id = normalize_card_id(payload.card_id)
    if storage.get_card(card_id):
        raise HTTPException(status_code=409, detail="Картка вже існує")
    storage.register_card(card_id, payload.owner_name, payload.pin, payload.telegram_chat_id)
    telegram.send_event(payload.telegram_chat_id, f"Starterminal: створено карту {card_id}")
    return {"ok": True, "message": "Картку створено", "card_id": card_id}


@app.post("/nfc/scan")
def nfc_scan(payload: NfcScanRequest):
    card_id = normalize_card_id(payload.card_id)
    card = storage.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Картку не знайдено")
    storage.log_event(card_id, "nfc_scan", None)
    return {"ok": True, "card_id": card_id, "owner": card.owner_name, "balance": card.balance}


@app.get("/card/{card_id}/balance", response_model=BalanceResponse)
def get_balance(card_id: str):
    normalized = normalize_card_id(card_id)
    balance = storage.get_balance(normalized)
    if balance is None:
        raise HTTPException(status_code=404, detail="Картку не знайдено")
    return BalanceResponse(card_id=normalized, balance=balance)


@app.post("/card/topup")
def topup(payload: TopUpRequest):
    if not storage.is_terminal_verified():
        raise HTTPException(status_code=403, detail="Спершу підтвердіть код терміналу")
    card_id = normalize_card_id(payload.card_id)
    card = storage.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Картку не знайдено")
    ok, message = storage.topup(card_id, payload.amount)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    telegram.send_event(card.telegram_chat_id, f"Starterminal: +{payload.amount} на карту {card_id}")
    return {"ok": True, "message": message, "balance": storage.get_balance(card_id)}


@app.post("/card/withdraw")
def withdraw(payload: WithdrawRequest):
    if not storage.is_terminal_verified():
        raise HTTPException(status_code=403, detail="Спершу підтвердіть код терміналу")
    card_id = normalize_card_id(payload.card_id)
    if not storage.verify_pin(card_id, payload.pin):
        raise HTTPException(status_code=401, detail="Невірний PIN")
    ok, message = storage.withdraw(card_id, payload.amount)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    card = storage.get_card(card_id)
    if card:
        telegram.send_event(card.telegram_chat_id, f"Starterminal: -{payload.amount} з карти {card_id}")
    return {"ok": True, "message": message, "balance": storage.get_balance(card_id)}
