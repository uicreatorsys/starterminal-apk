package com.starterminal

class CardService {
    private var currentBalance: Long = 0L

    fun topUp(amount: Long): Long {
        currentBalance += amount
        return currentBalance
    }

    fun withdraw(amount: Long): Boolean {
        if (currentBalance < amount) return false
        currentBalance -= amount
        return true
    }

    fun balance(): Long = currentBalance
}
