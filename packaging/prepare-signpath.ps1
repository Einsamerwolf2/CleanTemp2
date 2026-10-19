param([Parameter(Mandatory=$true)][string]$InnoCompiler)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$inputDirectory=Join-Path $projectRoot 'dist\signpath\native-input'
New-Item -ItemType Directory -Path $inputDirectory -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $projectRoot 'dist\signpath\cache') -Force | Out-Null
foreach ($staleFile in @((Join-Path $inputDirectory 'uninstaller.exe'),(Join-Path $projectRoot 'dist\signpath\uninstaller-cache.json'))) {
    if (Test-Path -LiteralPath $staleFile) { Remove-Item -LiteralPath $staleFile }
}
$exportScript=Join-Path $PSScriptRoot 'export-signing-file.ps1'
$exportCommand='powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $q' + $exportScript + '$q -FilePath $f'
& $InnoCompiler /DRemoteSignExport=1 ('/SCleanTempExport=' + $exportCommand) packaging/installer.iss
if ($LASTEXITCODE -eq 0) { throw 'A preparação deveria ter parado antes da criação do instalador.' }
if (-not (Test-Path -LiteralPath (Join-Path $inputDirectory 'uninstaller.exe'))) { throw 'O compilador não exportou o desinstalador.' }
Copy-Item -LiteralPath (Join-Path $projectRoot 'dist\CleanTemp\CleanTemp.exe') -Destination (Join-Path $inputDirectory 'CleanTemp.exe') -Force
Write-Host 'Aplicativo e desinstalador preparados para a primeira assinatura remota.'
