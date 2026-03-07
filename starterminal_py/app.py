import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from starterminal_py.models import (
    BalanceResponse,
    ConfirmTopUpRequest,
    NfcScanRequest,
    RegisterCardRequest,
    TopUpRequest,
    WithdrawRequest,
)
from starterminal_py.storage import Storage
from starterminal_py.telegram_service import TelegramService

app = FastAPI(title="Starterminal Python API", version="1.1.0")
storage = Storage()
telegram = TelegramService()

BASE_DIR = Path(__file__).resolve().parent
UI_FILE = BASE_DIR / "ui" / "index.html"


@app.get("/")
def ui_home():
    return FileResponse(UI_FILE)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/card/register")
def register_card(payload: RegisterCardRequest):
    if storage.get_card(payload.card_id):
        raise HTTPException(status_code=409, detail="Картка вже існує")
    storage.register_card(payload.card_id, payload.owner_name, payload.pin, payload.telegram_chat_id)
    return {"ok": True, "message": "Картку створено"}


@app.post("/nfc/scan")
def nfc_scan(payload: NfcScanRequest):
    card = storage.get_card(payload.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Картку не знайдено")
    storage.log_event(payload.card_id, "nfc_scan", None)
    return {"ok": True, "card_id": payload.card_id, "owner": card.owner_name, "balance": card.balance}


@app.get("/card/{card_id}/balance", response_model=BalanceResponse)
def get_balance(card_id: str):
    balance = storage.get_balance(card_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="Картку не знайдено")
    return BalanceResponse(card_id=card_id, balance=balance)


@app.post("/card/topup/request")
def request_topup(payload: TopUpRequest):
    card = storage.get_card(payload.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Картку не знайдено")

    code = f"{secrets.randbelow(1_000_000):06d}"
    storage.set_pending_topup(payload.card_id, payload.amount, code)
    telegram.send_confirmation_code(card.telegram_chat_id, payload.card_id, code)
    return {"ok": True, "message": "Код підтвердження відправлено"}


@app.post("/card/topup/confirm")
def confirm_topup(payload: ConfirmTopUpRequest):
    ok, message = storage.confirm_topup(payload.card_id, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": True, "message": message, "balance": storage.get_balance(payload.card_id)}


@app.post("/card/withdraw")
def withdraw(payload: WithdrawRequest):
    if not storage.verify_pin(payload.card_id, payload.pin):
        raise HTTPException(status_code=401, detail="Невірний PIN")
    ok, message = storage.withdraw(payload.card_id, payload.amount)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": True, "message": message, "balance": storage.get_balance(payload.card_id)}
