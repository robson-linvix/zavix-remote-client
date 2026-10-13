package com.carriez.flutter_hbb

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Settings

/** Explicit administrative enrollment; the manifest requires the shell/system DUMP permission. */
class ZavixProvisionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (!BuildConfig.ZAVIX_MANAGED || intent.action != "app.zavix.remote.MDM_PREPARE") return
        val serial = intent.getStringExtra("serial")
        val ticket = intent.getStringExtra("enrollment_ticket")
        if (serial != null && ticket != null) ZavixEnrollment.prepare(context, serial, ticket)
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.P) {
            resultCode = 2
            resultData = "unsupported_android"
            return
        }
        val component = "${context.packageName}/com.carriez.flutter_hbb.InputService"
        val services = Settings.Secure.getString(context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES).orEmpty().split(':')
        // Android 7 has no PROJECT_MEDIA string app-op. MediaProjection itself enforces capture consent.
        if (component !in services) {
            resultCode = 3
            resultData = "permissions_pending"
            return
        }
        context.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_START_ON_BOOT_OPT, true).apply()
        ZavixManagedAndroid.restartFromBoot(context)
        resultCode = 0
        resultData = "capture_requested"
    }
}
