; ATK-Pro v2.2.1 Installer Script per Inno Setup
; Supporta 10 lingue con testi Unicode completi (arabo, ebraico, russo)
; Legge i disclaimer direttamente da assets/ 

#define MyAppName "ATK-Pro"
#define MyAppVersion "2.2.1"
#define MyAppPublisher "ATK-Pro Project"
#define MyAppURL "https://github.com/DanielePigoli/ATK-Pro"
#define MyAppExeName "ATK-Pro.exe"

[CustomMessages]
en.LicenseAcceptance=License Acceptance
it.LicenseAcceptance=Accettazione della Licenza
es.LicenseAcceptance=Aceptación de la Licencia
de.LicenseAcceptance=Lizenzakzeptanz
fr.LicenseAcceptance=Acceptation de la Licence
pt.LicenseAcceptance=Aceitação da Licença
nl.LicenseAcceptance=Licentieacceptatie
ar.LicenseAcceptance=قبول الترخيص
he.LicenseAcceptance=קבלת הרישיון
ru.LicenseAcceptance=Принятие лицензии
ja.LicenseAcceptance=ライセンス受け入れ
zh.LicenseAcceptance=许可证接受
pl.LicenseAcceptance=Akceptacja Licencji
tr.LicenseAcceptance=Lisans Kabulü
da.LicenseAcceptance=Licensakceptans
no.LicenseAcceptance=Lisenseaksept
vi.LicenseAcceptance=Chấp nhận Giấy phép
el.LicenseAcceptance=Αποδοχή Άδειας
ro.LicenseAcceptance=Acceptarea Licenței
sv.LicenseAcceptance=Licensacceptans
  ; Custom messages per localizzazione completa
  en.NameAndVersion=ATK-Pro v2.2.1
  it.NameAndVersion=ATK-Pro v2.2.1
  es.NameAndVersion=ATK-Pro v2.2.1
  de.NameAndVersion=ATK-Pro v2.2.1
  fr.NameAndVersion=ATK-Pro v2.2.1
  pt.NameAndVersion=ATK-Pro v2.2.1
  nl.NameAndVersion=ATK-Pro v2.2.1
  ar.NameAndVersion=ATK-Pro v2.2.1
  he.NameAndVersion=ATK-Pro v2.2.1
  ru.NameAndVersion=ATK-Pro v2.2.1
  ja.NameAndVersion=ATK-Pro v2.2.1
  zh.NameAndVersion=ATK-Pro v2.2.1
  pl.NameAndVersion=ATK-Pro v2.2.1
  tr.NameAndVersion=ATK-Pro v2.2.1
  da.NameAndVersion=ATK-Pro v2.2.1
  no.NameAndVersion=ATK-Pro v2.2.1
  vi.NameAndVersion=ATK-Pro v2.2.1
  el.NameAndVersion=ATK-Pro v2.2.1
  ro.NameAndVersion=ATK-Pro v2.2.1
  sv.NameAndVersion=ATK-Pro v2.2.1

  en.AdditionalIcons=Additional icons
  it.AdditionalIcons=Icone aggiuntive
  es.AdditionalIcons=Iconos adicionales
  de.AdditionalIcons=Zusätzliche Symbole
  fr.AdditionalIcons=Icônes supplémentaires
  pt.AdditionalIcons=Ícones adicionais
  nl.AdditionalIcons=Extra pictogrammen
  ar.AdditionalIcons=رموز إضافية
  he.AdditionalIcons=סמלים נוספים
  ru.AdditionalIcons=Дополнительные значки
  ja.AdditionalIcons=追加アイコン
  zh.AdditionalIcons=附加图标
  pl.AdditionalIcons=Dodatkowe ikony
  tr.AdditionalIcons=Ek simgeler
  da.AdditionalIcons=Yderligere ikoner
  no.AdditionalIcons=Flere ikoner
  vi.AdditionalIcons=Biểu tượng bổ sung
  el.AdditionalIcons=Πρόσθετα εικονίδια
  ro.AdditionalIcons=Icoane suplimentare
  sv.AdditionalIcons=Ytterligare ikoner

  en.CreateDesktopIcon=Create a desktop icon
  it.CreateDesktopIcon=Crea un'icona sul desktop
  es.CreateDesktopIcon=Crear un icono en el escritorio
  de.CreateDesktopIcon=Desktop-Symbol erstellen
  fr.CreateDesktopIcon=Créer une icône sur le bureau
  pt.CreateDesktopIcon=Criar um ícone na área de trabalho
  nl.CreateDesktopIcon=Bureaubladpictogram maken
  ar.CreateDesktopIcon=إنشاء رمز على سطح المكتب
  he.CreateDesktopIcon=צור סמל שולחן עבודה
  ru.CreateDesktopIcon=Создать значок на рабочем столе
  ja.CreateDesktopIcon=デスクトップアイコンを作成
  zh.CreateDesktopIcon=创建桌面图标
  pl.CreateDesktopIcon=Utwórz ikonę na pulpicie
  tr.CreateDesktopIcon=Masaüstü simgesi oluştur
  da.CreateDesktopIcon=Opret et skrivebordsikon
  no.CreateDesktopIcon=Opprett et skrivebordsikon
  vi.CreateDesktopIcon=Tạo biểu tượng trên màn hình
  el.CreateDesktopIcon=Δημιουργία εικονιδίου επιφάνειας εργασίας
  ro.CreateDesktopIcon=Crează a pictogramă pe desktop
  sv.CreateDesktopIcon=Skapa en skrivbordsikon

  en.CreateQuickLaunchIcon=Create a Quick Launch icon
  it.CreateQuickLaunchIcon=Crea un'icona di Avvio Rapido
  es.CreateQuickLaunchIcon=Crear un icono de inicio rápido
  de.CreateQuickLaunchIcon=Quick Launch-Symbol erstellen
  fr.CreateQuickLaunchIcon=Créer une icône de lancement rapide
  pt.CreateQuickLaunchIcon=Criar um ícone de inicialização rápida
  nl.CreateQuickLaunchIcon=Quick Launch-pictogram maken
  ar.CreateQuickLaunchIcon=إنشاء رمز التشغيل السريع
  he.CreateQuickLaunchIcon=צור סמל הפעלה מהירה
  ru.CreateQuickLaunchIcon=Создать значок быстрого запуска
  ja.CreateQuickLaunchIcon=クイック起動アイコンを作成
  zh.CreateQuickLaunchIcon=创建快速启动图标
  pl.CreateQuickLaunchIcon=Utwórz ikonę szybkiego uruchamiania
  tr.CreateQuickLaunchIcon=Hızlı başlat simgesi oluştur
  da.CreateQuickLaunchIcon=Opret et Quick Launch-ikon
  no.CreateQuickLaunchIcon=Opprett et hurtigstartikon
  vi.CreateQuickLaunchIcon=Tạo biểu tượng khởi động nhanh
  el.CreateQuickLaunchIcon=Δημιουργία εικονιδίου γρήγορης εκκίνησης
  ro.CreateQuickLaunchIcon=Crează o pictogramă de lansare rapidă
  sv.CreateQuickLaunchIcon=Skapa en snabbstartikon

  en.ProgramOnTheWeb=Program on the web
  it.ProgramOnTheWeb=Programma sul web
  es.ProgramOnTheWeb=Programa en la web
  de.ProgramOnTheWeb=Programm im Web
  fr.ProgramOnTheWeb=Programme sur le web
  pt.ProgramOnTheWeb=Programa na web
  nl.ProgramOnTheWeb=Programma op het web
  ar.ProgramOnTheWeb=البرنامج على الويب
  he.ProgramOnTheWeb=תוכנית באינטרנט
  ru.ProgramOnTheWeb=Программа в интернете
  ja.ProgramOnTheWeb=ウェブ上のプログラム
  zh.ProgramOnTheWeb=网络上的程序
  pl.ProgramOnTheWeb=Program w sieci
  tr.ProgramOnTheWeb=Web'de program
  da.ProgramOnTheWeb=Program på nettet
  no.ProgramOnTheWeb=Program på nettet
  vi.ProgramOnTheWeb=Chương trình trên web
  el.ProgramOnTheWeb=Πρόγραμμα στο διαδίκτυο
  ro.ProgramOnTheWeb=Program pe web
  sv.ProgramOnTheWeb=Program på webben

  en.UninstallProgram=Uninstall ATK-Pro
  it.UninstallProgram=Disinstalla ATK-Pro
  es.UninstallProgram=Desinstalar ATK-Pro
  de.UninstallProgram=ATK-Pro deinstallieren
  fr.UninstallProgram=Désinstaller ATK-Pro
  pt.UninstallProgram=Desinstalar ATK-Pro
  nl.UninstallProgram=ATK-Pro verwijderen
  ar.UninstallProgram=إلغاء تثبيت ATK-Pro
  he.UninstallProgram=הסר את ATK-Pro
  ru.UninstallProgram=Удалить ATK-Pro
  ja.UninstallProgram=ATK-Proをアンインストール
  zh.UninstallProgram=卸载ATK-Pro
  pl.UninstallProgram=Odinstaluj ATK-Pro
  tr.UninstallProgram=ATK-Pro'yu kaldır
  da.UninstallProgram=Afinstaller ATK-Pro
  no.UninstallProgram=Avinstaller ATK-Pro
  vi.UninstallProgram=Gỡ cài đặt ATK-Pro
  el.UninstallProgram=Απεγκατάσταση ATK-Pro
  ro.UninstallProgram=Dezinstalează ATK-Pro
  sv.UninstallProgram=Avinstallera ATK-Pro

  en.LaunchProgram=Launch ATK-Pro
  it.LaunchProgram=Avvia ATK-Pro
  es.LaunchProgram=Iniciar ATK-Pro
  de.LaunchProgram=ATK-Pro starten
  fr.LaunchProgram=Lancer ATK-Pro
  pt.LaunchProgram=Iniciar ATK-Pro
  nl.LaunchProgram=ATK-Pro starten
  ar.LaunchProgram=تشغيل ATK-Pro
  he.LaunchProgram=הפעל את ATK-Pro
  ru.LaunchProgram=Запустить ATK-Pro
  ja.LaunchProgram=ATK-Proを起動
  zh.LaunchProgram=启动ATK-Pro
  pl.LaunchProgram=Uruchom ATK-Pro
  tr.LaunchProgram=ATK-Pro'yu başlat
  da.LaunchProgram=Start ATK-Pro
  no.LaunchProgram=Start ATK-Pro
  vi.LaunchProgram=Khởi động ATK-Pro
  el.LaunchProgram=Εκκίνηση ATK-Pro
  ro.LaunchProgram=Pornește ATK-Pro
  sv.LaunchProgram=Starta ATK-Pro

  en.AssocFileExtension=Associate file extension
  it.AssocFileExtension=Associa estensione file
  es.AssocFileExtension=Asociar extensión de archivo
  de.AssocFileExtension=Dateierweiterung verknüpfen
  fr.AssocFileExtension=Associer l'extension de fichier
  pt.AssocFileExtension=Associar extensão de arquivo
  nl.AssocFileExtension=Bestandsextensie koppelen
  ar.AssocFileExtension=ربط امتداد الملف
  he.AssocFileExtension=קשר סיומת קובץ
  ru.AssocFileExtension=Ассоциировать расширение файла
  ja.AssocFileExtension=ファイル拡張子を関連付ける
  zh.AssocFileExtension=关联文件扩展名
  pl.AssocFileExtension=Skojarz rozszerzenie pliku
  tr.AssocFileExtension=Dosya uzantısını ilişkilendir
  da.AssocFileExtension=Associer filtypen
  no.AssocFileExtension=Associer filtypen
  vi.AssocFileExtension=Liên kết phần mở rộng tệp
  el.AssocFileExtension=Συσχέτιση επέκτασης αρχείου
  ro.AssocFileExtension=Asociați extensia fișierului
  sv.AssocFileExtension=Associera filändelse

  en.AssocingFileExtension=Associating file extension...
  it.AssocingFileExtension=Associazione estensione file...
  es.AssocingFileExtension=Asociando extensión de archivo...
  de.AssocingFileExtension=Dateierweiterung wird verknüpft...
  fr.AssocingFileExtension=Association de l'extension de fichier...
  pt.AssocingFileExtension=Associando extensão de arquivo...
  nl.AssocingFileExtension=Bestandsextensie wordt gekoppeld...
  ar.AssocingFileExtension=جارٍ ربط امتداد الملف...
  he.AssocingFileExtension=מקשר סיומת קובץ...
  ru.AssocingFileExtension=Ассоциация расширения файла...
  ja.AssocingFileExtension=ファイル拡張子を関連付けています...
  zh.AssocingFileExtension=正在关联文件扩展名...
  pl.AssocingFileExtension=Kojarzenie rozszerzenia pliku...
  tr.AssocingFileExtension=Dosya uzantısı ilişkilendiriliyor...
  da.AssocingFileExtension=Associerer filtypen...
  no.AssocingFileExtension=Associerer filtypen...
  vi.AssocingFileExtension=Đang liên kết phần mở rộng tệp...
  el.AssocingFileExtension=Συσχέτιση επέκτασης αρχείου...
  ro.AssocingFileExtension=Se asociază extensia fișierului...
  sv.AssocingFileExtension=Associerar filändelse...

  en.AutoStartProgramGroupDescription=Auto-start program group
  it.AutoStartProgramGroupDescription=Gruppo di avvio automatico
  es.AutoStartProgramGroupDescription=Grupo de inicio automático
  de.AutoStartProgramGroupDescription=Autostart-Programmgruppe
  fr.AutoStartProgramGroupDescription=Groupe de démarrage automatique
  pt.AutoStartProgramGroupDescription=Grupo de inicialização automática
  nl.AutoStartProgramGroupDescription=Automatisch opstarten programmamap
  ar.AutoStartProgramGroupDescription=مجموعة بدء التشغيل التلقائي
  he.AutoStartProgramGroupDescription=קבוצת הפעלה אוטומטית
  ru.AutoStartProgramGroupDescription=Группа автозапуска программ
  ja.AutoStartProgramGroupDescription=自動起動プログラムグループ
  zh.AutoStartProgramGroupDescription=自动启动程序组
  pl.AutoStartProgramGroupDescription=Grupa autostartu programu
  tr.AutoStartProgramGroupDescription=Otomatik başlatma program grubu
  da.AutoStartProgramGroupDescription=Automatisk startprogramgruppe
  no.AutoStartProgramGroupDescription=Automatisk startprogramgruppe
  vi.AutoStartProgramGroupDescription=Nhóm chương trình tự động khởi động
  el.AutoStartProgramGroupDescription=Ομάδα αυτόματης εκκίνησης προγράμματος
  ro.AutoStartProgramGroupDescription=Grup de pornire automată a programului
  sv.AutoStartProgramGroupDescription=Automatisk startprogramgrupp

  en.AutoStartProgram=Auto-start ATK-Pro
  it.AutoStartProgram=Avvio automatico ATK-Pro
  es.AutoStartProgram=Inicio automático ATK-Pro
  de.AutoStartProgram=ATK-Pro automatisch starten
  fr.AutoStartProgram=Démarrage automatique ATK-Pro
  pt.AutoStartProgram=Inicialização automática ATK-Pro
  nl.AutoStartProgram=ATK-Pro automatisch opstarten
  ar.AutoStartProgram=تشغيل ATK-Pro تلقائيًا
  he.AutoStartProgram=הפעלת ATK-Pro אוטומטית
  ru.AutoStartProgram=Автоматический запуск ATK-Pro
  ja.AutoStartProgram=ATK-Proを自動起動
  zh.AutoStartProgram=自动启动ATK-Pro
  pl.AutoStartProgram=Automatyczne uruchamianie ATK-Pro
  tr.AutoStartProgram=ATK-Pro'yu otomatik başlat
  da.AutoStartProgram=Automatisk start af ATK-Pro
  no.AutoStartProgram=Automatisk start av ATK-Pro
  vi.AutoStartProgram=Tự động khởi động ATK-Pro
  el.AutoStartProgram=Αυτόματη εκκίνηση ATK-Pro
  ro.AutoStartProgram=Pornire automată ATK-Pro
  sv.AutoStartProgram=Automatisk start av ATK-Pro

  en.AddonHostProgramNotFound=Addon host program not found
  it.AddonHostProgramNotFound=Programma host addon non trovato
  es.AddonHostProgramNotFound=Programa host de complemento no encontrado
  de.AddonHostProgramNotFound=Addon-Host-Programm nicht gefunden
  fr.AddonHostProgramNotFound=Programme hôte d'extension introuvable
  pt.AddonHostProgramNotFound=Programa host de addon não encontrado
  nl.AddonHostProgramNotFound=Addon-hostprogramma niet gevonden
  ar.AddonHostProgramNotFound=برنامج مضيف الوظيفة الإضافية غير موجود
  he.AddonHostProgramNotFound=תוכנית מארחת תוסף לא נמצאה
  ru.AddonHostProgramNotFound=Программа-хост дополнения не найдена
  ja.AddonHostProgramNotFound=アドオンホストプログラムが見つかりません
  zh.AddonHostProgramNotFound=未找到插件主机程序
  pl.AddonHostProgramNotFound=Nie znaleziono programu hosta dodatku
  tr.AddonHostProgramNotFound=Eklenti ana programı bulunamadı
  da.AddonHostProgramNotFound=Addon-værtsprogram ikke fundet
  no.AddonHostProgramNotFound=Tilleggsvertprogram ikke funnet
  vi.AddonHostProgramNotFound=Không tìm thấy chương trình máy chủ addon
  el.AddonHostProgramNotFound=Δεν βρέθηκε πρόγραμμα υποδοχής προσθέτου
  ro.AddonHostProgramNotFound=Programul gazdă addon nu a fost găsit
  sv.AddonHostProgramNotFound=Addon-värdprogram hittades inte

