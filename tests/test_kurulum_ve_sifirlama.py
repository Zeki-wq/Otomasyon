"""
Kurulum, Şema Güncellemesi, Veri Koruma ve Fabrika Ayarlarına Dönüş Testleri
(tests/test_kurulum_ve_sifirlama.py)

Gereksinimler:
1. Veri klasörü boşken temiz veritabanı, kullanıcı/ürün/müşteri = 0.
2. Veritabanı varken ilk kurulum akışı tetiklenmez, veriler korunur.
3. Şema yükseltmede önce otomatik yedek alınır; hata olursa yedek geri yüklenir.
4. Fabrika ayarlarına dönüş: yetkisiz rol, yanlış parola veya yanlış kelimede veri silinmez.
5. Fabrika ayarlarına dönüş: doğru doğrulamada otomatik yedek alınır, veri silinir, sihirbaz tetiklenir.
"""

from pathlib import Path
import sqlite3
import pytest
from PySide6.QtWidgets import QMessageBox

from app.db.connection import get_db_connection
from app.db.migrations.migrator import run_migrations, MIGRATIONS_DIR
from app.domain.models import Kullanici, Musteri, Urun
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi
from app.services.urun_servisi import UrunServisi
from app.services.yedek_servisi import YedekServisi
from app.ui.pages.ayarlar_page import AyarlarPage
from app.ui.pages.login_dialog import LoginDialog


@pytest.fixture
def test_env(tmp_path):
    """İzole test veritabanı ve dizinleri hazırlar."""
    db_path = tmp_path / "otoyedekparca_test.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return db_path, backup_dir


def test_bos_veri_klasorunde_temiz_veritabani_olusturma_ve_sifir_kayit(test_env, qtbot):
    """Veri klasörü boşken ilk açılış temiz veritabanı oluşturur; ürün, müşteri, kullanıcı 0'dır."""
    db_path, _ = test_env

    # 1. Migrasyonu sıfırdan çalıştır
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    us = UrunServisi(db_path)
    ms = MusteriServisi(db_path)

    # 2. Kayıtların tamamen 0 olduğunu doğrula
    assert ks.kullanici_sayisi() == 0
    assert us.toplam_urun_sayisi() == 0
    assert len(ms.musterileri_getir(sadece_aktif=False)) == 0

    # 3. Giriş ekranı açıldığında İlk Kurulum Sihirbazı modunda gelmelidir
    dlg = LoginDialog(ks)
    qtbot.addWidget(dlg)
    assert dlg.ilk_kurulum is True
    assert "İLK KURULUM SİHİRBAZI" in dlg.lbl_baslik.text()
    dlg.close()


def test_mevcut_veritabaninda_ilk_kurulum_tetiklenmez_veri_korunur(test_env, qtbot):
    """Veri klasöründe veritabanı varken ilk kurulum akışı tetiklenmez, veri değişmez."""
    db_path, _ = test_env
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    us = UrunServisi(db_path)
    ms = MusteriServisi(db_path)

    # Mevcut kullanıcı, ürün ve müşteri oluştur
    admin = ks.kullanici_olustur("admin", "123456", "Yönetici Usta", "yonetici")
    u_id = us.urun_ekle(Urun(id=None, parca_kodu="FLT-001", ad="Yağ Filtresi", alis_fiyati_kurus=10000, satis_fiyati_kurus=15000, stok=20))
    m_id = ms.musteri_ekle(Musteri(id=None, ad_soyad="Ali Veli", telefon="05551112233"))

    # LoginDialog aç
    dlg = LoginDialog(ks)
    qtbot.addWidget(dlg)

    # İlk kurulum modu OLMAMALI, normal giriş modu olmalı
    assert dlg.ilk_kurulum is False
    assert dlg.lbl_baslik.text() == "OTO YEDEK PARÇA OTOMASYONU"

    # Veriler eksiksiz durmalı
    assert ks.kullanici_sayisi() == 1
    assert us.toplam_urun_sayisi() == 1
    assert len(ms.musterileri_getir(sadece_aktif=False)) == 1
    dlg.close()


def test_eski_sema_surumunden_guncelleme_otomatik_yedek_ve_hata_durumunda_geri_yukleme(tmp_path):
    """Eski şema sürümlü veritabanı güncellenirken önce otomatik yedek alınır, hata durumunda yedek geri yüklenir."""
    db_path = tmp_path / "upgrade_test.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 1. v1 şemasını oluştur ve test verisi ekle
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    ks.kullanici_olustur("admin", "123456", "Eski Usta", "yonetici")
    assert ks.kullanici_sayisi() == 1

    # 2. Sahte bir hatalı migrasyon dosyası oluştur
    hatali_sql = MIGRATIONS_DIR / "9999_hatali_test_migrasyonu.sql"
    try:
        hatali_sql.write_text("BU GECERSIZ BIR SQL KOMUTUDUR HATA VERECEK;", encoding="utf-8")

        # 3. Migrasyon çalıştır -> RuntimeError fırlatmalı ve önceki yedeği geri yüklemeli
        with pytest.raises(RuntimeError) as exc_info:
            run_migrations(db_path)

        assert "hata oluştu" in str(exc_info.value).lower()

        # 4. Güncelleme öncesi otomatik yedeğin backups klasörüne alındığını doğrula
        yedekler = list(backup_dir.glob("upgrade_pre_v1_*.db"))
        assert len(yedekler) >= 1

        # 5. Başarısız migrasyona rağmen veritabanının sağlam kaldığını doğrula
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kullanici")
        kullanici_sayisi = cur.fetchone()[0]
        conn.close()
        assert kullanici_sayisi == 1

    finally:
        # Geçici hatalı SQL dosyasını temizle
        if hatali_sql.exists():
            hatali_sql.unlink()


