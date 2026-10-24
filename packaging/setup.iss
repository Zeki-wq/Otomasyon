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
OutputDir=..\dist_installer
OutputBaseFilename=OtoYedekParca_Kurulum_v1.0.0
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\OtoYedekParca\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Uygulama kaldırılırken verilerin silinip silinmeyeceğini kullanıcıya sor
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\OtoYedekParca');
    if DirExists(DataDir) then
    begin
      if MsgBox('Dükkan veritabanı, sipariş geçmişi ve yedekleriniz şu konumda saklanmaktadır:' + #13#10 +
                DataDir + #13#10#13#10 +
                'Bu veritabanını ve tüm yedekleri kalıcı olarak silmek istiyor musunuz?' + #13#10 +
                '(İleride tekrar kuracaksanız veya verilerinizi saklamak istiyorsanız HAYIR seçiniz)',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
