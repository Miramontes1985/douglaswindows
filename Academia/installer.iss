; Inno Setup 6, compilador de 32 bits. BuildArchitecture: auto, x86 ou x64.
#ifndef BuildArchitecture
  #define BuildArchitecture "auto"
#endif
#define AppName "Power Academia"
#define AppVersion "1.0.0"
#define AppExeName "PowerAcademia.exe"

[Setup]
AppId={{992D68F0-973D-48E0-888B-D5C641D0E086}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Power Academia
DefaultDirName={localappdata}\Programs\Power Academia
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
#if BuildArchitecture == "x64"
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
OutputBaseFilename=Instalar-Power-Academia-64bits
#elif BuildArchitecture == "x86"
MinVersion=10.0
ArchitecturesAllowed=x86compatible
OutputBaseFilename=Instalar-Power-Academia-32bits
#else
MinVersion=10.0
ArchitecturesAllowed=x86compatible or x64compatible
OutputBaseFilename=Instalar-Power-Academia
#endif
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes
UseSetupLdr=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce

[InstallDelete]
; Apenas bibliotecas instaladas pelo aplicativo; cadastros ficam fora desta pasta.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
#if BuildArchitecture == "x86"
Source: "dist\x86\PowerAcademia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#elif BuildArchitecture == "x64"
Source: "dist\x64\PowerAcademia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#else
Source: "dist\x86\PowerAcademia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: not Use64BitVersion
Source: "dist\x64\PowerAcademia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: Use64BitVersion
#endif
Source: "LEIA-ME.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir Power Academia"; Flags: nowait postinstall skipifsilent

[Code]
function Use64BitVersion: Boolean;
var
  WindowsVersion: TWindowsVersion;
begin
  GetWindowsVersionEx(WindowsVersion);
  Result := Is64BitInstallMode and
    ((WindowsVersion.Major > 10) or
     ((WindowsVersion.Major = 10) and (WindowsVersion.Build >= 17763)));
end;

; Dados e backups em {localappdata}\DouglasAcademia são preservados.
