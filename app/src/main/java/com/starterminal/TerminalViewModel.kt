package com.starterminal

import android.content.Intent
import androidx.lifecycle.ViewModel

class TerminalViewModel : ViewModel() {

    private val nfcReader = NfcReader()
    private val cardService = CardService()

    fun readNfcTag(intent: Intent): String {
        val tagId = nfcReader.readTag(intent)
        return if (tagId == null) {
            "NFC мітка не знайдена"
        } else {
            "Зчитано NFC мітку: $tagId"
        }
    }

    fun topUp(amount: Long): String {
        if (amount <= 0) return "Введіть коректну суму"
        val newBalance = cardService.topUp(amount)
        return "Поповнення успішне. Баланс: $newBalance"
    }

    fun withdraw(amount: Long): String {
        if (amount <= 0) return "Введіть коректну суму"
        return if (cardService.withdraw(amount)) {
            "Зняття успішне. Баланс: ${cardService.balance()}"
        } else {
            "Недостатньо коштів. Баланс: ${cardService.balance()}"
        }
    }
}
