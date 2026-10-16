# Only run on a disposable Windows CI runner. The published candidate stays unsigned.
param([string]$Output = './MSIXOutput', [Parameter(Mandatory=$true)][string]$SignTool)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'Installation test requires a disposable GitHub Actions runner' }
$manifest = Get-Content (Join-Path $Output 'manifest.json') | ConvertFrom-Json
[xml]$xml = Get-Content (Join-Path $Output 'AppxManifest.xml')
$capabilities = @($xml.Package.Capabilities.ChildNodes | ForEach-Object { $_.Name })
if (($capabilities | Sort-Object) -join ',' -ne 'internetClient,runFullTrust') { throw 'Unexpected MSIX capabilities' }
if ($xml.OuterXml -match 'allowElevation|packagedServices|localSystemServices|windows.service|startupTask') { throw 'Store package requests forbidden assisted-edition capabilities' }
$source = Get-ChildItem $Output -Filter '*.msix' | Select-Object -First 1
$originalHash = (Get-FileHash $source.FullName -Algorithm SHA256).Hash
$temporary = Join-Path $env:RUNNER_TEMP ('msix-test-' + [guid]::NewGuid())
New-Item -ItemType Directory $temporary | Out-Null
$copy = Join-Path $temporary $source.Name
Copy-Item $source.FullName $copy
$certificate = $null
$trusted = $null
$package = $null
try {
    $certificate = New-SelfSignedCertificate -Type CodeSigningCert -Subject $manifest.identity.publisher -CertStoreLocation 'Cert:\CurrentUser\My' -HashAlgorithm SHA256
    $public = Join-Path $temporary 'ci-only.cer'
    Export-Certificate -Cert $certificate -FilePath $public | Out-Null
    $trusted = Import-Certificate -FilePath $public -CertStoreLocation 'Cert:\LocalMachine\TrustedPeople'
    & $SignTool sign /fd SHA256 /sha1 $certificate.Thumbprint $copy
    if ($LASTEXITCODE -ne 0) { throw 'CI-only package signing failed' }
    Add-AppxPackage -Path $copy
    $package = Get-AppxPackage -Name $manifest.identity.name
    if (-not $package -or $package.Version.ToString() -ne $manifest.package_version) { throw 'MSIX installation identity mismatch' }
    $aumid = $package.PackageFamilyName + '!Remote'
    Start-Process explorer.exe -ArgumentList "shell:AppsFolder\$aumid"
    $process = $null
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        $process = Get-Process -Name $manifest.app_name -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
        if ($process) { break }
    }
    if (-not $process -or -not $process.Path.StartsWith($package.InstallLocation)) { throw 'Installed Store application did not open from its package' }
    Add-Type -AssemblyName System.Drawing
    Add-Type -AssemblyName System.Windows.Forms
    $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bitmap = [System.Drawing.Bitmap]::new($screen.Width, $screen.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
    $bitmap.Save((Join-Path (Resolve-Path $Output) 'installed-window.png'))
    $graphics.Dispose(); $bitmap.Dispose()
    if (-not $process.CloseMainWindow()) { throw 'Installed application could not be closed' }
    if (-not $process.WaitForExit(20000)) { $process.Kill(); throw 'Closing Store application left remote access running' }
    if (Get-Service -Name $manifest.app_name -ErrorAction SilentlyContinue) { throw 'Store application created a service' }
    Remove-AppxPackage -Package $package.PackageFullName
    $package = $null
    if (Get-AppxPackage -Name $manifest.identity.name) { throw 'MSIX uninstall failed' }
    @{ schema='validated by MakeAppx'; installation='passed'; activation='passed'; close_exits='passed'; service='absent'; uninstall='passed'; signing='temporary CI certificate only'; store_certification='pending'; real_remote_session='pending' } | ConvertTo-Json | Set-Content (Join-Path $Output 'validation.json')
} finally {
    Get-Process -Name $manifest.app_name -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    if ($package) { Remove-AppxPackage -Package $package.PackageFullName -ErrorAction Continue }
    if ($trusted) { Remove-Item ('Cert:\LocalMachine\TrustedPeople\' + $trusted.Thumbprint) -ErrorAction Continue }
    if ($certificate) { Remove-Item ('Cert:\CurrentUser\My\' + $certificate.Thumbprint) -ErrorAction Continue }
    Remove-Item $temporary -Recurse -Force
    if ((Get-FileHash $source.FullName -Algorithm SHA256).Hash -ne $originalHash) { throw 'Unsigned submission candidate was modified by installation test' }
}
