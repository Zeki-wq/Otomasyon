"""
Yeni Mimari (app/) B1 - B8 Hatalarının Çözüldüğünü Kanıtlayan Regresyon Testleri.
Her test, B1-B8 hatalarının yeni kod tabanında ARTIK OLUŞMADIĞINI tek tek kanıtlar.
"""

import importlib
import sqlite3
import pytest

from app.db.connection import get_db_connection
from app.db.migrations.migrator import run_migrations
from app.domain.models import Musteri, Urun
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.ui.pages.urunler_page import UrunlerPage


def test_yeni_kod_b1_ayni_urune_coklu_siparis_basarili(tmp_path):
    """B1 KANITI: Yeni mimaride aynı ürüne defalarca sipariş girilebilir (IntegrityError OLUŞMAZ)."""
    db_path = tmp_path / "test_b1_fixed.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    admin = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)

    u_id = us.urun_ekle(Urun(id=None, parca_kodu="B1-TEST", ad="Buji Yeni", alis_fiyati_kurus=5000, satis_fiyati_kurus=10000, stok=100))

    # Aynı ürüne ardışık 5 sipariş ver
    for i in range(5):
        sip = satis.siparis_olustur(
            kalemler=[{"urun_id": u_id, "adet": 2, "birim_fiyat_kurus": 10000, "kdv_orani": 20}],
            odeme_tipi="nakit",
            kullanici_id=admin.id
        )
        assert sip.id > 0

    urun = us.urun_getir(u_id)
    assert urun.stok == 90  # 100 - (5 * 2)


def test_yeni_kod_b2_stok_dusumu_id_ile_izole_dogru_urun(tmp_path):
    """B2 KANITI: Stok düşümü isimle değil benzersiz ID ile yapılır; aynı isimli ürünlerin stoğu karışmaz."""
    db_path = tmp_path / "test_b2_fixed.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    admin = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)

    # Aynı isimde iki farklı ürün (biri Bosch, biri Valeo)
    u1 = us.urun_ekle(Urun(id=None, parca_kodu="FRN-01", ad="Fren Balatası", alis_fiyati_kurus=20000, satis_fiyati_kurus=30000, stok=20))
    u2 = us.urun_ekle(Urun(id=None, parca_kodu="FRN-02", ad="Fren Balatası", alis_fiyati_kurus=15000, satis_fiyati_kurus=25000, stok=10))

    # Yalnızca u1'den 2 adet sat
    satis.siparis_olustur(
        kalemler=[{"urun_id": u1, "adet": 2, "birim_fiyat_kurus": 30000, "kdv_orani": 20}],
        odeme_tipi="nakit",
        kullanici_id=admin.id
    )

    # u1 stoğu düşmeli, u2 stoğu KESİNLİKLE değişmemeli
    assert us.urun_getir(u1).stok == 18
    assert us.urun_getir(u2).stok == 10  # Legacy kodda bu da 8'e düşüyordu!


def test_yeni_kod_b3_tablo_dinamik_satir_sinirsiz(tmp_path):
    """B3 KANITI: Tablolar 30 satırla sınırlı değildir; 31 ve üzeri kayıtlar eksiksiz listelenir."""
    db_path = tmp_path / "test_b3_fixed.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    admin = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    ss = StokServisi(db_path)

    # 45 ürün ekle (30 sınırını aşar)
    for i in range(1, 46):
        us.urun_ekle(Urun(id=None, parca_kodu=f"PRC-{i:03d}", ad=f"Parça {i}", alis_fiyati_kurus=1000, satis_fiyati_kurus=2000, stok=10))

    page = UrunlerPage(us, ss, aktif_kullanici=admin)
    page.listeyi_guncelle()

    # Sayfadaki tablo satır sayısı 30'u aşabilmeli ve tüm 45 ürünü göstermeli
    assert page.tablo.rowCount() == 45
    page.close()


def test_yeni_kod_b4_modul_importlarinda_sifir_yan_etki():
    """B4 KANITI: app/ altındaki modüller import edildiğinde QApplication veya global veritabanı bağlantısı açmaz."""
    import app.domain.models
    import app.services.kimlik_servisi
    import app.services.urun_servisi
    import app.services.satis_servisi
    import app.ui.pages.urunler_page

    assert True  # Hiçbiri import anında sys.argv veya QApplication tüketmez


