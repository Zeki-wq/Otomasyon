# OTO YEDEK PARÇA OTOMASYONU - KULLANICI VE KURULUM REHBERİ (KURULUM.md)

Bu rehber, teknik bilgisi olmayan dükkan sahipleri, yedek parçacılar ve tezgahtarlar için hazırlanmıştır. Programın bilgisayarınıza kurulumu, ilk açılışı, güncellenmesi, yedeklenmesi ve kaldırılması adımlarını açıklar.

---

## 1. Sistem Gereksinimleri

- **İşletim Sistemi:** Windows 10 veya Windows 11 (64-bit)
- **Kullanıcı Yetkisi:** Yönetici (Administrator) yetkisi gerektirmez; standart Windows kullanıcı hesabıyla kurulabilir.
- **İnternet Bağlantısı:** Zorunlu DEĞİLDİR (%100 yerel ve çevrimdışı çalışır).
- **Ekran Çözünürlüğü:** En az 1366 x 768 piksel (%100 veya %125 Windows ölçekleme).
- **Depolama:** Kurulum için yaklaşık 150 MB, veri depolama için en az 500 MB boş disk alanı.

---

## 2. Kurulum Adımları (Tek Tıkla Kurulum)

1. Size sağlanan `OtoYedekParca_Setup_v1.0.0.exe` kurulum dosyasına çift tıklayınız.
2. Kurulum ekranında **"İleri"** butonlarına tıklayınız.
3. İsteğe bağlı olarak *"Masaüstü simgesi oluştur"* seçeneğini işaretleyiniz.
4. **"Kur"** butonuna basınız. Kurulum birkaç saniye içinde tamamlanacaktır.
5. Masaüstünüzdeki **"Oto Yedek Parça Otomasyonu"** simgesine çift tıklayarak programı başlatınız.

> [!NOTE]
> Kurulum programı hiçbir ek yazılım (veritabanı sunucusu, Python, sürücü vb.) gerektirmez. Tüm bağımlılıklar paketin içine gömülüdür.

---

## 3. İlk Açılış ve Kurulum Sihirbazı

Program ilk kez kurulduğunda **tamamen boş ve temiz bir veritabanı** ile açılır (içinde hiçbir sahte ürün, müşteri veya deneme satışı bulunmaz). Sizi otomatik olarak **"İlk Kurulum Sihirbazı"** karşılar:

1. **Yönetici Ad Soyad:** Dükkan sahibinin veya ana yöneticinin adı (Örn: *Ahmet Yılmaz*).
2. **Kullanıcı Adı:** Sisteme girişte kullanılacak yönetici kullanıcı adı (Örn: *admin* veya *ahmet*).
3. **Parola ve Parola Tekrarı:** Sisteme güvenle giriş yapmak için en az 4 karakterli parolanızı belirleyiniz.
4. **Dükkan Ünvanı:** Satış fişlerinizin ve ekstrelerinizin üstünde yer alacak dükkan adı (Örn: *Yıldız Oto Yedek Parça*).
5. **İletişim Telefonu ve Adres:** Fişlerde çıkacak dükkan bilgileri.
6. **Varsayılan KDV Oranı:** Parça satışlarında uygulanacak KDV oranı (Varsayılan: %20).
7. **"Yöneticiyi Oluştur ve Başla"** düğmesine basarak sistemi kullanıma hazır hale getiriniz.

---

## 4. Eski Dosyadan İçe Aktarma (İsteğe Bağlı)

Eski sistemden kalma bir veritabanınız (`urunler12.db`) varsa ve eski ürünlerinizi sisteme yüklemek istiyorsanız:
- İlk Kurulum Sihirbazındaki **"📁 Eski Dosyadan İçe Aktar (İsteğe Bağlı)"** düğmesine tıklayınız.
- Açılan pencereden bilgisayarınızdaki eski veritabanı dosyasını seçiniz.
- Sistem ürünlerinizi, stoklarınızı ve eski siparişlerinizi kayıpsız olarak içe aktaracaktır.
- *Not: Hiçbir eski dosya sisteme otomatik yüklenmez; yalnızca siz seçerseniz aktarılır.*

---

## 5. Programı Güncelleme (Yeni Sürüm Yükleme)

Yeni bir program güncellemesi yayınlandığında:
1. Mevcut programınızı **kaldırmanıza gerek yoktur**.
2. Yeni sürüm kurulum dosyasını (`OtoYedekParca_Setup_vX.X.X.exe`) doğrudan çalıştırıp aynı adımlarla üzerine kurunuz.
3. **VERİLERİNİZ SİLİNMEZ:** Kurulum programı mevcut veritabanınıza, ürünlerinize ve satışlarınıza kesinlikle dokunmaz.
4. Yeni sürüm ilk kez açıldığında, şema güncellemesi gerekiyorsa sistem **önce otomatik bir güvenlik yedeği alır**, ardından verilerinizi yeni sürüme güvenle yükseltir.

