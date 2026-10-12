# ZAVIX modifications, 2026-10-12: execute real Windows binaries, including hostile filename inputs.
param([Parameter(Mandatory=$true)][string]$Bundle)
$ErrorActionPreference = 'Stop'
$bundlePath = (Resolve-Path $Bundle).Path
$names = @('ZAVIXRemote.exe', 'ZAVIXRemote-host=attacker.invalid,key=AA,api=attacker.invalid,relay=attacker.invalid,.exe', 'ZAVIXRemote--eyJob3N0IjoiYXR0YWNrZXIuaW52YWxpZCJ9.exe')
$results = @()
Set-Content -Path (Join-Path $bundlePath 'custom.txt') -Value 'hostile-invalid-external-configuration'
try {
    foreach ($name in $names) {
        $exePath = Join-Path $bundlePath $name
        if ($name -ne 'ZAVIXRemote.exe') { Copy-Item (Join-Path $bundlePath 'ZAVIXRemote.exe') $exePath }
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $exePath
        $psi.Arguments = '--zavix-diagnostics'
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.EnvironmentVariables['RUSTDESK_APPNAME'] = $name
        $proc = [System.Diagnostics.Process]::Start($psi)
        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()
        if (-not $proc.WaitForExit(30000)) { $proc.Kill(); throw 'Diagnostic timeout' }
        if ($proc.ExitCode -ne 0) { throw "Diagnostic failed: $stderr" }
        $line = ($stdout -split "`n" | Where-Object { $_.Trim().StartsWith('{') } | Select-Object -Last 1)
        if (-not $line) { throw "No diagnostic JSON in runtime output: $stdout $stderr" }
        $data = $line | ConvertFrom-Json
        if ($data.app_name -ne 'ZAVIXRemote' -or $data.server -ne '187.77.241.190' -or $data.relay -ne '187.77.241.190:21117' -or $data.api -ne 'https://remote.zavix.app' -or $data.approve_mode -ne 'click' -or $data.updater -ne 'N' -or -not $data.incoming_only) { throw 'Runtime configuration changed or is unsafe' }
        $results += @{case=$name;result='passed';configuration=$data}
        if ($name -ne 'ZAVIXRemote.exe') { Remove-Item $exePath }
    }
} finally { Remove-Item (Join-Path $bundlePath 'custom.txt') -ErrorAction SilentlyContinue }
$results | ConvertTo-Json -Depth 6 | Set-Content windows-runtime-evidence.json
Write-Host 'Windows runtime: brand, embedded configuration, custom.txt rejection and filename redirection tests passed'
