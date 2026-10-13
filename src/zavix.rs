// ZAVIX modifications, 2026-10-12: compiled public configuration for the Windows client.
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
    builtin: HashMap<String, String>,
    hard: HashMap<String, String>,
}

fn branding() -> ResultType<Branding> {
    let brand: Branding = serde_json::from_str(include_str!("../branding/zavix.json"))?;
    if brand.app_name != "ZAVIXRemote"
        || brand.settings.get("api-server").map(String::as_str) != Some("https://remote.zavix.app")
        || brand.settings.get("allow-auto-update").map(String::as_str) != Some("N")
        || brand.settings.get("approve-mode").map(String::as_str) != Some("click")
        || brand.hard.get("conn-type").map(String::as_str) != Some("incoming")
    {
        bail!("Invalid ZAVIX embedded configuration");
    }
    Ok(brand)
}

pub fn initialize() -> ResultType<()> {
    let brand = branding()?;
    *config::APP_NAME.write().unwrap() = brand.app_name;
    config::OVERWRITE_SETTINGS.write().unwrap().extend(brand.settings);
    config::BUILTIN_SETTINGS.write().unwrap().extend(brand.builtin);
    config::HARD_SETTINGS.write().unwrap().extend(brand.hard);
    config::DEFAULT_LOCAL_SETTINGS.write().unwrap().insert("lang".into(), "pt-br".into());
    Ok(())
}

pub fn diagnostics_requested() -> bool {
    if !std::env::args().any(|arg| arg == "--zavix-diagnostics") {
        return false;
    }
    match branding() {
        Ok(brand) => println!("{}", serde_json::json!({
            "app_name": config::APP_NAME.read().unwrap().as_str(),
            "product_name": brand.product_name,
            "version": brand.version,
            "base_version": crate::VERSION,
            "installed": crate::platform::windows::is_installed(),
            "server": config::Config::get_rendezvous_server(),
            "relay": config::Config::get_option("relay-server"),
            "api": crate::common::get_api_server(config::Config::get_option("api-server"), config::Config::get_option("custom-rendezvous-server")),
            "approve_mode": config::Config::get_option("approve-mode"),
            "updater": config::Config::get_option("allow-auto-update"),
            "incoming_only": config::is_incoming_only(),
            "filename_configuration": crate::platform::windows::get_license_from_exe_name().is_ok(),
            "signed": false
        })),
        Err(err) => {
            eprintln!("ZAVIX configuration error: {}", err);
            std::process::exit(1);
        }
    }
    true
}
