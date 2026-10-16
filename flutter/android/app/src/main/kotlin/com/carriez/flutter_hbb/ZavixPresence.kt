package com.carriez.flutter_hbb

import android.content.Context
import android.util.Log
import ffi.FFI
import org.json.JSONObject
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import javax.net.ssl.HttpsURLConnection

/** Presence belongs to the Android process, including boot without a Flutter activity. */
object ZavixPresence {
    private var started = false

    @Synchronized
    fun start(context: Context) {
        if (!BuildConfig.ZAVIX_MANAGED || started) return
        started = true
        val app = context.applicationContext
        Executors.newSingleThreadScheduledExecutor { task ->
            Thread(task, "ZavixPresence").apply { isDaemon = true }
        }.scheduleWithFixedDelay({ heartbeat(app) }, 0, 60, TimeUnit.SECONDS)
    }

    private fun heartbeat(context: Context) {
        try {
            val config = JSONObject(ZavixEnrollment.configuration(context))
            var token = config.optString("token")
            val ticket = config.optString("ticket")
            val id = config.optString("rustdesk_id")
            if (!id.matches(Regex("[0-9]{6,12}")) ||
                (token.isEmpty() && ticket.isEmpty())) return
            val packet = JSONObject().put("rustdesk_id", id)
                .put("capture_ready", MainService.isReady)
                .put("control_ready", InputService.isOpen)
            for (key in listOf("serial", "model", "app_version", "android_version", "android_sdk",
                "sunmi_os_version", "os_build", "boot_enabled")) {
                if (config.has(key)) packet.put(key, config.get(key))
            }
            if (token.isEmpty()) {
                val enrolled = request("enrollment/claim", ticket, packet)
                if (!enrolled.isNull("password")) {
                    check(FFI.mdmPassword(enrolled.getString("password")))
                }
                check(FFI.mdmPassword(""))
                token = enrolled.getString("token")
                check(token.matches(Regex("[A-Za-z0-9_-]{40,200}")))
                ZavixEnrollment.acknowledge(context, token)
            }
            check(FFI.mdmPassword(""))
            request("enrollment/activate", token, JSONObject(packet.toString()).put("password_saved", true))
            request("heartbeat", token, packet)
        } catch (error: Exception) {
            Log.w("ZavixPresence", "Presence unavailable: ${error.javaClass.simpleName}")
        }
    }

    private fun request(endpoint: String, token: String, packet: JSONObject): JSONObject {
        check(token.matches(Regex("[A-Za-z0-9_-]{40,200}")))
        val connection = URL("https://remote.zavix.app/api/android/$endpoint")
                .openConnection() as HttpsURLConnection
        try {
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 15000
            connection.readTimeout = 15000
            connection.requestMethod = "POST"
            connection.doOutput = true
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(packet.toString().toByteArray(Charsets.UTF_8)) }
            check(connection.responseCode == 200)
            val bytes = ByteArray(4097)
            var size = 0
            connection.inputStream.use { input ->
                while (size < bytes.size) {
                    val read = input.read(bytes, size, bytes.size - size)
                    if (read < 0) break
                    size += read
                }
            }
            check(size <= 4096)
            return JSONObject(String(bytes, 0, size, Charsets.UTF_8))
        } finally {
            connection.disconnect()
        }
    }
}
