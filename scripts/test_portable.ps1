# ZAVIX Windows V1: verify the executable delivered to the customer after extraction.
param([Parameter(Mandatory=$true)][string]$Executable)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path $Executable).Path
$versionInfo = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($exe)
if ($versionInfo.ProductName -ne 'ZAVIX Remote' -or $versionInfo.FileDescription -ne 'ZAVIX Remote') { throw 'Final executable has incorrect Windows branding' }
$signature = Get-AuthenticodeSignature $exe
if ($signature.Status -ne 'NotSigned') { throw "Unexpected signature status: $($signature.Status)" }
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $exe
$psi.Arguments = '--zavix-diagnostics'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()
$complete = [System.Threading.Tasks.Task]::WhenAll([System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask))
if (-not $complete.Wait(60000) -or -not $proc.WaitForExit(5000)) {
    if (-not $proc.HasExited) { $proc.Kill($true) }
    throw 'Portable extraction or diagnostic timed out'
}
if ($proc.ExitCode -ne 0) { throw "Portable executable failed: $($stderrTask.Result)" }
$line = ($stdoutTask.Result -split "`n" | Where-Object { $_.Trim().StartsWith('{') } | Select-Object -Last 1)
if (-not $line) { throw "Portable executable produced no diagnostic: $($stdoutTask.Result) $($stderrTask.Result)" }
$data = $line | ConvertFrom-Json
if ($data.app_name -ne 'ZAVIXRemote' -or $data.server -ne '187.77.241.190:21116' -or $data.api -ne 'https://remote.zavix.app' -or $data.approve_mode -ne 'click' -or $data.updater -ne 'N' -or -not $data.incoming_only -or $data.filename_configuration) { throw 'Portable runtime configuration is unsafe' }
$payload = Join-Path $env:LOCALAPPDATA 'zavixremote'
foreach ($file in @('ZAVIXRemote.exe', 'librustdesk.dll', 'LICENCE', 'NOTICE-ZAVIX.md', 'legal/cargo-inventory.json', 'legal/WindowInjection-LICENSE.txt')) {
    if (-not (Test-Path (Join-Path $payload $file) -PathType Leaf)) { throw "Portable payload is missing $file" }
}
@{result='passed';artifact=(Split-Path $exe -Leaf);sha256=(Get-FileHash $exe -Algorithm SHA256).Hash.ToLower();signature='NotSigned';product_name=$versionInfo.ProductName;configuration=$data;payload_notices=$true} | ConvertTo-Json -Depth 6 | Set-Content SignOutput/portable-runtime-evidence.json
Write-Host 'Final portable EXE: extraction, embedded runtime configuration and original notices passed'
