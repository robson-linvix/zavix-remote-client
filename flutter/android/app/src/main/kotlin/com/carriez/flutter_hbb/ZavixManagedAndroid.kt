package com.carriez.flutter_hbb

import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

object ZavixManagedAndroid {
    private val allowed = setOf("app_started", "app_crashed", "projection_requested", "projection_granted",
        "projection_denied", "projection_stopped", "capture_unavailable", "capture_failed", "capture_started",
        "capture_stopped", "client_authorized", "client_requested", "boot_enabled", "boot_received",
        "boot_requires_open", "boot_failed", "diagnostics_sent", "diagnostics_failed", "input_enabled", "input_disabled")

    private var crashInstalled = false

    private fun file(context: Context) = File(context.noBackupFilesDir, "zavix-diagnostics.json")

    @Synchronized
    fun record(context: Context, event: String, error: Throwable? = null) {
        if (!BuildConfig.ZAVIX_MANAGED || event !in allowed) return
        try {
            val path = file(context)
            val old = if (path.exists() && path.length() <= 32768) JSONArray(path.readText()) else JSONArray()
            val events = JSONArray()
            for (i in maxOf(0, old.length() - 199) until old.length()) events.put(old.getJSONObject(i))
            val entry = JSONObject().put("time", System.currentTimeMillis()).put("event", event)
            error?.let { entry.put("error", it.javaClass.simpleName.take(64)) }
            events.put(entry)
            path.writeText(events.toString())
        } catch (error: Exception) {
            Log.w("ZavixDiagnostics", "Diagnostic storage unavailable: ${error.javaClass.simpleName}")
        }
    }

    fun install(context: Context) {
        record(context, "app_started")
        val appContext = context.applicationContext
        if (crashInstalled) return
        val previous = Thread.getDefaultUncaughtExceptionHandler() ?: return
        crashInstalled = true
        Thread.setDefaultUncaughtExceptionHandler { thread, error ->
            record(appContext, "app_crashed", error)
            previous.uncaughtException(thread, error)
        }
    }

    @Synchronized
    fun snapshot(context: Context): String {
        val path = file(context)
        val events = try {
            if (path.exists() && path.length() <= 32768) JSONArray(path.readText()) else JSONArray()
        } catch (error: Exception) { JSONArray() }
        return JSONObject().put("schema", 1).put("app_version", BuildConfig.VERSION_NAME)
            .put("serial", ZavixEnrollment.serial(context))
            .put("package", context.packageName).put("model", Build.MODEL).put("manufacturer", Build.MANUFACTURER)
            .put("android", Build.VERSION.RELEASE).put("sdk", Build.VERSION.SDK_INT)
            .put("abis", JSONArray(Build.SUPPORTED_ABIS.toList())).put("service_ready", MainService.isReady)
            .put("capturing", MainService.isStart).put("input_enabled", InputService.isOpen)
            .put("boot_enabled", context.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE)
                .getBoolean(KEY_START_ON_BOOT_OPT, false)).put("events", events).toString()
    }

    fun enableBoot(context: Context): Boolean {
        if (!MainService.isReady || !InputService.isOpen) return false
        context.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_START_ON_BOOT_OPT, true).apply()
        record(context, "boot_enabled")
        return true
    }

    fun restartFromBoot(context: Context) {
        record(context, "boot_received")
        val prefs = context.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(KEY_START_ON_BOOT_OPT, false)) return
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.P) {
            record(context, "boot_requires_open")
            return
        }
        try {
            context.startActivity(Intent(context, PermissionRequestTransparentActivity::class.java).apply {
                action = ACT_REQUEST_MEDIA_PROJECTION
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                putExtra(EXT_INIT_FROM_BOOT, true)
            })
        } catch (error: Exception) { record(context, "boot_failed", error) }
    }
}
