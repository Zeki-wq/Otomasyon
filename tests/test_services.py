"""
İş Mantığı Servisleri ve Güvenlik/Dayanıklılık Testleri
Atomiklik, yetersiz stok reddi, iptalde stok iadesi, 100 ardışık sipariş, yedekleme.
"""

import pytest
from app.db.migrations.migrator import run_migrations
from app.domain.models import Urun, Musteri
from app.services.kimlik_servisi import KimlikServisi
from app.services.urun_servisi import UrunServisi
from app.services.stok_servisi import StokServisi
from app.services.satis_servisi import SatisServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.yedek_servisi import YedekServisi


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "servis_test.db"
    run_migrations(db_file)
    return str(db_file)


def test_kimlik_servisi_parola_ve_giris(test_db):
    kimlik = KimlikServisi(test_db)
    assert kimlik.kullanici_sayisi() == 0

    # Yönetici oluştur
    admin = kimlik.kullanici_olustur("admin", "GucluParola123!", "Yönetici Kullanıcı", "yonetici")
    assert admin.id is not None
    assert admin.rol == "yonetici"
    assert admin.parola_hash != "GucluParola123!"  # Parola açık tutulmaz!

    # Doğru parola ile giriş
    giris_basarili = kimlik.giris_yap("admin", "GucluParola123!")
    assert giris_basarili is not None
    assert giris_basarili.ad_soyad == "Yönetici Kullanıcı"

    # Yanlış parola ile giriş
    giris_hatali = kimlik.giris_yap("admin", "YanlisParola")
    assert giris_hatali is None

    # Mükerrer kullanıcı adı engeli
    with pytest.raises(ValueError):
        kimlik.kullanici_olustur("admin", "BaskaParola", "İkinci Admin", "yonetici")


def test_urun_ve_stok_servisi(test_db):
    urun_srv = UrunServisi(test_db)
    stok_srv = StokServisi(test_db)

    # Ürün ekle
    yeni_urun = Urun(
        id=None,
        parca_kodu="FRN-001",
        ad="Ön Fren Balatası",
        satis_fiyati_kurus=45000,  # 450,00 TL
        alis_fiyati_kurus=30000,   # 300,00 TL
        stok=25,
        kritik_stok=5
    )
    u_id = urun_srv.urun_ekle(yeni_urun)
    assert u_id > 0

    # Ürün oku
    getirilen = urun_srv.urun_getir(u_id)
    assert getirilen is not None
    assert getirilen.stok == 25
    assert getirilen.parca_kodu == "FRN-001"

    # Stok düzeltme
    stok_srv.stok_duzeltme_yap(u_id, 30, "Yıl sonu sayım fazlası")
    guncel_urun = urun_srv.urun_getir(u_id)
    assert guncel_urun.stok == 30

    # Stok hareket defteri kontrolü
    hareketler = stok_srv.stok_hareketlerini_getir(u_id)
    assert len(hareketler) >= 2  # Açılış ve sayım düzeltme


def test_satis_ve_stok_atomikligi(test_db):
    urun_srv = UrunServisi(test_db)
    satis_srv = SatisServisi(test_db)

    # 10 adet stoğu olan ürün
    u_id = urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="BUJ-001",
        ad="İridyum Buji",
        satis_fiyati_kurus=15000,
        stok=10
    ))

    # 4 adet sat
    siparis = satis_srv.siparis_olustur(
        kalemler=[{"urun_id": u_id, "adet": 4}],
        odeme_tipi="nakit"
    )
    assert siparis.id is not None
    assert siparis.genel_toplam_kurus == 15000 * 4 + int(15000 * 4 * 0.20)

    # Stok 10 -> 6 olmalı
    urun = urun_srv.urun_getir(u_id)
    assert urun.stok == 6

    # Yetersiz stok reddi: 7 adet istemeyi dene (stokta 6 var)
    with pytest.raises(ValueError) as exc_info:
        satis_srv.siparis_olustur(
            kalemler=[{"urun_id": u_id, "adet": 7}],
            odeme_tipi="nakit"
        )
    assert "Yetersiz stok" in str(exc_info.value)

    # Hata sonrası stok değişmemeli (atomik rollback):
    urun = urun_srv.urun_getir(u_id)
    assert urun.stok == 6


