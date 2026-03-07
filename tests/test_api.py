from pathlib import Path

from fastapi.testclient import TestClient

from starterminal_py import app as app_module
from starterminal_py.storage import Storage


def setup_function():
    db = Path("starterminal.db")
    if db.exists():
        db.unlink()
    snapshot = Path("cards_snapshot.txt")
    if snapshot.exists():
        snapshot.unlink()
    app_module.storage = Storage(db)


def activate_terminal(client: TestClient):
    start = client.post("/terminal/start")
    assert start.status_code == 200
    code = start.json()["code"]
    verify = client.post("/terminal/verify", json={"code": code})
    assert verify.status_code == 200


def test_register_scan_and_balance():
    client = TestClient(app_module.app)

    r = client.post("/card/register", json={
        "card_id": "CARD 1234 9999",
        "pin": "1234",
        "owner_name": "Test User",
        "telegram_chat_id": "1",
    })
    assert r.status_code == 200
    assert r.json()["card_id"] == "CARD12349999"

    s = client.post("/nfc/scan", json={"card_id": "CARD12349999", "source": "manual"})
    assert s.status_code == 200
    assert s.json()["card_id"] == "CARD12349999"

    b = client.get("/card/CARD12349999/balance")
    assert b.status_code == 200
    assert b.json()["balance"] == 0


def test_topup_and_withdraw_flow():
    client = TestClient(app_module.app)
    client.post("/card/register", json={
        "card_id": "4445 8878 9980 0987",
        "pin": "123",
        "owner_name": "Cash User",
    })

    # blocked until terminal code verified
    blocked = client.post("/card/topup", json={"card_id": "4445887899800987", "amount": 150})
    assert blocked.status_code == 403

    activate_terminal(client)

    top = client.post("/card/topup", json={"card_id": "4445_8878_9980_0987", "amount": 150})
    assert top.status_code == 200
    assert top.json()["balance"] == 150

    bad_pin = client.post("/card/withdraw", json={"card_id": "4445887899800987", "amount": 50, "pin": "999"})
    assert bad_pin.status_code == 401

    ok = client.post("/card/withdraw", json={"card_id": "4445887899800987", "amount": 50, "pin": "123"})
    assert ok.status_code == 200
    assert ok.json()["balance"] == 100

    snapshot = Path("cards_snapshot.txt")
    assert snapshot.exists()
    content = snapshot.read_text(encoding="utf-8")
    assert "4445887899800987" in content
