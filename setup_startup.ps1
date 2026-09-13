<#
    Register / unregister "UESTC AutoLogin" in the Windows Startup folder.

    Install:   powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_startup.ps1
    Uninstall: powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_startup.ps1 -Remove

    The shortcut points at always_online.bat in this folder and starts it
    minimized, so the auto-reconnect monitor comes up every time you log in.
#>
param(
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

$repoDir = $PSScriptRoot
$target = Join-Path $repoDir 'always_online.bat'
$startupDir = [Environment]::GetFolderPath('Startup')
$lnkPath = Join-Path $startupDir 'UESTC AutoLogin.lnk'

if ($Remove) {
    if (Test-Path -LiteralPath $lnkPath) {
        Remove-Item -LiteralPath $lnkPath -Force
        Write-Host "Removed: $lnkPath"
    }
    else {
        Write-Host "Not found: $lnkPath"
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $target)) {
    throw "Launcher not found: $target"
}

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($lnkPath)
$lnk.TargetPath = $target
$lnk.WorkingDirectory = $repoDir
$lnk.WindowStyle = 7          # 7 = minimized
$lnk.Description = 'UESTC campus network auto login (reconnect on drop)'
$lnk.Save()

Write-Host "Installed:"
Write-Host "  shortcut: $lnkPath"
Write-Host "  launcher: $target"
