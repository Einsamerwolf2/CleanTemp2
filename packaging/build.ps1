param(
    [string]$InnoCompiler = '',
    [switch]$PackageWithoutRuntimeValidation,
    [switch]$BundleOnly,
    [ValidatePattern('^$|^[A-Fa-f0-9]{40}$')][string]$CertificateThumbprint = '',
    [string]$SignToolPath = '',
    [string]$TimestampUrl = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar o Python.' }
}
& $pythonExe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as ferramentas de compilação.' }
& $pythonExe packaging/create_guide.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o guia em PDF.' }
& $pythonExe -m flake8 backend/app.py
if ($LASTEXITCODE -ne 0) { throw 'O backend não passou na verificação do Flake8.' }
& $pythonExe packaging/create_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o ícone.' }
& $pythonExe -m unittest discover -s backend/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Os testes falharam.' }
& $pythonExe -m PyInstaller --noconfirm --workpath .tools/pyinstaller packaging/CleanTemp.spec
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o executável.' }
& $pythonExe packaging/collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao incluir licenças das dependências.' }
& $pythonExe packaging/verify_bundle.py
if ($LASTEXITCODE -ne 0) { throw 'O pacote não passou na verificação de recursos.' }
if ($BundleOnly) { Write-Host 'Pacote completo gerado em dist/CleanTemp. Não distribua build/ ou .tools/.'; exit 0 }
$reportPath = Join-Path $projectRoot 'dist\smoke-test.json'
$programPath = Join-Path $projectRoot 'dist\CleanTemp\CleanTemp.exe'
$signCommand = ''
if ($CertificateThumbprint) {
    if ($TimestampUrl -notmatch '^https://[A-Za-z0-9.-]+(?::[0-9]+)?(?:/[A-Za-z0-9_./-]*)?$') {
        throw 'Informe -TimestampUrl HTTPS do serviço de assinatura contratado.'
    }
    $signCertificate = Get-Item -LiteralPath ('Cert:\CurrentUser\My\' + $CertificateThumbprint)
    if (-not $signCertificate.HasPrivateKey -or $signCertificate.Subject -eq $signCertificate.Issuer -or -not $signCertificate.Verify()) {
        throw 'É necessário um certificado de assinatura válido e reconhecido. Certificados autoassinados não são usados para publicação.'
    }
    if (-not $SignToolPath) {
        $SignToolPath = (Get-Command signtool.exe -ErrorAction Stop).Source
    }
    $SignToolPath = (Resolve-Path -LiteralPath $SignToolPath).Path
    & $SignToolPath sign /sha1 $CertificateThumbprint /s My /fd SHA256 /tr $TimestampUrl /td SHA256 $programPath
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível assinar o executável.' }
    if ((Get-AuthenticodeSignature -LiteralPath $programPath).Status -ne 'Valid') {
        throw 'A assinatura do executável não foi validada.'
    }
    # Inno signs Setup, the uninstaller and temporary self-copies with this command.
    $signCommand = '"' + $SignToolPath + '" sign /sha1 ' + $CertificateThumbprint + ' /s My /fd SHA256 /tr ' + $TimestampUrl + ' /td SHA256 $f'
}
foreach ($oldReport in @('smoke-test.json','functional-packaged.json','runtime-validation-failure.json')) {
    $oldReportPath = Join-Path $projectRoot ('dist\' + $oldReport)
    if (Test-Path -LiteralPath $oldReportPath) { Remove-Item -LiteralPath $oldReportPath }
}
try {
    $smokeTest = Start-Process -FilePath $programPath -ArgumentList @('--self-test-report', ('"' + $reportPath + '"')) -PassThru -WindowStyle Hidden
    if (-not $smokeTest.WaitForExit(30000)) { throw 'A verificação do executável excedeu 30 segundos.' }
    if ($smokeTest.ExitCode -ne 0) { throw 'O teste do executável falhou. Consulte dist/smoke-test.json.' }
    $functionalPath = Join-Path $projectRoot 'dist\functional-packaged.json'
    $functional = Start-Process -FilePath $programPath -ArgumentList @('--functional-check-report', ('"' + $functionalPath + '"')) -PassThru -WindowStyle Hidden
    if (-not $functional.WaitForExit(90000)) { throw 'A validação funcional excedeu 90 segundos.' }
    if ($functional.ExitCode -ne 0) { throw 'A verificação funcional do executável falhou.' }
} catch {
    @{ version = '1.4.0'; ok = $false; error = $_.Exception.Message } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot 'dist\runtime-validation-failure.json') -Encoding UTF8
    if (-not $PackageWithoutRuntimeValidation) { throw }
    Write-Warning ('Pacote sem validação do executável: ' + $_.Exception.Message)
}
if (-not $InnoCompiler) {
    $candidates = @(
        (Join-Path $projectRoot '.tools\InnoSetup\ISCC.exe'),
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 7\ISCC.exe'
    )
    $InnoCompiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $InnoCompiler) { throw 'Instale o Inno Setup ou informe -InnoCompiler com o caminho de ISCC.exe.' }
if ($signCommand) {
    & $InnoCompiler /DSignRelease=1 ('/SCleanTempRelease=' + $signCommand) packaging/installer.iss
} else {
    & $InnoCompiler packaging/installer.iss
}
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o instalador.' }
$installer = Get-Item 'dist\installer\CleanTemp-Setup-1.4.0-x64.exe'
if ($CertificateThumbprint -and (Get-AuthenticodeSignature -LiteralPath $installer.FullName).Status -ne 'Valid') {
    throw 'A assinatura do instalador não foi validada.'
}
$installerHash = Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256
Set-Content -LiteralPath (Join-Path $installer.DirectoryName 'SHA256SUMS.txt') -Value ($installerHash.Hash + '  ' + $installer.Name) -Encoding ascii
$installerHash | Format-List
Write-Host ('Instalador criado: ' + $installer.FullName)



