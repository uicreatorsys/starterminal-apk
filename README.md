# Starterminal (Python Edition)

Симулятор терміналу з віконцем у браузері (для гри, не для реальних банківських карт):

- створення вигаданих карток вручну (номер + пароль/PIN);
- перевірка картки (manual scan);
- поповнення/зняття коштів;
- баланс;
- дані карток зберігаються на ПК у файлах: `starterminal.db` + `cards_snapshot.txt`.

## Швидкий старт

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
./run-server.sh
```

Відкрити UI: `http://localhost:8000/`

## Новий флоу "старт-код терміналу"

1. Натискаєш **Старт**.
2. Додаток показує 6-значний код.
3. Вводиш цей же код у поле і тиснеш **Підтвердити код**.
4. Після цього дозволені `поповнення` та `зняття`.

## Приклад під MacroDroid / Automate (опційно)

Trigger: NFC Tag detected  
Action: HTTP Request (POST)

URL:

`http://<IP_ПК>:8000/nfc/scan`

Body:

```json
{
  "card_id": "5564 6566 8879 0986",
  "source": "macro_nfc"
}
```

## Telegram (опційно)

Сервер підтримує Telegram Bot API, якщо задати змінну середовища:

```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
```

> Якщо токен вже десь публічно світився — обов'язково відклич його в @BotFather і створи новий.

## Тести

```bash
pytest -q
```
