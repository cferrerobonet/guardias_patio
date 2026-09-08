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
; Sin exigir administrador: en un centro educativo lo normal es no tener esos
; permisos, y exigirlos impedía instalar. Con `lowest` la aplicación va al perfil
; del usuario; quien tenga permisos puede elegir instalarla para todos (BLD-006).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Cerrar la aplicación si está abierta, en vez de fallar al copiar los ficheros.
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll,*.pyd
RestartApplications=no
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

[Code]
{ Desinstalar la versión anterior antes de copiar la nueva. Sustituir ficheros
  sobre una instalación en uso dejaba «DeleteFile falló; código 5» y la
  instalación a medias. Los datos del usuario viven en %APPDATA%\GuardiasDePatio,
  fuera del programa, así que desinstalar no se lleva nada por delante. }

function DesinstaladorAnterior(): String;
var
  Clave: String;
  Valor: String;
begin
  Result := '';
  Clave := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' +
           ExpandConstant('{#SetupSetting("AppId")}') + '_is1';
  if RegQueryStringValue(HKCU, Clave, 'UninstallString', Valor) then
    Result := Valor
  else if RegQueryStringValue(HKLM, Clave, 'UninstallString', Valor) then
    Result := Valor;
  Result := RemoveQuotes(Result);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Desinstalador: String;
  Codigo: Integer;
  Espera: Integer;
begin
  Result := '';
  Desinstalador := DesinstaladorAnterior();
  if (Desinstalador = '') or (not FileExists(Desinstalador)) then
    exit;

  if not Exec(Desinstalador, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '',
              SW_HIDE, ewWaitUntilTerminated, Codigo) then
    exit;

  { El desinstalador se copia a sí mismo al temporal y vuelve enseguida: hay que
    esperar a que el de verdad termine antes de escribir en la carpeta. }
  Espera := 0;
  while FileExists(Desinstalador) and (Espera < 60) do
  begin
    Sleep(500);
    Espera := Espera + 1;
  end;
end;

