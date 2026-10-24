-- 0001_initial.sql
-- Yeni Üretim Kalitesinde İlişkisel Şema

CREATE TABLE IF NOT EXISTS ayar (
    anahtar TEXT PRIMARY KEY,
    deger TEXT NOT NULL,
    aciklama TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS kullanici (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_adi TEXT NOT NULL UNIQUE,
    parola_hash TEXT NOT NULL,
    parola_salt TEXT NOT NULL,
    ad_soyad TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'personel' CHECK(rol IN ('yonetici', 'personel')),
    aktif INTEGER NOT NULL DEFAULT 1,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kategori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS marka (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS urun (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parca_kodu TEXT NOT NULL UNIQUE,
    barkod TEXT DEFAULT '',
    oem_no TEXT DEFAULT '',
    ad TEXT NOT NULL,
    kategori_id INTEGER REFERENCES kategori(id) ON DELETE SET NULL,
    marka_id INTEGER REFERENCES marka(id) ON DELETE SET NULL,
    alis_fiyati_kurus INTEGER NOT NULL DEFAULT 0,
    satis_fiyati_kurus INTEGER NOT NULL DEFAULT 0,
    kdv_orani INTEGER NOT NULL DEFAULT 20,
    stok INTEGER NOT NULL DEFAULT 0 CHECK(stok >= 0),
    kritik_stok INTEGER NOT NULL DEFAULT 5,
    raf_yeri TEXT DEFAULT '',
    aciklama TEXT DEFAULT '',
    aktif INTEGER NOT NULL DEFAULT 1,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS musteri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT NOT NULL,
    telefon TEXT DEFAULT '',
    eposta TEXT DEFAULT '',
    adres TEXT DEFAULT '',
    vergi_no_tc TEXT DEFAULT '',
    bakiye_kurus INTEGER NOT NULL DEFAULT 0,
    aktif INTEGER NOT NULL DEFAULT 1,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS siparis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    siparis_no TEXT NOT NULL UNIQUE,
    musteri_id INTEGER REFERENCES musteri(id) ON DELETE SET NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    durum TEXT NOT NULL DEFAULT 'tamamlandi' CHECK(durum IN ('tamamlandi', 'iptal', 'iade')),
    odeme_tipi TEXT NOT NULL DEFAULT 'nakit' CHECK(odeme_tipi IN ('nakit', 'kart', 'veresiye')),
    ara_toplam_kurus INTEGER NOT NULL DEFAULT 0,
    kdv_toplam_kurus INTEGER NOT NULL DEFAULT 0,
    genel_toplam_kurus INTEGER NOT NULL DEFAULT 0,
    aciklama TEXT DEFAULT '',
    kullanici_id INTEGER REFERENCES kullanici(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS siparis_kalem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    siparis_id INTEGER NOT NULL REFERENCES siparis(id) ON DELETE CASCADE,
    urun_id INTEGER REFERENCES urun(id) ON DELETE SET NULL,
    urun_adi_anlik TEXT NOT NULL,
    parca_kodu_anlik TEXT DEFAULT '',
    adet INTEGER NOT NULL CHECK(adet > 0),
    birim_fiyat_kurus INTEGER NOT NULL DEFAULT 0,
    kdv_orani INTEGER NOT NULL DEFAULT 20,
    toplam_kurus INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stok_hareket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urun_id INTEGER NOT NULL REFERENCES urun(id) ON DELETE CASCADE,
    hareket_tipi TEXT NOT NULL CHECK(hareket_tipi IN ('giris', 'satis', 'iade', 'iptal', 'sayim_duzeltme')),
    adet_degisim INTEGER NOT NULL,
    onceki_stok INTEGER NOT NULL,
    sonraki_stok INTEGER NOT NULL CHECK(sonraki_stok >= 0),
    referans_tipi TEXT DEFAULT 'manuel',
    referans_id INTEGER,
    kullanici_id INTEGER REFERENCES kullanici(id) ON DELETE SET NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    aciklama TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tahsilat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    musteri_id INTEGER NOT NULL REFERENCES musteri(id) ON DELETE CASCADE,
    tutar_kurus INTEGER NOT NULL CHECK(tutar_kurus > 0),
    odeme_tipi TEXT NOT NULL DEFAULT 'nakit' CHECK(odeme_tipi IN ('nakit', 'kart')),
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    aciklama TEXT DEFAULT '',
    kullanici_id INTEGER REFERENCES kullanici(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tedarikci (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unvan TEXT NOT NULL,
    yetkili TEXT DEFAULT '',
    telefon TEXT DEFAULT '',
    adres TEXT DEFAULT '',
    aktif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mal_kabul (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    belge_no TEXT DEFAULT '',
    tedarikci_id INTEGER REFERENCES tedarikci(id) ON DELETE SET NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    toplam_kurus INTEGER NOT NULL DEFAULT 0,
    aciklama TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS mal_kabul_kalem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mal_kabul_id INTEGER NOT NULL REFERENCES mal_kabul(id) ON DELETE CASCADE,
    urun_id INTEGER NOT NULL REFERENCES urun(id) ON DELETE CASCADE,
    adet INTEGER NOT NULL CHECK(adet > 0),
    birim_alis_kurus INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS denetim_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_id INTEGER REFERENCES kullanici(id) ON DELETE SET NULL,
    islem TEXT NOT NULL,
    detay TEXT DEFAULT '',
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Hızlı Arama ve Raporlama İndeksleri
CREATE INDEX IF NOT EXISTS idx_urun_parca_kodu ON urun(parca_kodu);
CREATE INDEX IF NOT EXISTS idx_urun_barkod ON urun(barkod);
CREATE INDEX IF NOT EXISTS idx_urun_oem ON urun(oem_no);
CREATE INDEX IF NOT EXISTS idx_urun_ad ON urun(ad);
CREATE INDEX IF NOT EXISTS idx_urun_aktif ON urun(aktif);
CREATE INDEX IF NOT EXISTS idx_siparis_tarih ON siparis(tarih);
CREATE INDEX IF NOT EXISTS idx_siparis_durum ON siparis(durum);
CREATE INDEX IF NOT EXISTS idx_stok_hareket_urun ON stok_hareket(urun_id);
CREATE INDEX IF NOT EXISTS idx_musteri_ad ON musteri(ad_soyad);

-- Başlangıç Ayarları
INSERT OR IGNORE INTO ayar (anahtar, deger, aciklama) VALUES
    ('dukkan_adi', 'Oto Yedek Parça Dükkanı', 'Dükkan Ticari Ünvanı'),
    ('varsayilan_kdv', '20', 'Varsayılan KDV Yüzdesi'),
    ('telefon', '0212 000 00 00', 'Dükkan İletişim Telefonu'),
    ('adres', 'Sanayi Sitesi, No: 1', 'Dükkan Adresi'),
    ('fis_alti_notu', 'Bilgi fişidir, mali değeri yoktur.', 'Satış Fişi Alt Notu'),
    ('legacy_import_tamamlandi', '0', 'Eski veritabanı göçü yapıldı mı');

-- Başlangıç Kategorileri (10 Adet)
INSERT OR IGNORE INTO kategori (ad) VALUES
    ('Motor Grubu'),
    ('Elektrik ve Elektronik'),
    ('Fren Sistemi'),
    ('Süspansiyon'),
    ('Şanzıman'),
    ('Soğutma Sistemi'),
    ('Kaporta'),
    ('İç Donanım'),
    ('Egzoz Sistemi'),
    ('Yakıt Sistemi');

-- Başlangıç Markaları (35 Adet)
INSERT OR IGNORE INTO marka (ad) VALUES
    ('Bosch'), ('Delphi'), ('Valeo'), ('Brembo'), ('Malhe'), ('TRW'),
    ('Mann Filter'), ('Denso'), ('NGK'), ('Contitech'), ('Sachs'),
    ('Ferodo'), ('Febi Bilstein'), ('Hella'), ('Lemförder'), ('KYB'),
    ('Textar'), ('SKF'), ('INA'), ('VDO'), ('Preiburg'), ('Behr'),
    ('Osram'), ('Champion'), ('Dayco'), ('Gates'), ('Beru'),
    ('Monroe'), ('ATE'), ('Zimmermann'), ('Bosal'),
    ('WIX Filters'), ('Lucas'), ('ACDelco'), ('Hitachi');
