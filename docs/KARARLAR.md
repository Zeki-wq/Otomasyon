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

### K8: Arayüz Tipografisi, Boyutlandırma ve Kırpılma Önleme Politikası
- **Metin Kırpılma Kök Nedeni:** Segoe UI 10pt font yüksekliği 23px (`ascent: 18px`, `descent: 5px`) olup, giriş bileşenlerine verilen aşırı padding (7px 12px) veya pencerelere verilen `setFixedSize` kısıtları kutuları 24-33px aralığına sıkıştırarak metinlerin alt ve üst yarılarının kesilmesine yol açıyordu.
- **Merkezi Çözüm (`theme.py`):**
  - Tüm giriş kutuları (`QLineEdit`, `QComboBox`, `QSpinBox`, `QDoubleSpinBox`, `QDateEdit`) ve `QPushButton` için `min-height: 26px`, dikey `padding: 3px` olarak standardize edildi.
  - Bileşenlere sabit yükseklik (`setFixedHeight`) verilmesi terk edildi; yükseklik içerik ve layout `sizeHint` değerinden türetilir.
  - QSpinBox/QDateEdit içindeki alt `QLineEdit` bileşeninin çerçevesi ve arka planı sıfırlanarak (`padding: 0px 4px; border: none; background: transparent;`) çift padding ve kutu içi sıkışma giderildi.
- **Pencere ve Diyalog Boyutları:**
  - `setFixedSize` yerine `setMinimumSize` ve `resize` kullanılarak işletim sistemi ve DPI ölçeklemelerine (100%, 125%, 150%) uyum sağlandı.
  - Tüm QDialog pencerelerinde Windows'un işlevsiz `?` (Context Help) butonu `Qt.WindowContextHelpButtonHint` kaldırılarak temizlendi.
- **Tablo Başlıkları:**
  - `QHeaderView.ResizeToContents` yerine sütunlara orantılı sabit/etkileşimli genişlikler ve `min-height: 26px; padding: 6px;` verilerek başlık metinlerinin ("Ürün Adı", "Durum" vb.) kırpılması önlendi.
- **Otomasyonlu Denetim:** `tests/test_ui_no_clipping.py` testi ile her sayfa ve diyalog açıldığında tüm giriş ve buton bileşenlerinin `height >= sizeHint().height() - 1` ve font advance genişlik kuralları denetlenir.

### K9: Pasif Ürünler ve Durum Yönetimi
- **Aktif/Pasif Filtreleme:** Ürünler sayfasında `Aktif / Pasif / Tümü` filtresi sunulur. Pasif ürünler soluk gri (`#718093`) ve `⛔ Pasif` rozetiyle gösterilir.
- **Aktife Alma Yetkisi:** Yalnızca yönetici rolündeki kullanıcılar pasif ürünü seçtiğinde "♻️ Aktife Al" butonu görünür.
- **Satış Ekranı İzolasyonu:** Satış ekranındaki ürün aramalarında `aktif = 1` filtresi zorunlu tutularak pasif ürünlerin yeni sepetlere eklenmesi engellenir.
- **Denetim İzi:** Pasife ve aktife alma işlemleri `denetim_log` tablosuna (`urun_pasife_al` / `urun_aktife_al`) ve `stok_hareket` defterine (`hareket_tipi = 'sayim_duzeltme'`, `referans_tipi = 'urun_durum'`, kullanıcı id ve zaman damgasıyla) yazılır.

### K10: Sepet Hesaplamaları ve Kuruş Hassasiyeti
- **Merkezi Servis Fonksiyonu:** Sepet matrah, KDV ve genel toplam hesabı UI katmanına bırakılmamış, `satis_servisi.sepet_hesapla()` fonksiyonunda tamsayı kuruş hassasiyetinde toplanmıştır.
- **Reaktif Arayüz ve Koruma:** Sepet tablosunda adet artırıldığında (`QSpinBox` veya tablo hücresi) satır tutarı ve alt toplam kartları anında güncellenir. Sinyal döngülerini engellemek için `_guncelleniyor` kalkanı (recursion guard) uygulanır.
- **Stok Denetimi:** Sepetteki adet mevcut stoku aştığında işlem reddedilir, kullanıcıya mevcut stok uyarısı verilir ve adet mevcut stoka çekilir. Adet 0'a çekilirse satır sepetten otomatik silinir.

