<#
    UESTC AutoLogin - register / remove a Scheduled Task that starts the
    reconnect monitor at system boot, with NO interactive logon required.

    Install (asks for administrator approval once):
        powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1

    Status:
        powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1 -Status

    Remove:
        powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1 -Remove

    How it works: the task runs always_online.bat as the SYSTEM account 30 s
    after boot. Campus portal authentication is done per machine IP, so no
    desktop session is needed, and no Windows password is ever stored in the
    task - the campus account lives only in config.toml, which is git-ignored.

    NOTE: keep this file ASCII-only. Windows PowerShell 5.1 reads .ps1 files
    without a BOM as ANSI, so non-ASCII text here would end up garbled.
#>
[CmdletBinding()]
param(
    [switch]$Remove,
    [switch]$Status,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'

$taskName   = 'UESTC AutoLogin'
$repoDir    = $PSScriptRoot
$launcher   = Join-Path $repoDir 'always_online.bat'
$startupLnk = Join-Path ([Environment]::GetFolderPath('Startup')) 'UESTC AutoLogin.lnk'

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal $id).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Show-TaskStatus {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    }
    catch {
        # 0x80041003 = WBEM_E_ACCESS_DENIED. The task runs as SYSTEM, so a
        # non-elevated shell cannot read it back - that is NOT "not registered",
        # and reporting it as such would be a false negative.
        if ($_.Exception.Message -match '0x80041003|Access is denied|denied') {
            Write-Host "Cannot read '$taskName' from a non-elevated shell (access denied)."
            Write-Host 'The task runs as SYSTEM; run this script from an elevated PowerShell to'
            Write-Host 'see its status. Hint: check that a python.exe is running as SYSTEM, or'
            Write-Host 'look at the timestamp of logs\always_online.console.log.'
            return
        }
        Write-Host "Not registered: $taskName"
        return
    }
    $info = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Host "Task      : $taskName"
    Write-Host "State     : $($task.State)"
    Write-Host ("Last run  : {0}" -f $info.LastRunTime)
    Write-Host ("Last code : 0x{0:X8}" -f $info.LastTaskResult)
    Write-Host ("Next run  : {0}" -f $info.NextRunTime)
}

if ($Status) {
    Show-TaskStatus
    exit 0
}

if (-not (Test-IsAdmin)) {
    Write-Host 'Administrator rights are required; relaunching elevated (UAC prompt)...'
    $elevatedArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"")
    if ($Remove)  { $elevatedArgs += '-Remove' }
    if ($NoStart) { $elevatedArgs += '-NoStart' }
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $elevatedArgs
    exit 0
}

if ($Remove) {
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Removed scheduled task: $taskName"
    }
    else {
        Write-Host "Not registered: $taskName"
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Launcher not found: $launcher"
}

if (Test-Path -LiteralPath $startupLnk) {
    Write-Host 'WARNING: the Startup-folder shortcut is also installed:'
    Write-Host "  $startupLnk"
    Write-Host '  With both, a second monitor starts at every logon. To drop that one:'
    Write-Host '  powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_startup.ps1 -Remove'
    Write-Host ''
}

$consoleLog = Join-Path $repoDir 'logs\always_online.console.log'

# Re-running the installer should also pick up config.toml changes, so stop the
# instance that is currently running before registering the fresh definition.
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and $existing.State -eq 'Running') {
    Write-Host 'Stopping the running monitor instance...'
    Stop-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 2
}

$action = New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\cmd.exe') `
    -Argument ('/c ""{0}" > "{1}" 2>&1"' -f $launcher, $consoleLog) `
    -WorkingDirectory $repoDir

# 30 s after boot so the network stack is ready; the monitor retries anyway.
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = 'PT30S'

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)      # no time limit

$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $taskName `
    -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
    -Description 'UESTC campus network auto login (starts at boot, no logon required)' `
    -Force | Out-Null

Write-Host "Registered scheduled task: $taskName"
Write-Host "  launcher : $launcher"
Write-Host '  identity : SYSTEM (starts at boot, no interactive logon needed)'
Write-Host "  logs     : $(Join-Path $repoDir 'logs')"
Write-Host "  console  : $consoleLog"

if (-not $NoStart) {
    Start-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 2
    Write-Host ''
    Show-TaskStatus
}

Write-Host ''
Write-Host 'Remove with: powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1 -Remove'
