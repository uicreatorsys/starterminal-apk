package com.starterminal

import android.content.Intent
import android.nfc.NfcAdapter

class NfcReader {
    fun readTag(intent: Intent): String? {
        val action = intent.action ?: return null
        if (action != NfcAdapter.ACTION_NDEF_DISCOVERED) return null

        val tag = intent.getParcelableExtra<android.nfc.Tag>(NfcAdapter.EXTRA_TAG)
        return tag?.id?.joinToString(separator = "") { eachByte ->
            "%02X".format(eachByte)
        }
    }
}
