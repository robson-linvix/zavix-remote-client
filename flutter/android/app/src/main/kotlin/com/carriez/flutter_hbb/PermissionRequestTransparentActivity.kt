package com.carriez.flutter_hbb

import android.app.Activity
import android.app.ActivityManager
import android.content.Intent
import android.media.projection.MediaProjectionConfig
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.ResultReceiver
import android.util.Log

class PermissionRequestTransparentActivity: Activity() {
    private val logTag = "permissionRequest"
    private val deadline = Handler(Looper.getMainLooper())
    private val timeout = Runnable { failCapture("projection_timeout") }

    private fun failCapture(event: String, error: Exception? = null) {
        if (isFinishing || isDestroyed) return
        deadline.removeCallbacks(timeout)
        ZavixManagedAndroid.record(this, event, error)
        try {
            val receiver = intent.getParcelableExtra<ResultReceiver>(EXT_MEDIA_PROJECTION_RESULT_RECEIVER)
            if (receiver != null) receiver.send(RES_FAILED, null) else setResult(RES_FAILED)
            // Close a child consent window too, if it never delivered its result.
            finishActivity(REQ_REQUEST_MEDIA_PROJECTION)
        } finally {
            finish()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (BuildConfig.ZAVIX_MANAGED) {
            val manager = getSystemService(ACTIVITY_SERVICE) as? ActivityManager
            if (intent.getBooleanExtra(EXT_INIT_FROM_BOOT, false) || manager == null ||
                manager.lockTaskModeState != ActivityManager.LOCK_TASK_MODE_NONE) {
                failCapture("capture_deferred")
                return
            }
            deadline.postDelayed(timeout, 15000)
        }
        ZavixManagedAndroid.record(this, "projection_requested")
        Log.d(logTag, "onCreate PermissionRequestTransparentActivity: intent.action: ${intent.action}")

        when (intent.action) {
            ACT_REQUEST_MEDIA_PROJECTION -> {
                ZavixConsent.screen(this, {
                val mediaProjectionManager =
                    getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
                val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                    mediaProjectionManager.createScreenCaptureIntent(
                        MediaProjectionConfig.createConfigForDefaultDisplay()
                    )
                } else {
                    mediaProjectionManager.createScreenCaptureIntent()
                }
                try {
                    startActivityForResult(intent, REQ_REQUEST_MEDIA_PROJECTION)
                } catch (error: Exception) {
                    if (!BuildConfig.ZAVIX_MANAGED) throw error
                    failCapture("capture_failed", error)
                }
                }, {
                    val receiver = intent.getParcelableExtra<ResultReceiver>(EXT_MEDIA_PROJECTION_RESULT_RECEIVER)
                    if (receiver != null) receiver.send(RES_FAILED, null) else setResult(RES_FAILED)
                    finish()
                })
            }
            else -> finish()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (BuildConfig.ZAVIX_MANAGED && (isFinishing || isDestroyed)) return
        deadline.removeCallbacks(timeout)
        if (requestCode == REQ_REQUEST_MEDIA_PROJECTION) {
            if (resultCode == RESULT_OK && data != null) {
                ZavixManagedAndroid.record(this, "projection_granted")
                try {
                    launchService(data)
                } catch (error: Exception) {
                    if (!BuildConfig.ZAVIX_MANAGED) throw error
                    failCapture("capture_failed", error)
                }
            } else {
                ZavixManagedAndroid.record(this, "projection_denied")
                val resultReceiver =
                    intent.getParcelableExtra<ResultReceiver>(EXT_MEDIA_PROJECTION_RESULT_RECEIVER)
                if (resultReceiver != null) {
                    resultReceiver.send(RES_FAILED, null)
                } else {
                    setResult(RES_FAILED)
                }
            }
        }

        finish()
    }

    override fun onDestroy() {
        deadline.removeCallbacks(timeout)
        super.onDestroy()
    }

    private fun launchService(mediaProjectionResultIntent: Intent) {
        Log.d(logTag, "Launch MainService")
        val serviceIntent = Intent(this, MainService::class.java)
        serviceIntent.action = ACT_INIT_MEDIA_PROJECTION_AND_SERVICE
        serviceIntent.putExtra(EXT_MEDIA_PROJECTION_RES_INTENT, mediaProjectionResultIntent)
        serviceIntent.putExtra(EXT_INIT_FROM_BOOT, intent.getBooleanExtra(EXT_INIT_FROM_BOOT, false))

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

}
