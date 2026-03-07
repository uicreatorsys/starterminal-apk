import hashlib
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path("starterminal.db")


@dataclass
class Card:
    card_id: str
    owner_name: str
    pin_hash: str
    pin_salt: str
    balance: int
    telegram_chat_id: str | None


class Storage:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cards (
                    card_id TEXT PRIMARY KEY,
                    owner_name TEXT NOT NULL,
                    pin_hash TEXT NOT NULL,
                    pin_salt TEXT NOT NULL,
                    balance INTEGER NOT NULL DEFAULT 0,
                    telegram_chat_id TEXT
                );

                CREATE TABLE IF NOT EXISTS pending_topups (
                    card_id TEXT PRIMARY KEY,
                    amount INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    amount INTEGER,
                    created_at INTEGER NOT NULL
                );
                """
            )

    @staticmethod
    def hash_pin(pin: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{pin}".encode()).hexdigest()

    def register_card(self, card_id: str, owner_name: str, pin: str, telegram_chat_id: str | None) -> None:
        salt = secrets.token_hex(8)
        pin_hash = self.hash_pin(pin, salt)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO cards(card_id, owner_name, pin_hash, pin_salt, telegram_chat_id) VALUES(?,?,?,?,?)",
                (card_id, owner_name, pin_hash, salt, telegram_chat_id),
            )
            self.log_event(card_id, "card_registered", None, conn)

    def get_card(self, card_id: str) -> Card | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM cards WHERE card_id=?", (card_id,)).fetchone()
            if not row:
                return None
            return Card(**dict(row))

    def verify_pin(self, card_id: str, pin: str) -> bool:
        card = self.get_card(card_id)
        if not card:
            return False
        return self.hash_pin(pin, card.pin_salt) == card.pin_hash

    def get_balance(self, card_id: str) -> int | None:
        with self._connect() as conn:
            row = conn.execute("SELECT balance FROM cards WHERE card_id=?", (card_id,)).fetchone()
            return row["balance"] if row else None

    def set_pending_topup(self, card_id: str, amount: int, code: str, ttl_seconds: int = 120) -> None:
        expires_at = int(time.time()) + ttl_seconds
        with self._connect() as conn:
            conn.execute(
                "REPLACE INTO pending_topups(card_id, amount, code, expires_at) VALUES(?,?,?,?)",
                (card_id, amount, code, expires_at),
            )
            self.log_event(card_id, "topup_requested", amount, conn)

    def confirm_topup(self, card_id: str, code: str) -> tuple[bool, str]:
        now = int(time.time())
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM pending_topups WHERE card_id=?", (card_id,)).fetchone()
            if not row:
                return False, "Немає активного поповнення"
            if row["expires_at"] < now:
                conn.execute("DELETE FROM pending_topups WHERE card_id=?", (card_id,))
                return False, "Код прострочений"
            if row["code"] != code:
                return False, "Невірний код"

            amount = row["amount"]
            conn.execute("UPDATE cards SET balance = balance + ? WHERE card_id=?", (amount, card_id))
            conn.execute("DELETE FROM pending_topups WHERE card_id=?", (card_id,))
            self.log_event(card_id, "topup_confirmed", amount, conn)
            return True, "Поповнення успішне"

    def withdraw(self, card_id: str, amount: int) -> tuple[bool, str]:
        with self._connect() as conn:
            row = conn.execute("SELECT balance FROM cards WHERE card_id=?", (card_id,)).fetchone()
            if not row:
                return False, "Картку не знайдено"
            if row["balance"] < amount:
                return False, "Недостатньо коштів"
            conn.execute("UPDATE cards SET balance = balance - ? WHERE card_id=?", (amount, card_id))
            self.log_event(card_id, "withdraw", amount, conn)
            return True, "Зняття успішне"

    def log_event(self, card_id: str, event_type: str, amount: int | None, conn: sqlite3.Connection | None = None) -> None:
        target = conn if conn else self._connect()
        target.execute(
            "INSERT INTO events(card_id, event_type, amount, created_at) VALUES(?,?,?,?)",
            (card_id, event_type, amount, int(time.time())),
        )
        if conn is None:
            target.commit()
            target.close()
