# MİMARİ VE TASARIM KARARLARI (KARARLAR.md)

Bu belge, Oto Yedek Parça Otomasyonu projesinde alınan teknik, mimari ve iş alanı kararlarını ve gerekçelerini belgeler.

---

## 1. Hedef ve Varsayılan Dükkan Profili

- **Donanım ve Ortam:** Tek Windows 10/11 PC, internet bağlantısı zorunluluğu olmadan (%100 offline) çalışır.
- **Kullanıcı Sayısı:** 1 ila 3 kullanıcı (dükkan sahibi / yönetici ve tezgahtarlar / personel).
- **Ürün Kapasitesi:** 5.000 ila 50.000 aktif ürün kalemi.
- **Temel İş Akışı:**
  1. Hızlı parça arama (kod, ad, marka, barkod, OEM)
  2. Fiyat ve stok görme
  3. Müşteriye anında satış veya sipariş oluşturma (sepet / çoklu kalem)
  4. Tek işlemde (atomik transaction) stok düşümü ve hareket kaydı
  5. Gün sonu kasa / ciro / stok raporları alma
  6. Otomatik ve elle veri yedekleme
- **Kullanıcı Seviyesi:** Teknik bilgisi olmayan dükkan sahipleri ve personeller için sezgisel, klavye dostu ve hataya yer bırakmayan arayüz.

---

## 2. Mimari Kararlar ve İlkeler

### K1: Dizin Yapısı ve Modülerlik
- `app/` altında temiz katmanlı mimari:
  - `db/`: Veritabanı bağlantı havuzu (SQLite WAL), sıralı SQL migrasyonları, `legacy_import.py`.
  - `domain/`: Veri modelleri (dataclass), `money.py` (kuruş <-> TL çevrimi, KDV hesaplamaları).
  - `services/`: İş mantığı servisleri (`urun_servisi.py`, `satis_servisi.py`, `stok_servisi.py`, `musteri_servisi.py`, `kimlik_servisi.py`, `yedek_servisi.py`, `rapor_servisi.py`). **Servisler Qt veya UI bileşenlerine kesinlikle bağımlı değildir.**
  - `ui/`: Tek `QApplication`, modern koyu tema (`theme.py`), tek ana pencere (`main_window.py`) ve sayfalar (`pages/`).
  - `utils/`: Loglama (`logging.py`), Excel/PDF dışa aktarım (`export.py`).
- **Gerekçe:** UI ile iş mantığının ve SQL'in ayrılması, test edilebilirliği sağlar ve Qt olmadan tüm iş kurallarının bağımsız test edilmesini mümkün kılar.

### K2: Veri Saklama ve Parasal İşlemler
- Bütün para değerleri veritabanında ve bellek içinde `INTEGER` olarak **kuruş** cinsinden tutulur (Örnek: 150,50 ₺ -> `15050`).
- Yuvarlama işlemlerinde Python `decimal` modülü (`ROUND_HALF_UP`) kullanılır. KDV hesaplaması tek bir merkezi modülden (`app/domain/money.py`) yürütülür.
- **Gerekçe:** Kayan noktalı (float) aritmetiğinde meydana gelen kuruş kayıplarını ve tutarsızlıkları tamamen önler.

### K3: Veri Klasörü ve Yollar
- Uygulama veritabanı, loglar ve otomatik yedekler `%APPDATA%\OtoYedekParca` altında saklanır.
- **Gerekçe:** Windows işletim sisteminde `Program Files` altına yazma izinleri kısıtlıdır. `%APPDATA%` kullanıcının yazma yetkisine sahip olduğu, Windows yedekleme standartlarına uyan dizindir.

### K4: Veritabanı Motoru ve Dayanıklılık
- SQLite motoru `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`, `PRAGMA busy_timeout = 5000` ve `PRAGMA synchronous = NORMAL` ayarlarıyla çalıştırılır.
- Tablolarda negatif stok oluşmaması için `CHECK(stok >= 0)` kısıtı uygulanır.
- Her yazma işlemi tek bir transaction (`with conn:`) içinde yürütülür; hata anında tam rollback yapılır.
- Şema versiyonlaması `PRAGMA user_version` ve sıralı `.sql` migrasyon dosyaları ile takip edilir.

### K5: Bağımlılık Politikası
- Ağır kütüphaneler (pandas, ORM'ler, büyük frameworkler) eklenmemiştir.
- Eklenen hafif bağımlılıklar:
  - `openpyxl`: Excel (.xlsx) ürün içe/dışa aktarımı için.
  - `reportlab`: Satış/sipariş bilgi fişleri ve rapor PDF çıktısı için.
  - `pytest` & `pytest-qt`: Otomasyonlu birim ve arayüz testleri için.
  - `ruff`: Kod kalitesi ve linter denetimi için.
  - `pyinstaller`: Windows tek tıkla çalıştırılabilir paket üretimi için.

### K6: Kimlik Doğrulama ve Güvenlik
- Şifreler `hashlib.pbkdf2_hmac` ('sha256', 100.000 iterasyon) ve rastgele 16 baytlık `salt` ile hash'lenir. Açık parola asla saklanmaz.
- Varsayılan / sabit şifre yoktur. İlk kurulumda yönetici oluşturma sihirbazı çalışır.
- Kişisel veriler (KVKK gereği) yalnızca yerel makinede saklanır, loglara maskelenmeden yazılmaz.

### K7: Eski Verinin Korunması (`legacy_import.py`)
- Orijinal `urunler12.db` dosyasındaki 2 ürün ve 17 sipariş satırı yeni ilişkisel şemaya kayıpsız aktarılır.
- Eşleşmeyen sipariş ürünleri "silinmiş/tanımsız ürün" olarak ad ve fiyat kopyasıyla korunur.
- İçe aktarma işlemi idempotent'tir (birden fazla çalıştırıldığında mükerrer kayıt üretmez).
