//! Store-only assisted profile; EXE/MSI builds leave this feature disabled.
use hbb_common::config;

pub fn handle_entrypoint() -> bool {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.iter().any(|arg| arg == "--msix-diagnostics") {
        println!("{}", serde_json::json!({
            "profile": "store-assisted",
            "app_name": crate::get_app_name(),
            "installation_disabled": config::is_disable_installation(),
            "can_elevate": crate::ui_cm_interface::can_elevate(),
            "approve_mode": config::Config::get_option("approve-mode"),
            "verification_method": config::Config::get_option("verification-method"),
            "incoming_only": config::is_incoming_only(),
            "server": config::Config::get_rendezvous_server(),
            "relay": config::Config::get_option("relay-server"),
            "updater": config::Config::get_option("allow-auto-update"),
            "close_exits": config::BUILTIN_SETTINGS.read().map(|settings| settings.get("store-assisted").map(String::as_str) == Some("Y")).unwrap_or(false),
        }));
        return true;
    }
    if args.iter().any(|arg| [
        "--install", "--uninstall", "--update", "--service", "--server", "--tray",
        "--elevate", "--run-as-system", "--quick_support", "--portable-service",
        "--password", "--import-config", "--option",
    ].iter().any(|prefix| arg.starts_with(prefix))) {
        eprintln!("This Store edition supports assisted access only while the application is open.");
        std::process::exit(64);
    }
    false
}