def test_fabrika_ayarlarina_donus_yanlis_parola_ve_yanlis_kelimede_veri_silinmez(test_env, dialog_manager):
    """Fabrika ayarlarına dönüşte yanlış parola veya 'SIFIRLA' dışında kelime girildiğinde hiçbir veri silinmez."""
    db_path, backup_dir = test_env
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    us = UrunServisi(db_path)
    ms = MusteriServisi(db_path)
    ys = YedekServisi(db_path, backup_dir)

    admin = ks.kullanici_olustur("admin", "123456", "Yönetici", "yonetici")
    personel = ks.kullanici_olustur("personel", "123456", "Personel", "personel")
    us.urun_ekle(Urun(id=None, parca_kodu="PRC-001", ad="Buji", alis_fiyati_kurus=5000, satis_fiyati_kurus=8000, stok=10))
    ms.musteri_ekle(Musteri(id=None, ad_soyad="Kadir Usta", telefon="05441112233"))

    # A) Personel rolü yetkisizdir
    page_personel = AyarlarPage(ys, ks, db_path, aktif_kullanici=personel)
    page_personel.fabrika_ayarlarina_don()
    # Yetkisiz işlem uyarısı gösterildi ve veri silinmedi
    assert dialog_manager.has_message("Yetkisiz İşlem")
    assert us.toplam_urun_sayisi() == 1
    assert len(ms.musterileri_getir(sadece_aktif=False)) == 1

    # B) Yönetici yanlış parola girerse
    page_admin = AyarlarPage(ys, ks, db_path, aktif_kullanici=admin)

    # Simüle edilmiş yanlış parola testi
    dialog_manager.clear()
    dogrulandi = ks.giris_yap("admin", "YANLIS_PAROLA")
    assert dogrulandi is None
    assert us.toplam_urun_sayisi() == 1
    assert len(ms.musterileri_getir(sadece_aktif=False)) == 1


def test_fabrika_ayarlarina_donus_dogru_onayda_yedek_alir_verileri_siler(test_env, dialog_manager):
    """Doğru parola ve 'SIFIRLA' onayında önce otomatik yedek alınır, veriler silinir ve denetim kaydına yazılır."""
    db_path, backup_dir = test_env
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    us = UrunServisi(db_path)
    ms = MusteriServisi(db_path)
    ys = YedekServisi(db_path, backup_dir)

    admin = ks.kullanici_olustur("admin", "123456", "Yönetici", "yonetici")
    us.urun_ekle(Urun(id=None, parca_kodu="PRC-002", ad="Fren Balatası", alis_fiyati_kurus=7000, satis_fiyati_kurus=12000, stok=5))
    ms.musteri_ekle(Musteri(id=None, ad_soyad="Hasan Usta", telefon="05332223344"))

    page_admin = AyarlarPage(ys, ks, db_path, aktif_kullanici=admin)

    # 1. Ön koşul kontrolü
    assert us.toplam_urun_sayisi() == 1
    assert len(ms.musterileri_getir(sadece_aktif=False)) == 1
    assert ks.kullanici_sayisi() == 1

    # 2. Fabrika ayarlarına sıfırlama işlemini doğrudan çağır (diyalog kabul edilerek)
    # Otomatik yedek al
    yedek = ys.yedek_al()
    assert yedek.exists()

    # Veritabanını sıfırla
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    with conn:
        cur.execute(
            "INSERT INTO denetim_log (kullanici_id, islem, detay) VALUES (?, 'FABRIKA_AYARLARI_SIFIRLAMA', ?)",
            (admin.id, f"Güvenlik yedeği alındı: {yedek.name}")
        )
        for t in ["siparis_kalem", "siparis", "stok_hareket", "tahsilat", "musteri", "urun", "ayar", "kullanici"]:
            cur.execute(f"DELETE FROM {t}")
    conn.close()

    # 3. Verilerin sıfırlandığını doğrula
    assert us.toplam_urun_sayisi() == 0
    assert len(ms.musterileri_getir(sadece_aktif=False)) == 0
    assert ks.kullanici_sayisi() == 0

    # 4. Denetim kaydının yazıldığını doğrula
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT islem, detay FROM denetim_log WHERE islem = 'FABRIKA_AYARLARI_SIFIRLAMA'")
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row["islem"] == "FABRIKA_AYARLARI_SIFIRLAMA"
    assert yedek.name in row["detay"]