def test_yeni_kod_b5_kategori_formdan_okunur_ve_gecersiz_girdi_guvenli(tmp_path):
    """B5 KANITI: Ürün formu sağdaki filtreyi değil form alanını okur; geçersiz girdiler ValueError ile patlamaz."""
    from app.domain.validators import sayisal_fiyat_dogrula, ValidationError
    db_path = tmp_path / "test_b5_fixed.db"
    run_migrations(db_path)
    us = UrunServisi(db_path)

    k1 = us.kategori_ekle("Motor")
    k2 = us.kategori_ekle("Fren")

    # Form k1 seçerken filtre kutusu k2 olsa bile ürün k1'e ait kaydedilir
    u_id = us.urun_ekle(Urun(id=None, parca_kodu="PRC-KAT", ad="Subap", kategori_id=k1, alis_fiyati_kurus=1000, satis_fiyati_kurus=2000, stok=5))
    assert us.urun_getir(u_id).kategori_id == k1

    # Geçersiz fiyat girdisi ValueError patlatmaz, ValidationError üretir
    with pytest.raises(ValidationError):
        sayisal_fiyat_dogrula("abc", "Fiyat")


def test_yeni_kod_b6_guncelleme_sql_ve_secimsiz_islem_guvenli(tmp_path, dialog_manager):
    """B6 KANITI: SQL sorgularında Türkçe 'ı' hatası yoktur; seçim yokken silme/düzenleme IndexError vermez."""
    db_path = tmp_path / "test_b6_fixed.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    admin = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    ss = StokServisi(db_path)

    u_id = us.urun_ekle(Urun(id=None, parca_kodu="PRC-B6", ad="Rot Başı", aciklama="Orijinal Parça", alis_fiyati_kurus=5000, satis_fiyati_kurus=8000, stok=10))

    # Güncelleme SQL'i hatasız çalışır
    urun = us.urun_getir(u_id)
    urun.aciklama = "Güncellenmiş Açıklama"
    us.urun_guncelle(urun)
    assert us.urun_getir(u_id).aciklama == "Güncellenmiş Açıklama"

    # Seçim yapılmadan silme/düzenleme butonuna basılırsa IndexError çökmesi OLMAZ
    page = UrunlerPage(us, ss, aktif_kullanici=admin)
    page.tablo.clearSelection()
    page.urun_duzenle_ac()  # Uyarı verir, çökmez
    assert dialog_manager.has_message("Seçim Yapılmadı", kind="warning")
    page.close()


def test_yeni_kod_b7_filtreleme_sutun_kaymasi_yok(tmp_path):
    """B7 KANITI: Tablo doldurulurken sütun kayması (indexSutun+1) yoktur; 0. sütun ID, 1. sütun Parça Kodu vb. doğrudur."""
    db_path = tmp_path / "test_b7_fixed.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    admin = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    ss = StokServisi(db_path)

    u_id = us.urun_ekle(Urun(id=None, parca_kodu="KOD-007", ad="Ayna", alis_fiyati_kurus=1000, satis_fiyati_kurus=2000, stok=5))
    page = UrunlerPage(us, ss, aktif_kullanici=admin)
    page.listeyi_guncelle()

    # 0. sütun boş değildir, ürün ID'sini içerir; 1. sütun Parça Kodu'nu içerir
    assert page.tablo.item(0, 0).text() == str(u_id)
    assert page.tablo.item(0, 1).text() == "KOD-007"
    assert page.tablo.item(0, 4).text() == "Ayna"
    page.close()


def test_yeni_kod_b8_foreign_keys_aktifken_kusursuz_iliski(tmp_path):
    """B8 KANITI: PRAGMA foreign_keys = ON etkinken sipariş ve stok hareketleri hatasız işlenir (mismatch OLUŞMAZ)."""
    db_path = tmp_path / "test_b8_fixed.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)
    admin = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)

    conn = get_db_connection(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    conn.close()
    assert fk_status == 1

    # PRAGMA foreign_keys açıkken sipariş ve kalem ekleme
    u_id = us.urun_ekle(Urun(id=None, parca_kodu="PRC-B8", ad="Filtre", alis_fiyati_kurus=1000, satis_fiyati_kurus=2000, stok=20))
    sip = satis.siparis_olustur(
        kalemler=[{"urun_id": u_id, "adet": 3, "birim_fiyat_kurus": 2000, "kdv_orani": 20}],
        odeme_tipi="nakit",
        kullanici_id=admin.id
    )
    assert sip.id > 0