---

## 6. Veriler Bilgisayarda Nerede Saklanır?

Tüm ticari bilgileriniz Windows işletim sisteminizin korumalı kullanıcı veri alanında saklanır:
- **Ana Klasör:** `%APPDATA%\OtoYedekParca` (Windows Dosya Gezgini adres çubuğuna yapıştırıp Enter'a basabilirsiniz).
- **Veritabanı Dosyası:** `otoyedekparca.db`
- **Otomatik Yedekler:** `%APPDATA%\OtoYedekParca\backups`
- **Sistem Günlükleri (Loglar):** `%APPDATA%\OtoYedekParca\logs`
- **Dışa Aktarılan Fiş ve Belgeler:** `%APPDATA%\OtoYedekParca\exports`

> [!IMPORTANT]
> Verileriniz `Program Files` içine yazılmaz. Bu sayede Windows güncellemelerinde veya program kaldırıp yüklemelerinde verileriniz güvende kalır.

---

## 7. Yedekleme ve Yedekten Geri Yükleme

Dükkan verilerinizin güvenliği için düzenli yedek alınması tavsiye edilir:
- **Otomatik Kapanış Yedeği:** Program her kapatıldığında otomatik olarak arka planda güncel bir yedek dosyası oluşturur.
- **Manuel Yedek Al:** *Sistem Ayarları* -> *Yedekleme & Geri Yükleme* sekmesinden **"💾 Şimdi Yedek Al"** düğmesine basabilirsiniz.
- **USB Belleğe / Harici Diske Yedekle:** Aynı sekmeden **"📁 Harici Konuma / USB'ye Yedekle"** düğmesine basarak takılı USB belleğinizi seçip tam bir kopya alabilirsiniz.
- **Yedekten Geri Yükleme:** Bilgisayar arızası veya yanlış işlem sonrasında, listeden dilediğiniz tarihli yedeği seçip **"🔄 Seçilen Yedekten Geri Yükle"** düğmesine basarak sistemi o ana döndürebilirsiniz. (İşlem öncesinde mevcut durumun otomatik güvenlik yedeği alınır).

---

## 8. Fabrika Ayarlarına Dönüş (Tüm Verileri Sıfırlama)

Yalnızca dükkan sahibi (**Yönetici**) rolü için geçerli olan acil sıfırlama seçeneğidir:
1. *Sistem Ayarları* -> *Yedekleme & Geri Yükleme* sekmesinin altındaki **"⚠️ Fabrika Ayarlarına Dön (Tüm Verileri Sil)"** butonuna tıklayınız.
2. Açılan güvenlik penceresinde:
   - Yönetici parolanızı giriniz.
   - Onay kutusuna büyük harflerle **SIFIRLA** yazınız.
3. Parola veya onay kelimesi hatalıysa **hiçbir veri silinmez**.
4. Bilgiler doğruysa sistem:
   - Önce mevcut tüm veritabanının **otomatik tam güvenlik yedeğini** alır.
   - Denetim kaydına işlemi işler.
   - Tüm ürün, sipariş ve müşteri verilerini temizler.
   - Sizi yeniden temiz **İlk Kurulum Sihirbazı** ekranına yönlendirir.

---

## 9. Uygulamayı Kaldırma (Uninstall)

Programı bilgisayarınızdan kaldırmak isterseniz:
1. Windows *Ayarlar* -> *Uygulamalar* -> *Yüklü Uygulamalar* bölümünden veya Denetim Masası'ndan **"Oto Yedek Parça Otomasyonu"** programını seçip **"Kaldır"** butonuna basınız.
2. Kaldırma sihirbazı program dosyalarını ve masaüstü kısayollarını temizler.
3. Ardından size şu soruyu yöneltir:
   > *"Dükkan veritabanı, sipariş geçmişi ve yedekleriniz şu konumda korunmaktadır: (%APPDATA%\OtoYedekParca). Bu veritabanını ve tüm yedekleri kalıcı olarak silmek istiyor musunuz?"*
4. **Varsayılan seçenek HAYIR'dır.** Hayır'ı seçerseniz tüm geçmiş dükkan kayıtlarınız korunur; böylece ileride programı tekrar kurduğunuzda verileriniz aynen geri gelir. Yalnızca bilgisayarı başkasına devrederken veya tamamen temizlemek istediğinizde **Evet** seçeneğini kullanınız.
5. Sessiz modda (`/SILENT` veya `/VERYSILENT`) yapılan kaldırma işlemlerinde kullanıcı verileri **ASLA silinmez**.
