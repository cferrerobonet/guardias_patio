#define MyAppName "Guardias de Patio"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "Carlos Ferrero Bonet"
#define MyAppExeName "GuardiasDePatio.exe"

[Setup]
AppId={{A4D57A08-8E76-4D42-9632-FAC2D8F91C7A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Guardias de Patio
DefaultGroupName=Guardias de Patio
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir=Output
OutputBaseFilename=GuardiasDePatio-{#MyAppVersion}-Windows-Setup
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
SetupIconFile=imagenes\logo.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "dist\GuardiasDePatio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Guardias de Patio"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Guardias de Patio"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Guardias de Patio"; Flags: nowait postinstall skipifsilent
