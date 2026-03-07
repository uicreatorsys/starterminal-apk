from pathlib import Path

from fastapi.testclient import TestClient

from starterminal_py import app as app_module
from starterminal_py.storage import Storage


def setup_function():
    db = Path("starterminal.db")
    if db.exists():
        db.unlink()
    app_module.storage = Storage(db)


def test_register_scan_and_balance():
    client = TestClient(app_module.app)

    r = client.post("/card/register", json={
        "card_id": "CARD1234",
        "pin": "1234",
        "owner_name": "Test User",
        "telegram_chat_id": "1",
    })
    assert r.status_code == 200

    s = client.post("/nfc/scan", json={"card_id": "CARD1234", "source": "macro"})
    assert s.status_code == 200
    assert s.json()["card_id"] == "CARD1234"

    b = client.get("/card/CARD1234/balance")
    assert b.status_code == 200
    assert b.json()["balance"] == 0


def test_topup_and_withdraw_flow():
    client = TestClient(app_module.app)
    client.post("/card/register", json={
        "card_id": "CARD5678",
        "pin": "1111",
        "owner_name": "Cash User",
    })

    req = client.post("/card/topup/request", json={"card_id": "CARD5678", "amount": 150})
    assert req.status_code == 200

    # read code directly from storage for test
    with app_module.storage._connect() as conn:
        row = conn.execute("SELECT code FROM pending_topups WHERE card_id='CARD5678'").fetchone()
    code = row["code"]

    conf = client.post("/card/topup/confirm", json={"card_id": "CARD5678", "code": code})
    assert conf.status_code == 200
    assert conf.json()["balance"] == 150

    bad_pin = client.post("/card/withdraw", json={"card_id": "CARD5678", "amount": 50, "pin": "2222"})
    assert bad_pin.status_code == 401

    ok = client.post("/card/withdraw", json={"card_id": "CARD5678", "amount": 50, "pin": "1111"})
    assert ok.status_code == 200
    assert ok.json()["balance"] == 100
