use hbb_common::{bail, config, ResultType};
use serde_derive::Deserialize;
use std::collections::HashMap;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Branding {
    app_name: String,
    product_name: String,
    version: String,
    settings: HashMap<String, String>,
    local: HashMap<String, String>,
    builtin: HashMap<String, String>,
    hard: HashMap<String, String>,
}

pub fn initialize() -> ResultType<()> {
    let mut brand: Branding = serde_json::from_str(include_str!("../branding/zavix-android.json"))?;
    if brand.app_name != "ZAVIXRemote"
        || brand.product_name != "ZAVIX Remote"
        || brand.version.is_empty()
        || brand.settings.get("approve-mode").map(String::as_str) != Some("password")
        || brand.settings.get("allow-auto-update").map(String::as_str) != Some("N")
        || brand.hard.get("conn-type").map(String::as_str) != Some("incoming")
    {
        bail!("Invalid ZAVIX Android managed configuration");
    }
    *config::APP_NAME.write().unwrap() = brand.app_name;
    for key in ["approve-mode", "verification-method"] {
        if let Some(value) = brand.settings.remove(key) {
            config::DEFAULT_SETTINGS.write().unwrap().insert(key.into(), value);
        }
    }
    config::OVERWRITE_SETTINGS.write().unwrap().extend(brand.settings);
    config::OVERWRITE_LOCAL_SETTINGS.write().unwrap().extend(brand.local);
    config::BUILTIN_SETTINGS.write().unwrap().extend(brand.builtin);
    config::HARD_SETTINGS.write().unwrap().extend(brand.hard);
    Ok(())
}
