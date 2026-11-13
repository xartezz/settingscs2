#ifndef AppVersion
  #define AppVersion "0.5.1"
#endif
[Setup]
AppId={{F1A6C765-6D47-485D-98CF-48F264C8B14F}
AppName=SETTINGSCS2 Desktop
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\SettingsCS2
DefaultGroupName=SETTINGSCS2
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=SettingsCS2-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\SettingsCS2.exe
CloseApplications=yes
RestartApplications=no
[Files]
Source: "..\build-dist\SettingsCS2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\SETTINGSCS2"; Filename: "{app}\SettingsCS2.exe"; AppUserModelID: "SettingsCS2.Desktop"
Name: "{autodesktop}\SETTINGSCS2"; Filename: "{app}\SettingsCS2.exe"; AppUserModelID: "SettingsCS2.Desktop"
[Registry]
Root: HKCU; Subkey: "Software\Classes\settingscs2"; ValueType: string; ValueData: "URL:SettingsCS2"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\settingscs2"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCU; Subkey: "Software\Classes\settingscs2\shell\open\command"; ValueType: string; ValueData: """{app}\SettingsCS2.exe"" ""%1"""
[Run]
Filename: "{app}\SettingsCS2.exe"; Flags: nowait runasoriginaluser
; Personal library is outside {app}; uninstall/update never deletes it.

