package com.starterminal

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private val viewModel: TerminalViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val amountInput = findViewById<EditText>(R.id.amountInput)
        val statusText = findViewById<TextView>(R.id.statusText)

        findViewById<Button>(R.id.readNfcButton).setOnClickListener {
            statusText.text = viewModel.readNfcTag(intent)
        }

        findViewById<Button>(R.id.topUpButton).setOnClickListener {
            val amount = amountInput.text.toString().toLongOrNull() ?: 0L
            statusText.text = viewModel.topUp(amount)
        }

        findViewById<Button>(R.id.withdrawButton).setOnClickListener {
            val amount = amountInput.text.toString().toLongOrNull() ?: 0L
            statusText.text = viewModel.withdraw(amount)
        }
    }
}
