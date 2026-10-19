param([Parameter(Mandatory=$true)][string]$InstallDirectory)
$ErrorActionPreference = 'Stop'
$expectedExe = Join-Path ([IO.Path]::GetFullPath($InstallDirectory)) 'CleanTemp.exe'
# Only tasks that actually launch this installed executable are removed.
Get-ScheduledTask -TaskName 'CleanTemp-User-*' -ErrorAction SilentlyContinue | ForEach-Object {
    $task = $_
    foreach ($action in $task.Actions) {
        if ($action.Execute -eq $expectedExe -and $action.Arguments -eq '--scheduled-clean') {
            Unregister-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Confirm:$false
            break
        }
    }
}
# Remove known app-owned data only. Other Windows accounts keep their local logs.
$owned = Join-Path $env:LOCALAPPDATA 'CleanTemp'
if (Test-Path -LiteralPath $owned) {
    $folder = Get-Item -LiteralPath $owned -Force
    if (-not ($folder.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        foreach ($name in @('schedule.json','schedule.new','schedule.json.new','last-clean.json','last-clean.json.new','tour-seen','history.json','history.json.new','preferences.json','preferences.json.new')) {
            $target = Join-Path $owned $name
            if (Test-Path -LiteralPath $target -PathType Leaf) { Remove-Item -LiteralPath $target -Force }
        }
        $logs = Join-Path $owned 'logs'
        if (Test-Path -LiteralPath $logs -PathType Container) {
            $logFolder = Get-Item -LiteralPath $logs -Force
            if (-not ($logFolder.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                foreach ($name in @('cleantemp.log','cleantemp.log.1','cleantemp.log.2')) {
                    $target = Join-Path $logs $name
                    if (Test-Path -LiteralPath $target -PathType Leaf) { Remove-Item -LiteralPath $target -Force }
                }
                if (-not (Get-ChildItem -LiteralPath $logs -Force)) { Remove-Item -LiteralPath $logs }
            }
        }
        if (-not (Get-ChildItem -LiteralPath $owned -Force)) { Remove-Item -LiteralPath $owned }
    }
}
