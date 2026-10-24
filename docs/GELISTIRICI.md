# OTO YEDEK PARÇA OTOMASYONU - GELİŞTİRİCİ DOKÜMANI (GELISTIRICI.md)

Bu doküman, projeye katkıda bulunacak yazılım mühendisleri ve yapay zeka ajanları için teknik mimariyi ve geliştirme standartlarını açıklar.

---

## 1. Mimari Katmanlar

```
oto-yedek-parca/
  app/
    main.py            # Tek giriş noktası, tek QApplication, DPI ve tek örnek kilidi
    config.py          # %APPDATA%\OtoYedekParca dizinleri, sabitler, sürüm
    db/
      connection.py    # WAL modlu SQLite bağlantısı, sağlık kontrolü
      legacy_import.py # urunler12.db dosyasını kayıpsız ve idempotent aktaran motor
      migrations/      # PRAGMA user_version ile sıralı NNNN_*.sql migrasyonları
    domain/
      money.py         # Kuruş <-> TL, KDV yuvarlama (ROUND_HALF_UP)
      models.py        # Dataclass varlıkları
    services/          # Bağımsız iş mantığı (Qt'ye bağımlı DEĞİL!)
    ui/
      theme.py         # Merkezi koyu tema (#1e1f26, #262b33, #00a8ff)
      main_window.py   # Kenar çubuğu ve QStackedWidget
      pages/           # Dashboard, Satış, Ürünler, Siparişler, Müşteriler, vb.
    utils/
      logging.py       # RotatingFileHandler + sys.excepthook
      export.py        # openpyxl ve reportlab entegrasyonu
  tests/               # 33+ otomasyonlu pytest ve pytest-qt birim testi
  legacy/              # Orijinal dokunulmamış legacy kodlar ve veritabanı
  packaging/           # PyInstaller spec ve Inno Setup kurulum betikleri
```

---

## 2. Bağlayıcı Geliştirme Kuralları

1. **Para her zaman kuruş:** Veritabanında ve bellek içinde `INTEGER` kuruş saklanır. Dönüşümler sadece `app/domain/money.py` ile yapılır.
2. **UI'da SQL yok, serviste Qt yok:** Kullanıcı arayüzü yalnızca servisleri çağırır. Servisler veritabanıyla parametreli SQL kullanarak konuşur.
3. **Şema Değişikliği:** Doğrudan DB üzerinde yapılamaz. `app/db/migrations/` altında sıralı `.sql` dosyası olarak eklenmelidir.
4. **Hata Düzeltme Kuralı:** Yeni bir hata tespit edildiğinde önce onu yeniden üreten başarısız bir test yazılır, ardından kod düzeltilir.
5. **Kullanıcı Metinleri:** Kullanıcıya görünen tüm metinler Türkçe, kod tanımlayıcıları tutarlı ASCII olmalıdır.

---

## 3. Testleri Çalıştırma ve Kod Kalitesi

Tüm birim, entegrasyon ve arayüz testlerini çalıştırmak için:

```powershell
$env:QT_QPA_PLATFORM="offscreen"
pytest tests/ -v
```

Kod kalitesi denetimi için:
```powershell
ruff check app/ tests/
```

PyInstaller ile derleme için:
```powershell
python packaging/build_exe.py
```
