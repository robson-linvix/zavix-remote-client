param([Parameter(Mandatory=$true)][string]$Bundle)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path (Join-Path $Bundle 'ZAVIXRemote.exe')).Path
$p = Start-Process $exe -PassThru -RedirectStandardOutput sciter-startup-output.txt -RedirectStandardError sciter-startup-error.txt
try {
    Start-Sleep -Seconds 8
    $p.Refresh()
    if ($p.HasExited) { throw "Legacy GUI exited during startup: $($p.ExitCode)" }
    if ($p.MainWindowHandle -eq 0) { throw 'Legacy GUI did not create a top-level window in the runner desktop' }
    $output = (Get-Content sciter-startup-output.txt -Raw -ErrorAction SilentlyContinue) + (Get-Content sciter-startup-error.txt -Raw -ErrorAction SilentlyContinue)
    if ($output -match 'SyntaxError|ReferenceError|error parsing script') { throw 'Legacy GUI reported a script startup error' }
    @{result='passed';case='x86 GUI startup under WOW64';window_title=$p.MainWindowTitle;actual_windows_7_8_tested=$false} | ConvertTo-Json | Set-Content sciter-startup-evidence.json
} finally {
    if (-not $p.HasExited) { taskkill /PID $p.Id /T /F | Out-Null }
    Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $exe } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
