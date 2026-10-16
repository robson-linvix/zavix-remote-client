package com.carriez.flutter_hbb

import android.content.Context
import android.util.Log
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
        var connection: HttpsURLConnection? = null
        try {
            val config = JSONObject(ZavixEnrollment.configuration(context))
            val token = config.optString("token")
            val id = config.optString("rustdesk_id")
            if (!token.matches(Regex("[A-Za-z0-9_-]{40,200}")) ||
                !id.matches(Regex("[0-9]{6,12}"))) return
            val packet = JSONObject().put("rustdesk_id", id)
                .put("capture_ready", MainService.isReady)
                .put("control_ready", InputService.isOpen)
            for (key in listOf("serial", "model", "app_version", "android_version", "android_sdk",
                "sunmi_os_version", "os_build", "boot_enabled")) {
                if (config.has(key)) packet.put(key, config.get(key))
            }
            connection = URL("https://remote.zavix.app/api/android/heartbeat")
                .openConnection() as HttpsURLConnection
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 15000
            connection.readTimeout = 15000
            connection.requestMethod = "POST"
            connection.doOutput = true
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(packet.toString().toByteArray(Charsets.UTF_8)) }
            if (connection.responseCode != 200) throw IllegalStateException("Heartbeat rejected")
            connection.inputStream.close()
        } catch (error: Exception) {
            Log.w("ZavixPresence", "Presence unavailable: ${error.javaClass.simpleName}")
        } finally {
            connection?.disconnect()
        }
    }
}
