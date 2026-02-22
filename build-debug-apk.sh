#!/usr/bin/env bash
set -euo pipefail

# Простий скрипт для збірки тестового APK
# Запуск: ./build-debug-apk.sh

JAVA_17="/root/.local/share/mise/installs/java/17.0.2"

if [ -d "$JAVA_17" ]; then
  export JAVA_HOME="$JAVA_17"
  export PATH="$JAVA_HOME/bin:$PATH"
fi

echo "▶ Запускаю збірку тестового APK..."

gradle assembleDebug

echo "✅ Готово! APK тут: app/build/outputs/apk/debug/app-debug.apk"
