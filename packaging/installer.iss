#define AppVersion "1.4.0"
#include "..\.tools\runtime-required.iss"
[Setup]
AppId={{AB2270A8-CE83-4DCB-AE78-BF1356E9F62E}
#ifdef RemoteSignExport
SignTool=CleanTempExport
SignedUninstaller=yes
SignedUninstallerDir=..\dist\signpath\cache
#elif defined(RemoteSigned)
SignedUninstaller=yes
SignedUninstallerDir=..\dist\signpath\cache
#endif
#ifdef SignRelease
SignTool=CleanTempRelease
SignedUninstaller=yes
#endif
AppName=CleanTemp
AppVersion={#AppVersion}
AppPublisher=Edilson Enoque
AppPublisherURL=https://github.com/Einsamerwolf2/CleanTemp2
AppSupportURL=https://github.com/Einsamerwolf2/CleanTemp2/issues
AppUpdatesURL=https://github.com/Einsamerwolf2/CleanTemp2/releases
DefaultDirName={autopf}\CleanTemp
UsePreviousAppDir=no
DisableDirPage=yes
DefaultGroupName=CleanTemp
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\installer
OutputBaseFilename=CleanTemp-Setup-{#AppVersion}-x64
SetupIconFile=..\assets\cleantemp.ico
UninstallDisplayIcon={app}\CleanTemp.exe
LicenseFile=..\TERMS.txt
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardSmallImageFile=..\assets\wizard-small.bmp
WizardImageFile=..\assets\wizard-large.bmp
CloseApplications=yes
RestartApplications=no
[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos:"
[Files]
Source: "..\dist\CleanTemp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "remove-user-data.ps1"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\CleanTemp"; Filename: "{app}\CleanTemp.exe"; IconFilename: "{app}\CleanTemp.exe"
Name: "{autodesktop}\CleanTemp"; Filename: "{app}\CleanTemp.exe"; IconFilename: "{app}\CleanTemp.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\CleanTemp.exe"; Description: "Abrir CleanTemp"; Flags: nowait postinstall skipifsilent runasoriginaluser


[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\remove-user-data.ps1"" -InstallDirectory ""{app}"""; Flags: runhidden waituntilterminated; RunOnceId: "CleanTempRemoveSchedules"

[Code]
function RuntimeFilesPresent(): Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\CleanTemp.exe')) and
    FileExists(ExpandConstant('{app}\_internal\{#PythonDllName}')) and
    FileExists(ExpandConstant('{app}\_internal\VCRUNTIME140.dll')) and
    FileExists(ExpandConstant('{app}\_internal\VCRUNTIME140_1.dll')) and
    FileExists(ExpandConstant('{app}\_internal\_tkinter.pyd')) and
    FileExists(ExpandConstant('{app}\_internal\{#TclDllName}')) and
    FileExists(ExpandConstant('{app}\_internal\{#TkDllName}'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and not RuntimeFilesPresent() then
    RaiseException('A instalação ficou incompleta. Reinstale pelo CleanTemp-Setup. Não é necessário instalar Python ou bibliotecas separadamente.');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if WizardSilent and (ExpandConstant('{param:ACCEPTTERMS|0}') <> '1') then
  begin
    MsgBox('A instalação exige a aceitação dos termos. Leia TERMS.txt e use /ACCEPTTERMS=1 somente se concordar.', mbError, MB_OK);
    Result := False;
  end;
end;
