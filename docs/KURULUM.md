# OTO YEDEK PARÇA OTOMASYONU - KURULUM REHBERİ (KURULUM.md)

Bu rehber, teknik bilgisi olmayan dükkan sahipleri ve çalışanları için hazırlanmıştır. Bilgisayarınıza programı kurmak ve kullanmaya başlamak için aşağıdaki adımları sırasıyla uygulayınız.

---

## 1. Sistem Gereksinimleri

- **İşletim Sistemi:** Windows 10 veya Windows 11 (64-bit)
- **İnternet Bağlantısı:** Zorunlu DEĞİLDİR (%100 çevrimdışı / internetsiz çalışır)
- **Ekran Çözünürlüğü:** En az 1366 x 768 piksel
- **Depolama:** En az 200 MB boş disk alanı

---

## 2. Kurulum Adımları (Tek Tıkla Kurulum)

1. Size iletilen `OtoYedekParca_Kurulum_v1.0.0.exe` kurulum dosyasını çift tıklayarak açınız.
2. Kurulum sihirbazındaki **"İleri"** butonlarına tıklayınız.
3. Masaüstüne kısayol oluşturma kutucuğunu işaretli bırakınız.
4. **"Kur"** butonuna basarak kurulumu tamamlayınız.
5. Masaüstünüzde beliren **"Oto Yedek Parça Otomasyonu"** simgesine çift tıklayarak uygulamayı başlatınız.

---

## 3. İlk Çalıştırma ve Yönetici Hesabı Oluşturma

Uygulama ilk kez açıldığında sizi **"İlk Kurulum Sihirbazı"** karşılar:

1. **Ad Soyad:** Kendi adınızı veya firma ünvanınızı yazınız (Örn: *Ahmet Yılmaz*).
2. **Kullanıcı Adı:** Sisteme girerken kullanacağınız kullanıcı adını belirleyiniz (Örn: *ahmet* veya *admin*).
3. **Parola:** Dükkanınızın güvenliği için unutmayacağınız bir şifre giriniz ve tekrar kutusuna aynı şifreyi yazınız.
4. **"Yöneticiyi Oluştur ve Başla"** butonuna basınız.

> [!TIP]
> Program açıldığında dükkan adı, telefon ve adres bilgilerinizi sol menüdeki **"Sistem Ayarları"** sekmesinden güncelleyebilirsiniz.

---

## 4. Eski Dükkan Verilerinin Otomatik Taşınması

Eğer eski sistemdeki `urunler12.db` dosyanız mevcutsa, program ilk açılışta bu dosyayı otomatik olarak tespit eder ve:
- Tüm eski ürünlerinizi parça kodlarıyla birlikte yeni sisteme aktarır.
- Eski siparişlerinizi ve stok açılış hareketlerini kayıpsız olarak veritabanına ekler.
- Hiçbir eski bilginiz kaybolmaz.

---

## 5. Uygulamayı Kaldırma (Uninstall)

Uygulamayı Denetim Masası'ndan kaldırmak istediğinizde sistem size şunu soracaktır:
> *"Dükkan veritabanı, sipariş geçmişi ve yedeklerinizi silmek istiyor musunuz?"*

- Eğer bilgisayarı formatlayacaksanız veya uygulamayı yeniden kuracaksanız **HAYIR** seçeneğini seçiniz; böylece dükkanınızın geçmiş verileri ve yedekleri `%APPDATA%\OtoYedekParca` klasöründe güvenle korunacaktır.
