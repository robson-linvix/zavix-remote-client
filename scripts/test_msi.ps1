param([Parameter(Mandatory=$true)][string]$Installer, [ValidateSet('x86','x64')][string]$Architecture = 'x64')
$ErrorActionPreference = 'Stop'
if (($Architecture -eq 'x86' -and [IntPtr]::Size -ne 4) -or ($Architecture -eq 'x64' -and [IntPtr]::Size -ne 8)) { throw 'Run lifecycle tests in PowerShell with the matching architecture' }
$Installer = (Resolve-Path $Installer).Path
$brand = Get-Content branding/zavix.json | ConvertFrom-Json
$app = $brand.app_name
$folder = Join-Path $env:ProgramFiles $app
$exe = Join-Path $folder "$app.exe"
$stateKey = "HKLM:\SOFTWARE\$app\InstallState\$app"
$evidence = @()
function Install-Package([string]$path, [string]$label) {
    $log = Join-Path $PWD "msi-$label.log"
    $p = Start-Process msiexec.exe -ArgumentList @('/i', "`"$path`"", '/qn', '/norestart', '/l*v', "`"$log`"") -PassThru -Wait
    if ($p.ExitCode -notin @(0,3010)) { Get-Content $log -Tail 70; throw "$label failed: $($p.ExitCode)" }
    $script:evidence += @{case=$label; exit_code=$p.ExitCode}
}
function Check-Installed {
    if (-not (Test-Path $exe)) { throw 'MSI did not install the executable' }
    $process = Start-Process $exe -ArgumentList '--zavix-diagnostics' -PassThru -Wait -RedirectStandardOutput runtime-installed.json -RedirectStandardError runtime-installed-error.txt
    if ($process.ExitCode -ne 0) { throw 'Installed diagnostics failed' }
    $data = Get-Content runtime-installed.json | ConvertFrom-Json
    if (-not $data.installed -or $data.architecture -ne $Architecture -or $data.approve_mode -ne 'click' -or $data.server -ne '187.77.241.190:21116' -or $data.api -ne 'https://remote.zavix.app' -or $data.version -ne $brand.version) { throw 'Installed native configuration or detection differs' }
    $service = Get-CimInstance Win32_Service -Filter "Name='$app'"
    if ($service.State -ne 'Running' -or $service.StartName -ne 'LocalSystem' -or $service.PathName -notlike "*$exe*--service*") { throw 'Installed service did not start with the intended binary' }
    if (-not (Test-Path (Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) 'ZAVIX Remote.lnk'))) { throw 'Desktop shortcut missing' }
    if (-not (Test-Path (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs\ZAVIX Remote.lnk'))) { throw 'Start menu shortcut missing' }
    $script:evidence += @{case='installed runtime and service';result='passed';runtime=$data;service=@{name=$service.Name;state=$service.State;account=$service.StartName}}
}
if (Test-Path $stateKey) { throw 'The test runner already contains a ZAVIX installation' }
# A separate registry/file sentinel must survive installation, upgrades and removal.
$legacy = 'HKLM:\SOFTWARE\RustDesk\ZavixMsiTestSentinel'
if (Test-Path $legacy) { throw 'Unexpected legacy test state' }
New-Item $legacy -Force | Out-Null
New-ItemProperty $legacy -Name Keep -Value 'unchanged' -PropertyType String | Out-Null
try {
    $old = (Resolve-Path msi-test/previous-version.msi).Path
    Install-Package $old 'previous-version-install'
    Check-Installed
    $oldCode = (Get-ItemProperty $stateKey).MsiProductCode
    Install-Package $Installer 'upgrade-to-release'
    Check-Installed
    $currentCode = (Get-ItemProperty $stateKey).MsiProductCode
    if ($currentCode -eq $oldCode) { throw 'Major upgrade did not replace the prior MSI product' }
    $downgrade = Start-Process msiexec.exe -ArgumentList @('/i', "`"$old`"", '/qn', '/norestart', '/l*v', 'msi-downgrade.log') -PassThru -Wait
    if ($downgrade.ExitCode -eq 0) { throw 'Downgrade was incorrectly allowed' }
    if ((Get-ItemProperty $stateKey).MsiProductCode -ne $currentCode) { throw 'Blocked downgrade changed installation state' }
    $evidence += @{case='downgrade blocked';exit_code=$downgrade.ExitCode}
    Remove-Item (Join-Path $folder 'PRIVACY.md')
    $repair = Start-Process msiexec.exe -ArgumentList @('/fa', $currentCode, '/qn', '/norestart', '/l*v', 'msi-repair.log') -PassThru -Wait
    if ($repair.ExitCode -notin @(0,3010) -or -not (Test-Path (Join-Path $folder 'PRIVACY.md'))) { throw 'MSI repair did not restore the removed installed file' }
    $evidence += @{case='repair missing file';exit_code=$repair.ExitCode}
    $remove = Start-Process msiexec.exe -ArgumentList @('/x', $currentCode, '/qn', '/norestart', '/l*v', 'msi-uninstall.log') -PassThru -Wait
    if ($remove.ExitCode -notin @(0,3010)) { throw 'MSI uninstall failed' }
    if (Test-Path $exe) { throw 'Executable remained after uninstall' }
    if (Get-Service $app -ErrorAction SilentlyContinue) { throw 'Service remained after uninstall' }
    if (Test-Path $stateKey) { throw 'Installer registry state remained after uninstall' }
    if (Test-Path (Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) 'ZAVIX Remote.lnk')) { throw 'Desktop shortcut remained after uninstall' }
    if ((Get-ItemProperty $legacy).Keep -ne 'unchanged') { throw 'Legacy RustDesk state was changed' }
    $evidence += @{case='uninstall and legacy sentinel preservation';result='passed'}
    if ((Get-AuthenticodeSignature $Installer).Status -ne 'NotSigned') { throw 'Unexpected package signature state' }
    $evidence | ConvertTo-Json -Depth 6 | Set-Content windows-msi-evidence.json
} finally {
    if (Test-Path $stateKey) {
        $code = (Get-ItemProperty $stateKey).MsiProductCode
        Start-Process msiexec.exe -ArgumentList @('/x', $code, '/qn', '/norestart') -Wait
    }
    Remove-Item $legacy -Recurse -Force
}
Write-Host 'MSI: installed runtime, service, shortcuts, upgrade, blocked downgrade, repair and uninstall passed'
