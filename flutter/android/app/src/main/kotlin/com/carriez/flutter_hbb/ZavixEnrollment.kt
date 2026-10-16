package com.carriez.flutter_hbb

import android.annotation.SuppressLint
import android.content.Context
import android.os.Build
import org.json.JSONObject
import java.io.File

object ZavixEnrollment {
    private fun file(context: Context) = File(context.noBackupFilesDir, "zavix-enrollment.json")
    private fun saved(context: Context): JSONObject {
        val path = file(context)
        return if (path.exists() && path.length() <= 4096) JSONObject(path.readText()) else JSONObject()
    }

    @SuppressLint("HardwareIds")
    fun serial(context: Context): String {
        val native = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) Build.getSerial() else Build.SERIAL
        } catch (_: SecurityException) { "" }
        return if (native.isNotBlank() && native != Build.UNKNOWN) native else saved(context).optString("serial")
    }

    fun prepare(context: Context, serial: String, ticket: String) {
        if (!serial.matches(Regex("[A-Za-z0-9._-]{4,64}")) ||
            !ticket.matches(Regex("[A-Za-z0-9_-]{40,200}"))) return
        val existing = ZavixEnrollment.serial(context)
        if (existing.isNotBlank() && existing != serial) return
        file(context).writeText(JSONObject().put("serial", serial).put("ticket", ticket).toString())
    }

    fun configuration(context: Context): String = saved(context).apply {
        put("serial", serial(context)); put("model", Build.MODEL)
        put("app_version", BuildConfig.VERSION_NAME)
        put("android_version", Build.VERSION.RELEASE); put("android_sdk", Build.VERSION.SDK_INT)
        put("sunmi_os_version", sunmiOsVersion()); put("os_build", Build.VERSION.INCREMENTAL)
        put("boot_enabled", context.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE)
            .getBoolean(KEY_START_ON_BOOT_OPT, true))
    }.toString()

    private fun sunmiOsVersion(): String = try {
        Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            .invoke(null, "ro.version.sunmi_versionname").toString().take(100)
    } catch (_: Exception) { "" }

    fun acknowledge(context: Context, token: String) {
        if (!token.matches(Regex("[A-Za-z0-9_-]{40,200}"))) return
        val value = saved(context)
        value.remove("ticket"); value.put("token", token)
        file(context).writeText(value.toString())
    }
}
