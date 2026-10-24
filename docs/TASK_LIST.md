# PROJE GÖREV LİSTESİ (TASK LIST)

## [x] Faz 0: Güvenceye Al
- [x] `git init` yapıldı, orijinal dosyalar `legacy/` altına dokunulmadan kopyalandı ve ilk commit atıldı.
- [x] Temel mimari kararlar (`docs/KARARLAR.md`) ve proje kuralları (`.agents/rules/proje_kurallari.md`) oluşturuldu.
- [x] İmplementasyon planı (`implementation_plan.md`) hazırlandı.
- [ ] Bölüm 3'teki B1-B8 hatalarını yakalayan başarısız testler (`tests/legacy_bugs/test_legacy_bugs.py`) yazılacak ve çalıştırılacak.
- [ ] Faz 0 Walkthrough oluşturulup git commit atılacak.

## [x] Faz 1: Temel Mimari, Servisler ve Veri Göçü
- [x] Dizin iskeleti: `app/config.py`, `app/utils/logging.py`, `app/domain/money.py`.
- [x] Veritabanı motoru: `app/db/connection.py`, `app/db/migrations/0001_initial.sql`, migrasyon çalıştırıcı.
- [x] Orijinal veri göçü: `app/db/legacy_import.py` (2 ürün, 17 sipariş kayıpsız aktarım).
- [x] Servis katmanı: `urun_servisi.py`, `satis_servisi.py`, `stok_servisi.py`, `musteri_servisi.py`, `kimlik_servisi.py`, `yedek_servisi.py`, `rapor_servisi.py`.
- [x] Servis testleri: Atomiklik, kuruş/KDV yuvarlama, göç doğrulama testleri (22/22 test geçti).
- [x] Faz 1 git commit tamamlandı.

## [x] Faz 2: Ürünler ve Hızlı Arama
- [x] Merkezi modern koyu tema: `app/ui/theme.py`.
- [x] Ürün listesi ve yönetim ekranı: `app/ui/pages/urunler_page.py`.
- [x] Girdi doğrulama ve pasife alma (soft-delete).
- [x] 20.000 sanal ürünle performans ve anlık arama testi (< 100 ms).
- [x] Faz 2 git commit tamamlandı.

## [ ] Faz 3: Satış, Sepet ve Stok Yönetimi
- [ ] Çok kalemli sepet ve hızlı satış ekranı: `app/ui/pages/satis_page.py`.
- [ ] Sipariş listesi ve filtreleme ekranı: `app/ui/pages/siparisler_page.py`.
- [ ] Sipariş iptal/iade ve stoğu tek transaction içinde geri alma.
- [ ] Stok hareketleri defteri ve kritik stok uyarı rozetleri.
- [ ] Faz 3 Walkthrough oluşturulup git commit atılacak.

## [ ] Faz 4: Kullanıcı Girişi, Cari Hesaplar ve Yedekleme
- [ ] Giriş ekranı, ilk kurulum sihirbazı ve rol yönetimi (`yonetici`, `personel`).
- [ ] Müşteri ve cari hesap yönetimi: veresiye bakiyesi, tahsilat girişi, ekstre.
- [ ] Otomatik ve elle yedekleme servisi, açılışta `PRAGMA quick_check`.
- [ ] Faz 4 Walkthrough oluşturulup git commit atılacak.

## [ ] Faz 5: Raporlar ve Veri İçe/Dışa Aktarımı
- [ ] Raporlar ekranı: Kasa, ciro, en çok satanlar, kritik stok, stok değeri.
- [ ] Excel ile toplu ürün içe aktarma (önizleme, hata raporlama) ve dışa aktarma (`openpyxl`).
- [ ] Bilgi fişi ve ekstre PDF çıktısı (`reportlab`).
- [ ] Faz 5 Walkthrough oluşturulup git commit atılacak.

## [ ] Faz 6: Cila, Paketleme ve Teslim
- [ ] Tek ana pencere (`main_window.py`) ve kenar çubuğu entegrasyonu.
- [ ] Ekran çözünürlüğü ve DPI testleri (`widget.grab()` ile `docs/ekran/`).
- [ ] `ruff` kod kalitesi ve tam test koşusu.
- [ ] Dokümanlar: `KURULUM.md`, `KULLANIM.md`, `YEDEKLEME.md`, `GELISTIRICI.md`, `DEGISIKLIK_GUNLUGU.md`.
- [ ] PyInstaller ve Inno Setup paketleme betikleri (`packaging/`).
- [ ] Son Walkthrough üretimi ve kapanış.
