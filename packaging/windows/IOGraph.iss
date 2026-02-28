#define MyAppName "IOGraph"
#ifndef AppVersion
  #define AppVersion "dev"
#endif
#ifndef SourceDir
  #error SourceDir is not defined
#endif
#ifndef OutputDir
  #error OutputDir is not defined
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "IOGraph-windows-setup"
#endif

[Setup]
AppId={{B3BFF647-46B8-4A17-B61F-2CA6C9D9CF0A}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=IOGraphica
DefaultDirName={autopf}\IOGraph
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\IOGraph.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\IOGraph.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\IOGraph.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\IOGraph.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
