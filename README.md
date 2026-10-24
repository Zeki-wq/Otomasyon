# Oto Yedek Parça Otomasyonu (v1.0.0)

Oto yedek parça perakende ve toptan satış dükkanları için geliştirilmiş, yüksek performanslı, modern arayüzlü ve %100 çevrimdışı çalışabilen masaüstü ERP ve satış otomasyon yazılımı.

---

## 🌟 Öne Çıkan Özellikler

- **Modern & Yüksek Kontrastlı Arayüz (PySide6 / Qt 6):**
  - Koyu tema (Dark Mode) ve WCAG standartlarına tam uyumlu kontrast oranları.
  - 1366x768 piksel ve %100, %125, %150 Windows DPI ölçekleme desteği (sıfır metin kırpılması).
- **Hızlı Satış ve Sepet Yönetimi:**
  - Barkod, OEM numarası, parça kodu ve ürün adına göre milisaniyeler içinde arama (20.000+ ürün indeksli).
  - Anlık sepet adet artırma, KDV dahil/hariç fiyatlandırma, nakit, kart ve veresiye tahsilat.
  - Sipariş iptali ve iade durumlarında otomatik stok geri yükleme garantisi.
- **Cari Hesap ve Müşteri Defteri:**
  - TC Kimlik / Vergi Numarası ve telefon formatı doğrulaması (algoritmik sağlama ve maskeleme).
  - Cari bakiye takibi, borç/alacak ekstresi ve tahsilat makbuzu.
- **Raporlama ve Fiş Çıktısı:**
  - ReportLab ile termal yazıcı formatında (80mm) ve A4 boyutunda anlık PDF satış fişi üretimi.
  - 5.000+ satırlık Excel (.xlsx) ürün listesini hücre hücre doğrulayarak toplu içe aktarma.
- **Veri Güvenliği ve Sağlamlık:**
  - SQLite WAL (Write-Ahead Logging) modu ile eşzamanlı işlem güvenliği.
  - Otomatik kapanış yedeği, USB/Harici sürücüye tek tıkla yedekleme ve SQLite Online Backup API ile canlı geri yükleme.
  - Şema yükseltmelerinde (migration) otomatik güvenlik yedeği ve hata anında rollback koruması.
  - Yönetici doğrulamalı çift aşamalı "Fabrika Ayarlarına Dönüş" seçeneği.

---

## 💻 Sistem Gereksinimleri

| Bileşen | Minimum Gereksinim |
| :--- | :--- |
| **İşletim Sistemi** | Windows 10/11 (64-bit), Debian/Ubuntu/Mint, Fedora/RHEL/CentOS |
| **Ekran Çözünürlüğü** | 1366 x 768 piksel |
| **Bellek (RAM)** | 2 GB RAM |
| **Depolama** | 150 MB disk alanı (Kurulum için) |
| **İnternet** | Zorunlu değildir (%100 yerel ve çevrimdışı) |
| **Kullanıcı İzni** | Standart kullanıcı (Yönetici yetkisi gerekmez) |

---

## 🚀 Kurulum ve İlk Çalıştırma

### Windows:
1. `dist/installer/OtoYedekParca_Setup_v1.0.0.exe` kurulum dosyasını çalıştırınız.
2. Program kullanıcı profili altına (`%LOCALAPPDATA%\Programs\OtoYedekParca`) kurulur.
3. Masaüstündeki simgeye tıklayarak programı başlatınız.
4. İlk açılışta temiz şema otomatik oluşturulur ve **İlk Kurulum Sihirbazı** gelir.
5. Detaylı rehber için lütfen [docs/KURULUM.md](docs/KURULUM.md) belgesini inceleyiniz.

### Debian / Ubuntu:
```bash
sudo apt install ./dist/installer/otoyedekparca_1.0.0_all.deb
otoyedekparca
```

### Fedora / RHEL:
```bash
tar -xzf dist/installer/otoyedekparca-1.0.0-fedora-installer.tar.gz
cd otoyedekparca-1.0.0
sudo ./install.sh
otoyedekparca
```
Detaylı Linux kurulum adımları ve RPM derleme yönergeleri için [docs/LINUX_KURULUM.md](docs/LINUX_KURULUM.md) belgesine bakınız.

---

## 🛠️ Geliştirici ve Derleme Yönergesi

### Testleri Çalıştırma:
```powershell
pytest -v --timeout=120
```

### Tek Komutla Resmi Sürüm Üretimi:
```powershell
python packaging/build_release.py
```
Bu komut sırasıyla:
1. Tüm otomatik testleri (68 test) koşturur.
2. PyInstaller ile bağımsız `--onedir` paketini derler.
3. `packaging/dogrula_paket.py` ile güvenlik ve veri temizliği denetimi yapar.
4. Kod imzalama sertifikasını kontrol eder (varsa imzalar).
5. Inno Setup 6 (`ISCC.exe`) ile `dist/installer/OtoYedekParca_Setup_v1.0.0.exe` kurulum programını üretir.

---

## 📜 Lisans ve Yasal Bildirimler

- **Telif Hakkı:** Telif Hakkı (C) 2026 Oto Yedek Parça Otomasyonu. Tüm hakları saklıdır.
- **Yazılım Lisansı:** Tescilli ve ticari lisans sözleşmesi için [LICENSE](LICENSE) dosyasına bakınız.
- **Üçüncü Taraf Lisanslar:** PySide6 (LGPLv3 dinamik bağlama) ve diğer açık kaynak kütüphane lisans bildirimleri için [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) dosyasını inceleyiniz.
