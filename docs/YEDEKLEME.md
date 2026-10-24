# OTO YEDEK PARÇA OTOMASYONU - YEDEKLEME VE FELAKET KURTARMA (YEDEKLEME.md)

Bu belge, dükkan verilerinizin asla kaybolmaması için geliştirilen otomatik ve manuel yedekleme mekanizmalarını açıklar.

---

## 1. Otomatik Yedekleme Mekanizması

- **Kapanış Yedeği:** Uygulamayı her kapattığınızda sistem arka planda canlı ve eksiksiz bir veritabanı yedeği alır.
- **Yedek Konumu:** Yedekler `%APPDATA%\OtoYedekParca\backups` dizininde zaman damgasıyla saklanır (Örnek: `yedek_20261024_173000_123456.db`).
- **30 Günlük Otomatik Rotasyon:** Bilgisayarınızın diskini doldurmamak adına en güncel 30 yedek korunur, daha eski yedekler sistem tarafından güvenle silinir.

---

## 2. Harici Diske / USB Belleğe Yedek Alma (Tavsiye Edilir)

Bilgisayarınızın arızalanması, virüs bulaşması veya diskin bozulması riskine karşı haftada en az bir kez yedeklerinizi harici bir USB belleğe almanız önerilir:

1. USB belleğinizi bilgisayara takınız.
2. Sol menüden **"Sistem Ayarları"** -> **"Yedekleme & Geri Yükleme"** sekmesine geliniz.
3. **"📁 Harici Konuma / USB'ye Yedekle"** butonuna tıklayınız.
4. Açılan pencerede USB belleğinizi seçip Tamam'a basınız.
5. Veritabanınızın tam bir kopyası saniyeler içinde USB belleğe kaydedilecektir.

---

## 3. Yedekten Geri Yükleme (Felaket Kurtarma)

Eğer hatalı bir işlem yapıldıysa veya eski bir tarihe dönmek isteniyorsa:

1. Sol menüden **"Sistem Ayarları"** -> **"Yedekleme & Geri Yükleme"** sekmesine geliniz.
2. Tabloda listelenen geçmiş yedeklerden dönmek istediğiniz tarihi seçiniz.
3. **"🔄 Seçilen Yedekten Geri Yükle"** butonuna basınız.
4. **Güvenlik Önlemi:** Sistem, geri yükleme yapmadan hemen önce mevcut veritabanınızın güvenlik yedeğini otomatik olarak alır.
5. Onay verdiğinizde veritabanı seçilen yedeğin durumuna geri döndürülür.

---

## 4. Veritabanı Sağlık Kontrolü

Uygulamanın sağ üst köşesinde yer alan **"🩺 Veritabanı Sağlık Kontrolü"** butonuna basarak veritabanınızın bütünlüğünü (`PRAGMA quick_check`) dilediğiniz zaman test edebilirsiniz. Herhangi bir dosya bozulması tespit edilirse sistem sizi anında uyarır ve son sağlam yedekten geri dönmenizi önerir.
