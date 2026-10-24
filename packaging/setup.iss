; Oto Yedek Parça Otomasyonu - Inno Setup Kurulum Betiği
; Windows 10/11 Tek Tıkla Kurulum Paketi

#define MyAppName "Oto Yedek Parca Otomasyonu"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Oto Yedek Parca"
#define MyAppExeName "OtoYedekParca.exe"

[Setup]
AppId={{8660E92B-E5E7-47BE-80B8-F1E7BF8BCC30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\OtoYedekParca
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist\installer
OutputBaseFilename=OtoYedekParca_Setup_v1.0.0
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\OtoYedekParca\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\THIRD_PARTY_LICENSES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Uygulama kaldırılırken kullanıcı verilerinin korunması / sorulması
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\OtoYedekParca');
    // Sessiz modda (/SILENT veya /VERYSILENT) kullanıcı verisi ASLA silinmez.
    if not WizardSilent then
    begin
      if DirExists(DataDir) then
      begin
        // Varsayılan seçenek HAYIR (MB_DEFBUTTON2)
        if MsgBox('Dükkan veritabanı, sipariş geçmişi ve yedekleriniz şu konumda korunmaktadır:' + #13#10 +
                  DataDir + #13#10#13#10 +
                  'Bu veritabanını ve tüm yedekleri kalıcı olarak silmek istiyor musunuz?' + #13#10 +
                  '(Tavsiye edilen: İleride tekrar kuracaksanız veya verilerinizi saklamak istiyorsanız HAYIR seçiniz)',
                  mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        begin
          DelTree(DataDir, True, True, True);
        end;
      end;
    end;
  end;
end;
