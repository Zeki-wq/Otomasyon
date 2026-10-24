# Mimari ve Tasarım Kararları Kaydı (KARARLAR.md)

Bu belge, Oto Yedek Parça Otomasyonu projesinde alınan temel mimari, veri saklama, kurulum ve güvenlik kararlarını ve bunların gerekçelerini kayıt altına alır.

---

## 1. Veri Depolama Konumu Kararı

### **Karar: `%APPDATA%\OtoYedekParca`**
Uygulama veritabanı (`otoyedekparca.db`), otomatik yedekler (`backups/`), log dosyaları (`logs/`) ve dışa aktarılan raporlar (`exports/`), Windows ortamında **`%APPDATA%\OtoYedekParca`** (Roaming Application Data) altında saklanır.

### **Gerekçeler ve Karşılaştırma:**

1. **Neden `Program Files` Altına Yazılmıyor?**
   - Windows Vista ve sonrasında gelen UAC (Kullanıcı Hesabı Denetimi) gereği `C:\Program Files` ve `C:\Program Files (x86)` dizinleri salt okunurdur.
   - Bu klasörlere çalışma zamanında SQLite veritabanı yazmaya çalışmak `PermissionError: [Errno 13] Permission denied` hatasına ve veri bozulmasına neden olur.

2. **Neden `%ProgramData%` Yerine `%APPDATA%` Tercih Edildi?**
   - `%ProgramData%` ortak makine seviyesinde bir dizindir; ancak alt klasör oluşturma ve ACL izinleri genellikle yönetici (Administrator) yetkisi gerektirir.
   - Oto sanayi ve yedek parça dükkanlarında kasadaki bilgisayarlar çoğunlukla tek bir Windows oturumu üzerinden kullanılır.
   - `%APPDATA%`, standart (yönetici olmayan) Windows kullanıcı hesaplarının hiçbir UAC engeline takılmadan okuma/yazma yapabilmesini sağlar.
   - Windows yedekleme, kullanıcı profili aktarımı ve bulut eşitleme araçları `%APPDATA%` yapısını doğrudan tanır ve korur.

3. **Merkezi Yönetim:**
   - Dizin yolları uygulama genelinde kesinlikle dağınık yazılmaz; yalnızca [app/config.py](file:///c:/Users/Zeki/OneDrive/Masa%C3%BCst%C3%BC/Otomasyon/app/config.py) içindeki `DATA_DIR`, `DEFAULT_DB_PATH`, `BACKUP_DIR`, `LOG_DIR` sabitleri üzerinden tek merkezden yönetilir.

---

## 2. Kurulum Yetki Seviyesi (`PrivilegesRequired=lowest`)

### **Karar:**
Inno Setup yapılandırmasında (`packaging/setup.iss`), `PrivilegesRequired=lowest` direktifi seçilmiştir.

### **Gerekçeler:**
- Dükkan sahipleri veya tezgahtarlar, dükkandaki bilgisayarda yönetici parolasına sahip olmayabilir veya UAC uyarılarından çekinebilir.
- `PrivilegesRequired=lowest` sayesinde kurulum programı `{autopf}\OtoYedekParca` (kullanıcı bazlı program dizini: `%LOCALAPPDATA%\Programs\OtoYedekParca`) altına yüklenir.
- Kullanıcı hiçbir yönetici şifresi girmeden tek tıkla yazılımı kurabilir ve güncelleyebilir.
- Veri dizini (`%APPDATA%`) ile kurulum dizini tam uyum içinde çalışır.

---

## 3. Temiz Veritabanı ve Sıfır Geliştirici Verisi İlkesi

### **Karar:**
Dağıtıma çıkan kurulum paketlerine (`dist/OtoYedekParca` ve `setup.exe`) kesinlikle hiçbir `.db`, `.sqlite`, `.log`, yedek dosyası veya geliştirici ortamında kullanılan `legacy/urunler12.db` dosyası dahil edilmez.

### **Gerekçeler:**
- Her müşteri kurulum yaptığında temiz, sıfır ürünlü, sıfır müşterili ve sıfır siparişli bir şema ile başlar.
- Geliştirici ortamındaki test verilerinin (sahte müşteriler, test satışları, geliştirici şifreleri) müşteriye gitmesi KVKK ve ticari itibar açısından kritik bir ihlaldir.
- Eski veritabanından veri aktarmak isteyen müşteriler, İlk Kurulum Sihirbazı veya Ayarlar ekranından "Eski Dosyadan İçe Aktar" düğmesine basarak kendi dosyalarını seçmelidir; otomatik aktarım kesinlikle yapılmaz.

---

## 4. Güncelleme ve Veri Koruma Garantisi

### **Karar:**
Programın yeniden kurulması veya yeni bir sürüm kurulumu mevcut veritabanını hiçbir koşulda silmez, ezmez veya sıfırlamaz.

### **Gerekçeler:**
- Inno Setup `[Files]` yönergesinde kullanıcı verileri yer almaz; yalnızca program dosyaları güncellenir.
- Veritabanı şema sürümü eski ise, uygulama ilk açılışta `run_migrations` fonksiyonu ile:
  1. Önce otomatik güvenlik yedeği alır (`upgrade_pre_v...db`).
  2. Bekleyen migrasyonları sırayla uygular.
  3. Bir hata oluşursa, otomatik güvenlik yedeğini geri yükleyerek veriyi korur.

---

## 5. Kaldırma (Uninstaller) Güvenlik Politikası

### **Karar:**
Yazılım Denetim Masasından kaldırıldığında:
1. Sessiz kaldırmada (`/SILENT` veya `/VERYSILENT`): Kullanıcı veritabanı ve yedekleri **ASLA SİLİNMEZ**.
2. Etkileşimli kaldırmada: Kullanıcıya açık bir onay kutusu sorulur. Varsayılan düğme **HAYIR** (`MB_DEFBUTTON2`) olarak ayarlanmıştır.

### **Gerekçeler:**
- Kullanıcılar programı geçici olarak kaldırıp yeniden yükleyebilir veya yanlışlıkla kaldırıcıyı çalıştırabilir. Müşterinin ticari hafızası (yıllık cirosu, alacakları, stokları) korunmalıdır.

---

## 6. Fabrika Ayarlarına Sıfırlama Koruması

### **Karar:**
Program içinden fabrika ayarlarına dönüş yalnızca **Yönetici** rolüne açıktır ve çift aşamalı doğrulama (Yönetici parolası + "SIFIRLA" kelimesi) zorunludur.

### **Gerekçeler:**
- Tezgahtar / personel rolündeki kullanıcıların dükkan verisini silememesi gerekir.
- Yanlışlıkla tıklama veya yanlış parola durumunda sıfırlama işlemi derhal durdurulur ve hiçbir veriye dokunulmaz.
- Sıfırlama yapılmadan önce otomatik tam yedek alınır ve `denetim_log` tablosuna işlem kaydı düşülür.
