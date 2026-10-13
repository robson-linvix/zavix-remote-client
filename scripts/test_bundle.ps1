param([Parameter(Mandatory=$true)][string]$Installer)
$ErrorActionPreference = 'Stop'
$Installer = (Resolve-Path $Installer).Path
$brand = Get-Content branding/zavix.json | ConvertFrom-Json
$exe = Join-Path $env:ProgramFiles 'ZAVIXRemote/ZAVIXRemote.exe'
$state = 'HKLM:\SOFTWARE\ZAVIXRemote\InstallState\ZAVIXRemote'
$state32 = 'HKLM:\SOFTWARE\WOW6432Node\ZAVIXRemote\InstallState\ZAVIXRemote'
if ((Test-Path $state) -or (Test-Path $state32)) { throw 'Runner already contains ZAVIX; do not overwrite it' }
function Run-Bundle([string]$action) {
    $label = $action.TrimStart('/')
    $p = Start-Process $Installer -ArgumentList @($action,'/quiet','/norestart','/log',"bundle-$label.log") -Wait -PassThru
    if ($p.ExitCode -notin @(0,3010)) { throw "Bundle $action failed: $($p.ExitCode)" }
}
try {
    # Start with the actual current x86 package to exercise same-version architecture migration.
    $x86 = (Resolve-Path "UniversalOutput/ZAVIXRemote-$($brand.version)-x86.msi").Path
    $old = Start-Process msiexec.exe -ArgumentList @('/i',"`"$x86`"",'/qn','/norestart','/l*v','bundle-x86-before.log') -PassThru -Wait
    if ($old.ExitCode -notin @(0,3010) -or -not (Test-Path $state32)) { throw 'x86 starting installation failed' }
    Run-Bundle '/install'
    if (-not (Test-Path $exe) -or -not (Test-Path $state) -or (Test-Path $state32)) { throw 'Bundle did not choose x64 and replace x86 on this x64 Windows' }
    $p = Start-Process $exe -ArgumentList '--zavix-diagnostics' -Wait -PassThru -RedirectStandardOutput bundle-runtime.json
    if ($p.ExitCode -ne 0) { throw 'Final bundled application diagnostics failed' }
    $runtime = Get-Content bundle-runtime.json | ConvertFrom-Json
    if ($runtime.architecture -ne 'x64' -or $runtime.client_ui -ne 'flutter' -or $runtime.version -ne $brand.version -or -not $runtime.installed -or $runtime.approve_mode -ne 'click' -or $runtime.server -ne '187.77.241.190:21116') { throw 'Final bundled runtime differs' }
    $service = Get-CimInstance Win32_Service -Filter "Name='ZAVIXRemote'"
    if ($service.StartMode -ne 'Auto' -or $service.State -ne 'Running' -or $service.StartName -ne 'LocalSystem' -or $service.PathName -notlike "*$exe*--service*") { throw 'Bundled service differs' }
    Restart-Service 'ZAVIXRemote'
    (Get-Service 'ZAVIXRemote').WaitForStatus('Running',[TimeSpan]::FromSeconds(30))
    Start-Sleep -Seconds 10
    if ((Get-Service 'ZAVIXRemote').Status -ne 'Running') { throw 'Service did not remain running after restart' }
    Remove-Item (Join-Path (Split-Path $exe) 'PRIVACY.md')
    Run-Bundle '/repair'
    if (-not (Test-Path (Join-Path (Split-Path $exe) 'PRIVACY.md'))) { throw 'Bundle repair did not restore payload' }
    Run-Bundle '/uninstall'
    if ((Test-Path $exe) -or (Test-Path $state) -or (Get-Service ZAVIXRemote -ErrorAction SilentlyContinue)) { throw 'Bundle uninstall left executable, state or service' }
    # Exercise upgrade from the exact MSI currently distributed, not only a version-number fixture.
    $releaseApi = if ($brand.app_name -eq 'LinvixRemote') { '/api/linvix-client-release' } else { '/api/client-release' }
    $previous = Invoke-RestMethod ('https://remote.zavix.app' + $releaseApi)
    if (-not $previous.ready -or $previous.product -ne $brand.product_name -or $previous.version -eq $brand.version) { throw 'Previous public MSI is not a valid upgrade baseline' }
    $priorMsi = $previous.downloads.msi64
    Invoke-WebRequest ('https://remote.zavix.app' + $priorMsi.url) -OutFile previous-public.msi
    if ((Get-FileHash previous-public.msi -Algorithm SHA256).Hash.ToLower() -ne $priorMsi.sha256) { throw 'Previous public MSI hash differs' }
    $old = Start-Process msiexec.exe -ArgumentList @('/i', '"previous-public.msi"', '/qn', '/norestart', '/l*v', 'bundle-previous-public.log') -PassThru -Wait
    if ($old.ExitCode -notin @(0,3010)) { throw 'Previous public MSI installation failed' }
    Run-Bundle '/install'
    $p = Start-Process $exe -ArgumentList '--zavix-diagnostics' -Wait -PassThru -RedirectStandardOutput bundle-upgrade-runtime.json
    $upgraded = Get-Content bundle-upgrade-runtime.json | ConvertFrom-Json
    if ($p.ExitCode -ne 0 -or $upgraded.version -ne $brand.version -or -not $upgraded.installed) { throw 'Upgrade retained an old native executable or DLL' }
    Run-Bundle '/uninstall'
    $signature = (Get-AuthenticodeSignature $Installer).Status.ToString()
    if ($signature -ne 'NotSigned') { throw 'Unexpected final installer signature' }
    @{result='passed';previous_public_version=$previous.version;signature=$signature;sha256=(Get-FileHash $Installer -Algorithm SHA256).Hash.ToLower();runtime=$runtime;
      cases=@('x86 MSI installation under WOW64','automatic x64 selection and replacement of x86 MSI','service startup','repair','uninstall','upgrade from actual published MSI');
      old_windows='not tested on Windows 7/8';x86_os='not tested on actual 32-bit OS'} | ConvertTo-Json -Depth 6 | Set-Content UniversalOutput/bundle-runtime-evidence.json
} finally {
    foreach ($key in @($state,$state32)) {
        if (Test-Path $key) {
            $code = (Get-ItemProperty $key).MsiProductCode
            Start-Process msiexec.exe -ArgumentList @('/x',$code,'/qn','/norestart') -Wait
        }
    }
}
Write-Host 'Final universal EXE: x64 selection, cross-architecture MSI migration, service, repair and uninstall passed'
