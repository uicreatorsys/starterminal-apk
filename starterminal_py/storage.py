import hashlib
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path("starterminal.db")
SNAPSHOT_PATH = Path("cards_snapshot.txt")


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

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    amount INTEGER,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS terminal_session (
                    id INTEGER PRIMARY KEY CHECK (id=1),
                    code TEXT,
                    verified INTEGER NOT NULL DEFAULT 0,
                    expires_at INTEGER NOT NULL DEFAULT 0
                );
                INSERT OR IGNORE INTO terminal_session(id, code, verified, expires_at) VALUES(1, '', 0, 0);
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
        self.export_snapshot()

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

    def topup(self, card_id: str, amount: int) -> tuple[bool, str]:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM cards WHERE card_id=?", (card_id,)).fetchone()
            if not row:
                return False, "Картку не знайдено"
            conn.execute("UPDATE cards SET balance = balance + ? WHERE card_id=?", (amount, card_id))
            self.log_event(card_id, "topup", amount, conn)
        self.export_snapshot()
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
        self.export_snapshot()
        return True, "Зняття успішне"

    def start_terminal_session(self, ttl_seconds: int = 300) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = int(time.time()) + ttl_seconds
        with self._connect() as conn:
            conn.execute(
                "UPDATE terminal_session SET code=?, verified=0, expires_at=? WHERE id=1",
                (code, expires_at),
            )
        return code

    def verify_terminal_code(self, code: str) -> tuple[bool, str]:
        with self._connect() as conn:
            row = conn.execute("SELECT code, expires_at FROM terminal_session WHERE id=1").fetchone()
            now = int(time.time())
            if not row or row["expires_at"] < now:
                return False, "Код терміналу прострочений"
            if row["code"] != code:
                return False, "Невірний код терміналу"
            conn.execute("UPDATE terminal_session SET verified=1 WHERE id=1")
            return True, "Термінал підтверджено"

    def is_terminal_verified(self) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT verified, expires_at FROM terminal_session WHERE id=1").fetchone()
            if not row:
                return False
            return bool(row["verified"]) and int(row["expires_at"]) >= int(time.time())

    def export_snapshot(self) -> None:
        with self._connect() as conn:
            rows = conn.execute("SELECT card_id, balance, pin_hash FROM cards ORDER BY card_id").fetchall()
        lines = ["# card_id = PIN(****) | balance"]
        for r in rows:
            masked = "*" * 4
            lines.append(f"{r['card_id']} = {masked} | {r['balance']}")
        SNAPSHOT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def log_event(self, card_id: str, event_type: str, amount: int | None, conn: sqlite3.Connection | None = None) -> None:
        target = conn if conn else self._connect()
        target.execute(
            "INSERT INTO events(card_id, event_type, amount, created_at) VALUES(?,?,?,?)",
            (card_id, event_type, amount, int(time.time())),
        )
        if conn is None:
            target.commit()
            target.close()