[Setup]
AppId={{8C7A9D5E-2A1B-3C4D-4E5E-8D3A2B1C4F9E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
PrivilegesRequired=admin
SetupIconFile=assets\common\grafici\ATK-Pro.ico
OutputDir=Output
OutputBaseFilename=ATK-Pro-Setup-v{#MyAppVersion}
ArchitecturesAllowed=x64compatible x86
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage
UsePreviousLanguage=no
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; Lingue supportate con relativi disclaimer

[Languages]

; 20 lingue supportate (autonimi per il menu)
Name: "en"; MessagesFile: "compiler:Default.isl"; LicenseFile: "assets\en\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"; LicenseFile: "assets\it\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"; LicenseFile: "assets\es\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"; LicenseFile: "assets\fr\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"; LicenseFile: "assets\de\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "pt"; MessagesFile: "inno_setup_languages\Portuguese.isl"; LicenseFile: "assets\pt\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"; LicenseFile: "assets\ru\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "ar"; MessagesFile: "compiler:Languages\Arabic.isl"; LicenseFile: "assets\ar\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "nl"; MessagesFile: "compiler:Languages\Dutch.isl"; LicenseFile: "assets\nl\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "he"; MessagesFile: "compiler:Languages\Hebrew.isl"; LicenseFile: "assets\he\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "ja"; MessagesFile: "compiler:Languages\Japanese.isl"; LicenseFile: "assets\ja\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "zh"; MessagesFile: "inno_setup_languages\Chinese.isl"; LicenseFile: "assets\zh\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "pl"; MessagesFile: "compiler:Languages\Polish.isl"; LicenseFile: "assets\pl\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "tr"; MessagesFile: "compiler:Languages\Turkish.isl"; LicenseFile: "assets\tr\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "da"; MessagesFile: "inno_setup_languages\Danish.isl"; LicenseFile: "assets\da\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "no"; MessagesFile: "compiler:Languages\Norwegian.isl"; LicenseFile: "assets\no\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "vi"; MessagesFile: "inno_setup_languages\Vietnamese.isl"; LicenseFile: "assets\vi\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "el"; MessagesFile: "inno_setup_languages\Greek.isl"; LicenseFile: "assets\el\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "ro"; MessagesFile: "inno_setup_languages\Romanian.isl"; LicenseFile: "assets\ro\testuali\disclaimer_legale_ATK-Pro.txt"
Name: "sv"; MessagesFile: "inno_setup_languages\Swedish.isl"; LicenseFile: "assets\sv\testuali\disclaimer_legale_ATK-Pro.txt"



[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked


[Files]
Source: "dist\ATK-Pro\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ATK-Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copia README e CHANGELOG localizzati in base alla lingua selezionata
Source: "assets\en\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: en
Source: "assets\en\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: en
Source: "assets\it\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: it
Source: "assets\it\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: it
Source: "assets\es\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: es
Source: "assets\es\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: es
Source: "assets\fr\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: fr
Source: "assets\fr\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: fr
Source: "assets\de\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: de
Source: "assets\de\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: de
Source: "assets\pt\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: pt
Source: "assets\pt\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: pt
Source: "assets\ru\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: ru
Source: "assets\ru\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: ru
Source: "assets\ar\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: ar
Source: "assets\ar\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: ar
Source: "assets\nl\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: nl
Source: "assets\nl\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: nl
Source: "assets\he\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: he
Source: "assets\he\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: he
Source: "assets\ja\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: ja
Source: "assets\ja\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: ja
Source: "assets\zh\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: zh
Source: "assets\zh\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: zh
Source: "assets\pl\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: pl
Source: "assets\pl\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: pl
Source: "assets\tr\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: tr
Source: "assets\tr\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: tr
Source: "assets\da\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: da
Source: "assets\da\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: da
Source: "assets\no\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: no
Source: "assets\no\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: no
Source: "assets\vi\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: vi
Source: "assets\vi\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: vi
Source: "assets\el\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: el
Source: "assets\el\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: el
Source: "assets\ro\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: ro
Source: "assets\ro\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: ro
Source: "assets\sv\testuali\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion; Languages: sv
Source: "assets\sv\testuali\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.md"; Flags: ignoreversion; Languages: sv

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; Flags: uninsdeletekey
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Language"; ValueData: "{language}"; Flags: uninsdeletevalue
Root: "HKCU"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Language"; ValueData: "{language}"; Flags: uninsdeletevalue

[Code]
// Map Windows UI language IDs to our installer language names
function UILangToInstallerLang(const UILang: Integer): String;
begin
  case UILang of
    $0409: Result := 'en'; // English (United States)
    $0809: Result := 'en'; // English (United Kingdom)
    $0410: Result := 'it'; // Italian
    $0C0A, $040A: Result := 'es'; // Spanish (Modern/Traditional)
    $0407: Result := 'de'; // German
    $040C: Result := 'fr'; // French
    $0816, $0416: Result := 'pt'; // Portuguese (Portugal/Brazil)
    $0413: Result := 'nl'; // Dutch
    $0401: Result := 'ar'; // Arabic
    $040D: Result := 'he'; // Hebrew
    $0419: Result := 'ru'; // Russian
  else
    Result := '';
  end;
end;

var
  DetectedUILang: String;

procedure CurLanguageChanged;
begin
  Log(Format('Language changed to %s', [ActiveLanguage()]));
end;

function InitializeSetup(): Boolean;
begin
  DetectedUILang := UILangToInstallerLang(GetUILanguage);

  if (DetectedUILang <> '') then
    Log(Format('Detected UI language: %s', [DetectedUILang]))
  else
    Log('UI language detection returned no match');

  Result := True;
end;

procedure InitializeWizard;
begin
  Log(Format('Initial active language: %s', [ActiveLanguage()]));

  if (DetectedUILang <> '') and (ActiveLanguage() <> DetectedUILang) then
    Log(Format('Active language differs from detected (%s)', [DetectedUILang]));
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

