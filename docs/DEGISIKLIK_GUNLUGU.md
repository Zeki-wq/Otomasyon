# DEĞİŞİKLİK GÜNLÜĞÜ (CHANGELOG)

Tüm sürüm değişiklikleri [Semantic Versioning](https://semver.org/lang/tr/) standardına uygundur.

---

## [1.0.0] - 2026-10-24

### Eklendi (Yeni Özellikler)
- **Tek MainWindow Mimarisi:** Kenar çubuğu gezintili tek pencere yapısı (`QStackedWidget`). 3 ayrı pencere açma mantığı kaldırıldı.
- **Güvenli Kimlik Doğrulama:** PBKDF2-HMAC-SHA256 ve 16 bayt salt ile şifrelenmiş kullanıcı yönetimi (`yonetici` ve `personel` rolleri).
- **İlk Kurulum Sihirbazı:** Sisteme ilk açılışta yönetici hesabı ve dükkan bilgisi oluşturma ekranı.
- **Çok Kalemli Sepet & Satış:** Barkod okuyucu destekli, anlık stok kontrollü ve tek transaction içinde çalışan hızlı satış ekranı.
- **Sipariş İptal & İade:** İptal edilen siparişlerin stoklarını depoya otomatik ve eksiksiz iade eden mekanizma.
- **Cari Hesap & Veresiye Takibi:** Müşteri veresiye bakiyesi, tahsilat girişi ve detaylı müşteri hesap ekstresi.
- **Stok Defteri & Kritik Stok:** Tüm stok değişimlerinin kayıt altına alındığı denetim defteri ve kritik stok seviyesi görsel rozetleri.
- **Otomatik & Manuel Yedekleme:** SQLite Online Backup API ile uygulama kapanışında otomatik yedekleme ve harici USB sürücüye yedek alma seçeneği.
- **Excel Toplu Veri Yönetimi:** 5.000+ satırlık ürünlerin hata raporuyla içeri aktarılması ve tüm envanterin Excel'e aktarılması.
- **Satış Bilgi Fişi (PDF):** ReportLab ile "Bilgi fişidir, mali değeri yoktur" yasal ibareli fiş çıktısı.
- **High-DPI & Responsive Yerleşim:** Mutlak koordinatlar (`setGeometry`) kaldırılarak `QLayout` tabanlı responsive arayüz sağlandı.
- **Windows Kurulum Paketi:** PyInstaller ve Inno Setup kurulum betikleri hazırlandı.

### Düzeltilen Doğrulanmış Hatalar (B1 - B8)
- **B1 Çözüldü:** `siparisal2.urunadi` UNIQUE kısıtından kaynaklanan çökme düzeltildi; sipariş başlığı ve kalemleri ayrıldı. Aynı ürüne sınırsız sipariş verilebiliyor.
- **B2 Çözüldü:** İsimle stok düşümü (`WHERE urunAdi = ?`) kaldırıldı; tüm stok hareketleri ve sipariş kalemleri benzersiz `urun_id` üzerinden atomik olarak düşülüyor.
- **B3 Çözüldü:** Sabit `setRowCount(30)` sınırı ve 31. üründen sonrasının yok sayılması engellendi; dinamik satır ekleme ve sayfalama altyapısı kuruldu. Tablo başlık ve sütun kaymaları giderildi.
- **B4 Çözüldü:** `pyton1.py` import anındaki `QApplication` çağrısı ve iç içe event loop açılması giderildi; tek giriş noktası (`app/main.py`) ve tek `QApplication` örneğine geçildi.
- **B5 Çözüldü:** `kayit_ekle` içindeki yanlış filtre kutusu okuması düzeltildi; girdi doğrulama eklendi ve harfli girişlerde çökme engellendi.
- **B6 Çözüldü:** Güncelleme sorgusundaki Türkçe karakter `urunAciklaması` hatası düzeltildi; `kayit_sil`'deki seçim olmadan tıklamada oluşan `IndexError` güvenli hale getirildi.
- **B7 Çözüldü:** Kategori listelemedeki `indexSutun+1` sütun kayması ve tam eşleşmeli yetersiz arama düzeltildi; 50.000 üründe < 100 ms kısmi arama sağlandı.
- **B8 Çözüldü:** `foreign key mismatch` hatası giderildi; normalleştirilmiş ilişkisel şemaya geçilerek `PRAGMA foreign_keys = ON` eksiksiz sağlandı.
