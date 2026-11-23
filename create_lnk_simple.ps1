$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path $desktop 'RetroVault.lnk'
$target = 'd:\Documentos Nilton\Games\RetroVault\start.bat'
$workDir = 'd:\Documentos Nilton\Games\RetroVault'
$sh = New-Object -ComObject WScript.Shell
$sc = $sh.CreateShortcut($lnkPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $workDir
# Optionally set icon if it exists
$iconPath = 'd:\Documentos Nilton\Games\RetroVault\RetroVault.ico'
if (Test-Path $iconPath) { $sc.IconLocation = $iconPath }
$sc.Save()
Write-Output "RetroVault shortcut created at $lnkPath"