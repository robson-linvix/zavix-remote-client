param([Parameter(Mandatory=$true)][string]$Installer)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes,System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class InstallerWindowCapture {
 [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out Rect r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
}
'@
$brand=Get-Content branding/zavix.json | ConvertFrom-Json
$app=$brand.app_name
$exe=Join-Path $env:ProgramFiles "$app/$app.exe"
$Installer=(Resolve-Path $Installer).Path
function Find-Control($window,[string]$name) {
 $cond=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,$name)
 return $window.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$cond)
}
function Wait-Control($window,[string]$name) {
 $deadline=(Get-Date).AddSeconds(90)
 do { $c=Find-Control $window $name; if($c -and $c.Current.IsEnabled){return $c};Start-Sleep -Milliseconds 500 } while((Get-Date)-lt $deadline)
 throw "Installer control unavailable: $name"
}
function Invoke-Control($control) {
 $pattern=$control.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
 $pattern.Invoke()
}
function Capture([IntPtr]$handle,[string]$name) {
 $rect=New-Object InstallerWindowCapture+Rect
 if(-not [InstallerWindowCapture]::GetWindowRect($handle,[ref]$rect)){throw 'Window capture geometry unavailable'}
 $bitmap=New-Object Drawing.Bitmap(($rect.Right-$rect.Left),($rect.Bottom-$rect.Top))
 $graphics=[Drawing.Graphics]::FromImage($bitmap);$dc=$graphics.GetHdc()
 try { if(-not [InstallerWindowCapture]::PrintWindow($handle,$dc,2)){throw 'Window capture failed'} } finally {$graphics.ReleaseHdc($dc)}
 $bitmap.Save((Join-Path $PWD "UniversalOutput/$name.png"),[Drawing.Imaging.ImageFormat]::Png)
 $graphics.Dispose();$bitmap.Dispose()
}
$legacyRoot=Join-Path $env:TEMP ('remote-installer-legacy-ui-'+$app)
if(Test-Path $legacyRoot){throw 'Legacy GUI staging already exists'}
try {
 $legacyMsi=(Resolve-Path "UniversalOutput/$app-$($brand.version)-x86.msi").Path
 $extract=Start-Process msiexec.exe -ArgumentList @('/a',"`"$legacyMsi`"",'/qn',"TARGETDIR=`"$legacyRoot`"",'/l*v','installer-ui-legacy.log') -Wait -PassThru
 if($extract.ExitCode -ne 0){throw 'Legacy MSI extraction failed'}
 $legacyExe=Get-ChildItem $legacyRoot -Recurse -Filter "$app.exe" | Select-Object -First 1
 if(-not $legacyExe){throw 'Legacy GUI payload missing'}
 $legacy=Start-Process $legacyExe.FullName -PassThru
 Start-Sleep -Seconds 8
 $legacy.Refresh()
 if($legacy.HasExited -or $legacy.MainWindowHandle -eq 0){throw 'Branded legacy GUI did not open'}
 Capture $legacy.MainWindowHandle 'installed-app-x86'
 $legacyTitle=$legacy.MainWindowTitle
 Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $legacyExe.FullName} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}
 $process=Start-Process $Installer -ArgumentList @('/install','/norestart','/log','installer-ui.log') -PassThru
 $deadline=(Get-Date).AddSeconds(45)
 do { $uiProcess=Get-Process | Where-Object {$_.MainWindowTitle -eq "Instalação — $($brand.product_name)"} | Select-Object -First 1; if($uiProcess){$process=$uiProcess;break};Start-Sleep -Milliseconds 500 } while((Get-Date)-lt $deadline)
 if($process.MainWindowHandle -eq 0){throw 'Interactive installer has no window'}
 $window=[System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
 $accept=Wait-Control $window 'Li e aceito os termos das licenças'
 $toggle=$accept.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
 if($toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::On){$toggle.Toggle()}
 Capture $process.MainWindowHandle 'installer-welcome'
 Invoke-Control (Wait-Control $window 'Instalar')
 $finish=Wait-Control $window 'Concluir e abrir'
 $serviceBefore=Get-CimInstance Win32_Service -Filter "Name='$app'"
 if($serviceBefore.State -ne 'Running' -or $serviceBefore.StartMode -ne 'Auto'){throw 'Service must start before Finish opens the app'}
 $deadline=(Get-Date).AddSeconds(30)
 do {
  $server=Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe -and $_.CommandLine -match '--server'} | Select-Object -First 1
  if($server){break};Start-Sleep -Milliseconds 500
 } while((Get-Date)-lt $deadline)
 if(-not $server){throw 'Service did not start its remote server before GUI launch'}
 Capture $process.MainWindowHandle 'installer-complete'
 Invoke-Control $finish
 $deadline=(Get-Date).AddSeconds(35)
 do {
  $client=Get-Process -Name $app -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1
  if($client){break};Start-Sleep -Milliseconds 500
 } while((Get-Date)-lt $deadline)
 if(-not $client){throw 'Finishing the installer did not open the application'}
 $clientProcess=Get-CimInstance Win32_Process -Filter "ProcessId=$($client.Id)"
 $owner=Invoke-CimMethod -InputObject $clientProcess -MethodName GetOwner
 if($owner.User -ne $env:USERNAME){throw 'Finish must open the app as the interactive installer user'}
 Start-Sleep -Seconds 3
 Capture $client.MainWindowHandle 'installed-app'
 $service=Get-CimInstance Win32_Service -Filter "Name='$app'"
 if($service.State -ne 'Running' -or $service.StartMode -ne 'Auto'){throw 'Automatic service is not running after interactive installation'}
 @{result='passed';product=$brand.product_name;version=$brand.version;application_window=$client.MainWindowTitle;legacy_window=$legacyTitle;
 finish_opens_application=$true;launch_user=$owner.User;service_before_finish=$serviceBefore.State;server_before_finish=$true;service=$service.State;service_start=$service.StartMode;environment='Windows Server 2022 x64 CI; interactive installer UI';
 screenshots=@('installed-app-x86.png','installer-welcome.png','installer-complete.png','installed-app.png')} | ConvertTo-Json | Set-Content UniversalOutput/installer-ui-evidence.json
} finally {
 Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe -and $_.CommandLine -notmatch '--service|--server|--cm'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
 if($legacyExe){Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $legacyExe.FullName} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}}
 if(Test-Path $legacyRoot){Remove-Item $legacyRoot -Recurse -Force}
 if(Test-Path $exe){Start-Process $Installer -ArgumentList @('/uninstall','/quiet','/norestart','/log','installer-ui-uninstall.log') -Wait}
}
