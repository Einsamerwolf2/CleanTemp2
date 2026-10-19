param([Parameter(Mandatory=$true)][string]$FilePath)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$inputDirectory=Join-Path $projectRoot 'dist\signpath\native-input'
New-Item -ItemType Directory -Path $inputDirectory -Force | Out-Null
Copy-Item -LiteralPath $FilePath -Destination (Join-Path $inputDirectory 'uninstaller.exe') -Force
@{ cacheName=([IO.Path]::GetFileName($FilePath) -replace '\.tmp$','') } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot 'dist\signpath\uninstaller-cache.json') -Encoding UTF8
# Intentionally stop this preparation pass before creating an unsigned installer.
exit 17

