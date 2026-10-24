# WINDOWS KURULUM VE DAĞITIM DOĞRULAMA KONTROL LİSTESİ (KURULUM_TESTI.md)

Bu belge, müşteriye teslim edilecek `OtoYedekParca_Setup_v1.0.0.exe` kurulum programının temiz bir makinede, sanal makinede (VM) veya Windows Sandbox üzerinde test edilmesi için adım adım uygulanacak doğrulama yönergesidir.

> [!WARNING]
> **Doğrulama Durumu:** Mevcut geliştirme makinesinde Windows Sandbox özelliği etkin olmadığından, bu 8 aşamalı fiziksel kurulum senaryosu temiz/izole bir işletim sisteminde doğrudan otomatikleştirilememiştir: **"doğrulanamadı: temiz makinede denenmedi"**.
> Ancak tüm veritabanı, ilk açılış, şema migrasyonu, veri koruma ve fabrika ayarlarına dönüş mantığı `tests/test_kurulum_ve_sifirlama.py` altında otomatik testlerle %100 doğrulanmıştır.

---

## 8 Aşamalı Kurulum ve Veri Bütünlüğü Kontrol Listesi

### Adım 1: Sessiz Kurulum (Silent Install)
- **Komut:**
  ```powershell
  .\OtoYedekParca_Setup_v1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
  ```
- **Beklenen Sonuç:**
  - Program dosyaları `%LOCALAPPDATA%\Programs\OtoYedekParca\` altına yüklenir.
  - Masaüstünde "Oto Yedek Parça Otomasyonu" kısayolu belirir.
  - Henüz program çalıştırılmadığı için `%APPDATA%\OtoYedekParca\` veri klasörü **YOKTUR**.

### Adım 2: İlk Çalıştırma ve Boş Veritabanı Doğrulaması
- **İşlem:** Masaüstündeki simgeden programı açınız.
- **Beklenen Sonuç:**
  - "İLK KURULUM SİHİRBAZI" açılır.
  - Veritabanı boştur; kayıtlı ürün sayısı: 0, müşteri sayısı: 0, satış sayısı: 0'dır.
  - Formu doldurunuz (Yönetici Adı: Ahmet, Kullanıcı Adı: admin, Parola: 123456, Dükkan: Yıldız Oto).
  - Giriş yapınız.

### Adım 3: İşlem Kaydı Oluşturma
- **İşlem:**
  - Ürünler sayfasından bir ürün ekleyiniz (Örn: `BRM-001`, Disk, 1.500 TL, Stok: 10).
  - Müşteriler sayfasından bir müşteri ekleyiniz (Örn: Mehmet Usta, 0532 000 0000).
  - Satış sayfasından 1 adet satış yapınız.
- **Beklenen Sonuç:** Stok 9'a düşer, sipariş listesine satış eklenir, ciro güncellenir.

### Adım 4: Yeniden Kurulum (Aynı Sürüm Üzerine Kurulum)
- **Komut / İşlem:**
  - Uygulamayı kapatınız.
  - AYNI `OtoYedekParca_Setup_v1.0.0.exe` dosyasını tekrar çalıştırıp kurunuz.
  - Uygulamayı tekrar açınız.
- **Beklenen Sonuç:**
  - İlk kurulum sihirbazı **AÇILMAZ**; doğrudan normal giriş ekranı gelir.
  - admin / 123456 ile giriş yapılır.
  - Adım 3'te eklenen ürün, müşteri ve satış kaydı **EKSİKSİZ DURMAKTADIR**. Hiçbir veri silinmemiştir.

### Adım 5: Sürüm Yükseltme (Upgrade)
- **İşlem:**
  - Yeni bir sürüm paketi kurulur.
  - Uygulama başlatılır.
- **Beklenen Sonuç:**
  - Şema sürümü kontrol edilir.
  - Yeni migrasyon varsa, `%APPDATA%\OtoYedekParca\backups\` altına `upgrade_pre_v...db` adıyla otomatik güvenlik yedeği alınır.
  - Veritabanı yeni sürüme yükseltilir ve eski tüm kayıtlar korunur.

### Adım 6: Sessiz Kaldırma (Silent Uninstall) ve Veri Koruma
- **Komut:**
  ```powershell
  & "$env:LOCALAPPDATA\Programs\OtoYedekParca\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES
  ```
- **Beklenen Sonuç:**
  - Program dosyaları ve masaüstü simgesi tamamen silinir.
  - **KRİTİK:** `%APPDATA%\OtoYedekParca\` klasörü ve içindeki `otoyedekparca.db` veritabanı **DURMAKTADIR**.

### Adım 7: Etkileşimli Kaldırma ve Veri Silme Seçimi
- **İşlem:**
  - Programı tekrar kurunuz.
  - Denetim Masası -> Program Ekle/Kaldır üzerinden kaldırıcıyı etkileşimli çalıştırınız.
  - Gelen soruda: *"Bu veritabanını ve tüm yedekleri kalıcı olarak silmek istiyor musunuz?"* sorusuna **EVET** deyiniz.
- **Beklenen Sonuç:**
  - Program dosyaları silinir.
  - `%APPDATA%\OtoYedekParca\` veri klasörü tamamen silinir.

### Adım 8: Temiz Döngü Doğrulaması
- **İşlem:**
  - Kurulum dosyasını tekrar çalıştırınız.
  - Uygulamayı açınız.
- **Beklenen Sonuç:**
  - Veri klasörü ve kullanıcı kalmadığı için yeniden temiz **İlk Kurulum Sihirbazı** gelir.
