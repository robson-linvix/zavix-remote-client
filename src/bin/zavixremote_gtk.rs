#[cfg(target_os = "linux")]
fn main() {
    if let Err(error) = librustdesk::zavix_linux_gtk::run() {
        eprintln!("ZAVIX Remote: {error}");
        std::process::exit(1);
    }
}

#[cfg(not(target_os = "linux"))]
fn main() {
    eprintln!("This client requires Linux.");
    std::process::exit(1);
}
