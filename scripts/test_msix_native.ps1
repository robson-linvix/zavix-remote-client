param([string]$Bundle = './dist')
$ErrorActionPreference = 'Stop'
$profile = Get-Content branding/msix-profile.json | ConvertFrom-Json
$exe = Join-Path (Resolve-Path $Bundle) ($profile.app_name + '.exe')
function Diagnostic($argument) {
    $info = [System.Diagnostics.ProcessStartInfo]::new($exe, $argument)
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $process = [System.Diagnostics.Process]::Start($info)
    $stdout = $process.StandardOutput.ReadToEnd()
    if (-not $process.WaitForExit(30000)) { $process.Kill(); throw "Diagnostic timeout: $argument" }
    if ($process.ExitCode -ne 0) { throw "Diagnostic failed: $argument" }
    return ($stdout -split "`n" | Where-Object { $_.Trim().StartsWith('{') } | Select-Object -Last 1 | ConvertFrom-Json)
}
$native = Diagnostic '--zavix-diagnostics'
$store = Diagnostic '--msix-diagnostics'
if ($native.app_name -ne $profile.app_name -or $native.product_name -ne $profile.product_name -or $native.version -ne $profile.version -or $native.architecture -ne 'x64' -or $native.server -ne '187.77.241.190:21116' -or $native.relay -ne '187.77.241.190:21117' -or $native.api -ne 'https://remote.zavix.app' -or $native.filename_configuration) { throw 'Wrong compiled Store identity/configuration' }
if ($store.profile -ne 'store-assisted' -or -not $store.installation_disabled -or $store.can_elevate -or -not $store.close_exits -or -not $store.incoming_only -or $store.approve_mode -ne 'click' -or $store.verification_method -ne 'use-temporary-password' -or $store.updater -ne 'N') { throw 'Store assisted restrictions failed' }
foreach ($argument in @('--install-service', '--service', '--elevate', '--run-as-system', '--portable-service', '--tray', '--after-install', '--before-uninstall', '--silent-install')) {
    $process = Start-Process -FilePath $exe -ArgumentList $argument -PassThru
    if (-not $process.WaitForExit(15000)) { $process.Kill(); throw "Blocked command timed out: $argument" }
    if ($process.ExitCode -ne 64) { throw "Management command was not blocked: $argument ($($process.ExitCode))" }
}
if (Get-Service -Name $profile.app_name -ErrorAction SilentlyContinue) { throw 'Store edition created a service' }
@{ native=$native; store=$store; management_commands='blocked'; service='absent' } | ConvertTo-Json -Depth 6 | Set-Content windows-msix-native.json
