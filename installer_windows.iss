; Script de Inno Setup para Guardias de Patio
; Crea un instalador profesional para Windows
; Requiere Inno Setup 6.0 o superior

#define MyAppName "Guardias de Patio"
#define MyAppVersion "2.7.0"
#define MyAppPublisher "Guardias de Patio"
#define MyAppURL "https://github.com/cferrerobonet/guardias_patio"
#define MyAppExeName "GuardiasDePatio.exe"

[Setup]
; Información de la aplicación
AppId={{8B5C9D4E-3F2A-4A1B-9E6D-7C8A5B2F1E3D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
InfoBeforeFile=README.md
OutputDir=dist
OutputBaseFilename=GuardiasDePatio-{#MyAppVersion}-Windows-Setup
SetupIconFile=imagenes\logo.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

; Información visual del instalador
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Archivos principales de la aplicación
Source: "dist\GuardiasDePatio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTA: No usar "Flags: ignoreversion" en archivos de sistema compartidos

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Crear base de datos inicial si no existe
    // (La aplicación lo hará automáticamente al iniciar)
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\guardias_patio.db"
Type: filesandordirs; Name: "{app}\logs"
