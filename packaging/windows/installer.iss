; Per-user installer; no user data is removed.
#ifndef AppVersion
#define AppVersion "0.2.0"
#endif

[Setup]
AppId={{539F5A80-CB59-4B6A-AC80-EF461D3B263C}
AppName=Transcript Studio
AppVersion={#AppVersion}
AppPublisher=Transcript Studio Contributors
DefaultDirName={localappdata}\Programs\Transcript Studio
DefaultGroupName=Transcript Studio
PrivilegesRequired=lowest
OutputDir=..\..\dist\installer
OutputBaseFilename=TranscriptStudio-Setup-{#AppVersion}-win-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\TranscriptStudio.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes

[Files]
Source: "..\..\dist\TranscriptStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Transcript Studio"; Filename: "{app}\TranscriptStudio.exe"
Name: "{autodesktop}\Transcript Studio"; Filename: "{app}\TranscriptStudio.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\TranscriptStudio.exe"; Description: "Abrir Transcript Studio"; Flags: postinstall nowait skipifsilent

; Data in %LOCALAPPDATA%\TranscriptStudio intentionally survives uninstall.
