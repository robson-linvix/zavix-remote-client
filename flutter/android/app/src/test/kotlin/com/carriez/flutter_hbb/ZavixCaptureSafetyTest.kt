package com.carriez.flutter_hbb

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.content.Intent
import android.os.Looper
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowAlertDialog
import java.time.Duration

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [25, 28], application = Application::class)
class ZavixCaptureSafetyTest {
    @Test
    fun rebootWithExistingAutostartNeverOpensCaptureWindow() {
        val app = RuntimeEnvironment.getApplication()
        app.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_START_ON_BOOT_OPT, true).commit()
        BootReceiver().onReceive(app, Intent(Intent.ACTION_BOOT_COMPLETED))
        assertNull(shadowOf(app).nextStartedActivity)
    }

    @Test
    fun lockedKioskRejectsCaptureAndClosesWrapper() {
        val app = RuntimeEnvironment.getApplication()
        val manager = app.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        shadowOf(manager).setLockTaskModeState(ActivityManager.LOCK_TASK_MODE_LOCKED)
        val activity = Robolectric.buildActivity(PermissionRequestTransparentActivity::class.java,
            Intent(app, PermissionRequestTransparentActivity::class.java)
                .setAction(ACT_REQUEST_MEDIA_PROJECTION)).create().get()
        assertTrue(activity.isFinishing)
        assertNull(shadowOf(activity).nextStartedActivity)
    }

    @Test
    fun missingPermissionResultCannotLeaveWrapperOpen() {
        val activity = Robolectric.buildActivity(PermissionRequestTransparentActivity::class.java,
            Intent().setAction(ACT_REQUEST_MEDIA_PROJECTION)).setup().get()
        ShadowAlertDialog.getLatestAlertDialog().getButton(-1).performClick()
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(16))
        assertTrue(activity.isFinishing)
        assertEquals(RES_FAILED, shadowOf(activity).resultCode)
    }
}
