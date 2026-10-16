package com.carriez.flutter_hbb

import android.content.Context
import ffi.FFI
import org.json.JSONObject

object ZavixMdm {
    fun initialize(context: Context) {
        if (!BuildConfig.ZAVIX_MANAGED) return
        ZavixManagedAndroid.install(context)
        try {
            val prefs = context.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE)
            val path = prefs.getString(KEY_APP_DIR_CONFIG_PATH, null)
                ?: context.getDir("flutter", Context.MODE_PRIVATE).absolutePath
            val home = context.getExternalFilesDir(null)?.absolutePath ?: context.filesDir.absolutePath
            val id = FFI.mdmIdentity(path, home).orEmpty()
            check(id.matches(Regex("[0-9]{6,12}")))
            prefs.edit().putString(KEY_APP_DIR_CONFIG_PATH, path).apply()
            ZavixEnrollment.rememberId(context, id)
        } catch (error: Exception) {
            ZavixManagedAndroid.record(context, "boot_failed", error)
        }
    }

    fun status(context: Context): String {
        val cfg = JSONObject(ZavixEnrollment.configuration(context))
        return JSONObject().put("serial", cfg.optString("serial"))
            .put("rustdesk_id", cfg.optString("rustdesk_id"))
            .put("app_version", BuildConfig.VERSION_NAME)
            .put("agent_configured", cfg.optString("token").isNotEmpty())
            .put("ticket_pending", cfg.optString("ticket").isNotEmpty())
            .put("password_saved", FFI.mdmPassword(""))
            .put("capture_ready", MainService.isReady).put("control_ready", InputService.isOpen)
            .toString()
    }
}
