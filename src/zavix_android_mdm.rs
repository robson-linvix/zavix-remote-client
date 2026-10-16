use hbb_common::config;
use jni::{objects::{JClass, JString}, sys::{jboolean, jstring}, JNIEnv};

#[no_mangle]
pub extern "system" fn Java_ffi_FFI_mdmIdentity(
    mut env: JNIEnv,
    _class: JClass,
    app_dir: JString,
    home_dir: JString,
) -> jstring {
    let identity = (|| -> Result<String, ()> {
        let app_dir: String = env.get_string(&app_dir).map_err(|_| ())?.into();
        let home_dir: String = env.get_string(&home_dir).map_err(|_| ())?.into();
        if !std::path::Path::new(&app_dir).is_absolute()
            || !std::path::Path::new(&home_dir).is_absolute()
        {
            return Err(());
        }
        // Configure storage before the first lazy Config read on a UI-free launch.
        *config::APP_DIR.write().map_err(|_| ())? = app_dir;
        *config::APP_HOME_DIR.write().map_err(|_| ())? = home_dir;
        crate::zavix_android::initialize().map_err(|_| ())?;
        Ok(config::Config::get_id())
    })();
    let id = match identity {
        Ok(id) => id,
        Err(()) => {
            log::error!("Managed Android identity initialization failed");
            String::new()
        }
    };
    env.new_string(id).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
}

#[no_mangle]
pub extern "system" fn Java_ffi_FFI_mdmPassword(
    mut env: JNIEnv,
    _class: JClass,
    password: JString,
) -> jboolean {
    let Ok(password) = env.get_string(&password) else { return 0 };
    let password: String = password.into();
    let saved = if password.is_empty() {
        config::Config::has_permanent_password()
    } else if (12..=128).contains(&password.len()) {
        crate::ui_interface::set_permanent_password_with_result(password)
    } else {
        false
    };
    saved.into()
}
