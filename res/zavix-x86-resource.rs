pub fn apply(resource: &mut winres::WindowsResource) -> Result<(), Box<dyn std::error::Error>> {
    println!("cargo:rerun-if-env-changed=ZAVIX_BUILD_VERSION");
    let Ok(version) = std::env::var("ZAVIX_BUILD_VERSION") else { return Ok(()); };
    let parts: Vec<u16> = version.split('.').map(str::parse).collect::<Result<_, _>>()?;
    if parts.len() != 4 { return Err("Expected four version fields".into()); }
    let number = parts.iter().fold(0u64, |value, part| (value << 16) | u64::from(*part));
    resource.set("CompanyName", "LINVIX SOFTWARES LTDA")
        .set("FileVersion", &version).set("ProductVersion", &version)
        .set_version_info(winres::VersionInfo::FILEVERSION, number)
        .set_version_info(winres::VersionInfo::PRODUCTVERSION, number);
    Ok(())
}