### K11: Sipariş Geçmişi, Kalem Sayısı ve Detaydan İptal
- **Sipariş Kalem & Adet Sayıları:** `siparis` tablosuna SQL alt sorgularıyla hesaplanan `kalem_sayisi` ve `toplam_adet` alanları eklenmiş, sipariş listesinde ve modelinde gösterilmiştir.
- **Ürün Arama Filtresi:** Sipariş listesinde siparişin herhangi bir kaleminde geçen parça kodu veya ürün adına göre filtreleme (`EXISTS`) eklenmiştir.
- **Detaydan İade/İptal:** Çift tıklanan siparişin detay penceresinde tüm kalemler (adet, birim fiyat, satır toplamı, KDV) listelenir ve yönetici yetkisiyle doğrudan pencereden sipariş iptal edilip stoklar geri iade edilebilir.

### K13: Müşteri & Ürün Formlarında Anlık Görsel Hata Geri Bildirimi ve Diyalog Güvencesi
- **Arayüz Seviyesi Kilit:** Geçersiz veri girildiğinde (ör. '515', 'asd', '1782', 1 karakterlik isim) diyalog kesinlikle kapatılmaz veya onaylanmaz (`accept()` çağrılmaz).
- **Görsel Vurgu ve Odak:** Hatalı alanların kenarlığı kırmızı (`border: 1.5px solid #ff4757; background-color: #2d1f24;`) olur, hemen altında Türkçe `⚠️` uyarı mesajı gösterilir ve klavye odağı ilk hatalı alana çekilir.
- **Mevcut Hatalı Kayıtlar ve Filtre:** Veritabanında daha önceden kalmış bozuk kayıtlar silinmez veya bozulmaz; tabloda `⚠️ Hatalı Bilgi` rozeti ve detaylı hata araç ipucu (tooltip) ile listelenir. Tabloya eklenen "Hatalı Kayıtlar" filtresi ile dükkan sahibi bu kayıtları izole edip düzenleyerek düzeltebilir.

### K14: Tablolarda WCAG Koyu Alternatif Satırlar ve Köşe Butonu Standardı
- **Kök Neden:** `setAlternatingRowColors(True)` açık olmasına rağmen `alternate-background-color` tanımlanmadığında Qt varsayılan Windows pencere rengi olan beyazı (`#ffffff`) kullanır; beyaz metin bu zemin üzerinde tamamen görünmez hale gelir.
- **Merkezi Çözüm (`theme.py`):**
  - Tüm tablolar için `background-color: #1e222a;` ve `alternate-background-color: #252b35;` atanmıştır.
  - Seçim (`#0984e3`), hover (`#2e3644`), dikey başlık (`#181b21`), köşe butonu (`QTableCornerButton::section`) ve viewport arka planı koyu tema ile homojenleştirilmiştir.
  - WCAG 2.1 kontrast oranı her satırda `>= 4.5:1` olarak testlerle garanti altına alınmıştır.

### K15: Tablo Satır Sayısı ve Hayalet Satır Engelleme Politikası
- **Kök Neden:** Ürün ekleme servisinin pasif ürünlerde `aktif` parametresini yok sayıp sabit `1` yazması veya tabloların yenilenirken eski satır sayısını koruması veri uyuşmazlığına yol açıyordu. Ayrıca alternatif satır beyazlığı metinleri gizleyerek satırı boş/hayalet gibi gösteriyordu.
- **Çözüm:** `urun_ekle` modeldeki `aktif` değerine tam uyar. Her tablo yenilemesinde `tablo.setRowCount(0)` ile sıfırdan ve tam `len(veriler)` kadar satır eklenir. Hiç sonuç bulunamadığında tablo temizlenir ve kullanıcıya turuncu "🔍 Arama kriterlerine uygun sonuç bulunamadı." uyarısı gösterilir.



