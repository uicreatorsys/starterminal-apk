# Starterminal (Python Edition)

Проєкт повністю перероблено під **Python API сервер** для роботи з картками:

- зчитування NFC (вхідні дані з телефону/MacroDroid);
- поповнення картки з кодом підтвердження;
- зняття коштів по PIN;
- перевірка балансу;
- заготовка інтеграції з Telegram.

## Швидкий старт

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
./run-server.sh
```

Сервер стартує на `http://localhost:8000`.
Swagger UI: `http://localhost:8000/docs`

## Основні API методи

- `POST /card/register` — створити картку + PIN
- `POST /nfc/scan` — прийняти NFC-ідентифікатор
- `GET /card/{card_id}/balance` — баланс
- `POST /card/topup/request` — запросити поповнення (генерує код)
- `POST /card/topup/confirm` — підтвердити код поповнення
- `POST /card/withdraw` — зняти кошти по PIN

## Приклад під MacroDroid

Trigger: NFC Tag detected  
Action: HTTP Request (POST)

URL:

`http://<IP_ПК>:8000/nfc/scan`

Body:

```json
{
  "card_id": "04AABBCCDD",
  "source": "macro_nfc"
}
```

## Тести

```bash
pytest -q
```