def test_ayni_urune_100_ardisik_siparis_b1_cozumu(test_db):
    """
    B1 Hatasının Çözüm Testi:
    Eski sistemde aynı ürüne 2. sipariş IntegrityError veriyordu.
    Yeni sistemde aynı ürüne 100 ardışık sipariş sorunsuz açılabilmeli.
    """
    urun_srv = UrunServisi(test_db)
    satis_srv = SatisServisi(test_db)

    u_id = urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="CIV-100",
        ad="M10 Çelik Cıvata",
        satis_fiyati_kurus=1000,
        stok=500
    ))

    # 100 ardışık sipariş
    for i in range(100):
        sip = satis_srv.siparis_olustur(
            kalemler=[{"urun_id": u_id, "adet": 1}],
            odeme_tipi="nakit"
        )
        assert sip.id is not None

    urun = urun_srv.urun_getir(u_id)
    assert urun.stok == 400


def test_siparis_iptalinde_stok_geri_alma(test_db):
    urun_srv = UrunServisi(test_db)
    satis_srv = SatisServisi(test_db)

    u_id = urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="JNT-001",
        ad="Çelik Jant",
        satis_fiyati_kurus=200000,
        stok=20
    ))

    # 5 adet sat -> stok 15'e düşer
    sip = satis_srv.siparis_olustur(
        kalemler=[{"urun_id": u_id, "adet": 5}],
        odeme_tipi="nakit"
    )
    assert urun_srv.urun_getir(u_id).stok == 15

    # Siparişi iptal et -> stok 20'ye geri dönmeli
    satis_srv.siparis_iptal_et(sip.id, "Müşteri siparişi vazgeçti")
    assert urun_srv.urun_getir(u_id).stok == 20

    # Zaten iptal edilen siparişi tekrar iptal etmeyi dene
    with pytest.raises(ValueError):
        satis_srv.siparis_iptal_et(sip.id)


def test_musteri_ve_veresiye_tahsilat(test_db):
    musteri_srv = MusteriServisi(test_db)
    urun_srv = UrunServisi(test_db)
    satis_srv = SatisServisi(test_db)

    m_id = musteri_srv.musteri_ekle(Musteri(
        id=None,
        ad_soyad="Ahmet Usta (Oto Tamir)",
        telefon="0555 123 4567"
    ))

    u_id = urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="YAG-001",
        ad="5W-30 Motor Yağı 4L",
        satis_fiyati_kurus=100000,  # 1.000 TL + %20 KDV = 1.200 TL = 120.000 kuruş
        stok=50
    ))

    # Veresiye sipariş oluştur
    sip = satis_srv.siparis_olustur(
        kalemler=[{"urun_id": u_id, "adet": 1}],
        musteri_id=m_id,
        odeme_tipi="veresiye"
    )

    # Müşteri bakiyesi 120.000 kuruş olmalı
    musteri = musteri_srv.musteri_getir(m_id)
    assert musteri.bakiye_kurus == 120000

    # 500,00 TL (50.000 kuruş) tahsilat yap
    musteri_srv.tahsilat_yap(m_id, 50000, "nakit", "Kısmi tahsilat")
    musteri = musteri_srv.musteri_getir(m_id)
    assert musteri.bakiye_kurus == 70000  # Kalan borç: 700,00 TL


def test_yedekleme_ve_geri_yukleme(tmp_path):
    db_file = tmp_path / "yedek_orijinal.db"
    backup_dir = tmp_path / "backups"
    run_migrations(db_file)

    urun_srv = UrunServisi(db_file)
    urun_srv.urun_ekle(Urun(id=None, parca_kodu="YDK-01", ad="Yedek Test Parçası", stok=10))

    yedek_srv = YedekServisi(db_file, backup_dir)

    # Yedek al
    alinan_yedek = yedek_srv.yedek_al()
    assert alinan_yedek.exists()

    # Orijinal veritabanını boz veya sil
    urun_srv.urun_ekle(Urun(id=None, parca_kodu="YDK-02", ad="Yedekten Sonraki Parça", stok=5))
    assert urun_srv.toplam_urun_sayisi() == 2

    # Yedekten geri dön
    yedek_srv.yedekten_geri_yukle(alinan_yedek)

    # Geri dönüldükten sonra yalnızca yedek anındaki 1 ürün olmalı
    assert urun_srv.toplam_urun_sayisi() == 1
    assert urun_srv.urun_getir_parca_kodu("YDK-01") is not None
    assert urun_srv.urun_getir_parca_kodu("YDK-02") is None
