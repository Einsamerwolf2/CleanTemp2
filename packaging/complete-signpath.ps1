param([Parameter(Mandatory=$true)][string]$InnoCompiler)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$signedDirectory=Join-Path $projectRoot 'dist\signpath\native-signed'
foreach ($filename in @('CleanTemp.exe','uninstaller.exe')) {
    $signedFile=Join-Path $signedDirectory $filename
    if ((Get-AuthenticodeSignature -LiteralPath $signedFile).Status -ne 'Valid') { throw ('Assinatura inválida: ' + $filename) }
}
$cacheInfo=Get-Content -LiteralPath (Join-Path $projectRoot 'dist\signpath\uninstaller-cache.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFileName($cacheInfo.cacheName) -ne $cacheInfo.cacheName) { throw 'Nome de cache inválido.' }
Copy-Item -LiteralPath (Join-Path $signedDirectory 'CleanTemp.exe') -Destination (Join-Path $projectRoot 'dist\CleanTemp\CleanTemp.exe') -Force
Copy-Item -LiteralPath (Join-Path $signedDirectory 'uninstaller.exe') -Destination (Join-Path $projectRoot ('dist\signpath\cache\' + $cacheInfo.cacheName)) -Force
& $InnoCompiler /DRemoteSigned=1 packaging/installer.iss
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível compilar com o desinstalador assinado.' }
Write-Host 'Instalador preparado para a segunda assinatura remota.'
