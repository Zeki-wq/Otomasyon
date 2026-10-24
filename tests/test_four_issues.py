"""
4 Temel Gerçek Kullanım Sorununa Yönelik Regresyon Testleri:
1. Pasife alınan ürün tekrar aktif edilebilmeli, denetim kaydı tutulmalı, satışta filtrelenmeli.
2. Satış ekranında adet artınca satır ve genel toplamlar anında kuruş hassasiyetiyle güncellenmeli.
3. Siparişler ekranında Kalem Sayısı ve Toplam Adet görünmeli, ürün adına göre aranabilmeli, detaydan iptal edilebilmeli.
4. Müşteri formunda TC Kimlik No ve telefon resmi algoritmalarla doğrulanmalı, KVKK maskelemesi yapılmalı.
"""

import pytest

from app.db.migrations.migrator import run_migrations
from app.domain.models import Musteri, Urun
from app.domain.validators import (
    eposta_dogrula,
    tc_kimlik_dogrula,
    tc_maskele,
    telefon_dogrula_ve_normalize,
    vergi_no_dogrula,
)
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi


def test_sorun1_pasif_urun_aktife_alma_ve_denetim(tmp_path):
    """SORUN 1: Pasife alınan ürün aktife alınabilmeli, satışta filtrelenmeli, denetim kaydı yazılmalı."""
    db_path = tmp_path / "test_sorun1.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)

    u_id = us.urun_ekle(Urun(
        id=None,
        parca_kodu="FLT-001",
        ad="Hava Filtresi",
        alis_fiyati_kurus=5000,
        satis_fiyati_kurus=8000,
        stok=25,
        kdv_orani=20
    ), kullanici_id=user.id)

    # 1. Başlangıçta aktif ve satışta aranabilir
    assert us.urun_getir_parca_kodu("FLT-001") is not None
    assert len(us.urun_ara(terim="Hava", sadece_aktif=True)) == 1

    # 2. Pasife al
    assert us.urun_pasife_al(u_id, kullanici_id=user.id) is True
    u_pasif = us.urun_getir(u_id)
    assert u_pasif.aktif == 0

    # Satış aramasında çıkmamalı!
    assert us.urun_getir_parca_kodu("FLT-001") is None
    assert len(us.urun_ara(terim="Hava", sadece_aktif=True)) == 0
    # Pasifleri göster filtresinde çıkmalı
    pasifler = us.urun_ara(terim="Hava", aktiflik_filtresi="pasif")
    assert len(pasifler) == 1

    # 3. Aktife al
    assert us.urun_aktife_al(u_id, kullanici_id=user.id) is True
    u_aktif = us.urun_getir(u_id)
    assert u_aktif.aktif == 1
    assert u_aktif.stok == 25  # Stok bozulmamış olmalı

    # Satışta tekrar görünmeli
    assert us.urun_getir_parca_kodu("FLT-001") is not None
    assert len(us.urun_ara(terim="Hava", sadece_aktif=True)) == 1

    # 4. Denetim log ve stok hareket kaydı oluşmuş olmalı
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT islem, detay FROM denetim_log WHERE kullanici_id = ?", (user.id,))
    loglar = cur.fetchall()
    islemler = [item[0] for item in loglar]
    assert "urun_pasife_al" in islemler
    assert "urun_aktife_al" in islemler

    cur.execute("SELECT hareket_tipi, referans_tipi, onceki_stok, sonraki_stok FROM stok_hareket WHERE urun_id = ?", (u_id,))
    hareketler = cur.fetchall()
    ref_tipleri = [h[1] for h in hareketler]
    assert "urun_durum" in ref_tipleri
    conn.close()


def test_sorun2_satis_sepet_hesapla_ve_adet_artisi(tmp_path):
    """SORUN 2: 1 ürün x 40 adet ve çoklu ürünlerde satır ve genel toplamlar kuruş hassasiyetiyle doğru hesaplanmalı."""
    db_path = tmp_path / "test_sorun2.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)

    u1_id = us.urun_ekle(Urun(id=None, parca_kodu="D-01", ad="Disk", satis_fiyati_kurus=15000, stok=100, kdv_orani=20))
    u2_id = us.urun_ekle(Urun(id=None, parca_kodu="B-01", ad="Balata", satis_fiyati_kurus=8000, stok=100, kdv_orani=20))
    u3_id = us.urun_ekle(Urun(id=None, parca_kodu="Y-01", ad="Yag", satis_fiyati_kurus=50000, stok=100, kdv_orani=20))

    # 1. 1 ürün x 40 adet hesaplaması
    hesap = satis.sepet_hesapla([
        {"urun_id": u1_id, "adet": 40, "birim_fiyat_kurus": 15000, "kdv_orani": 20}
    ])
    # 40 * 150,00 TL = 6.000,00 TL (600.000 kuruş) matrah
    # %20 KDV = 1.200,00 TL (120.000 kuruş)
    # Genel Toplam = 7.200,00 TL (720.000 kuruş)
    assert hesap["toplam_matrah"] == 600000
    assert hesap["toplam_kdv"] == 120000
    assert hesap["genel_toplam_kurus"] == 720000
    assert hesap["kalemler"][0]["satir_toplam_kurus"] == 720000

    # 2. 3 farklı ürünlü sepet hesaplaması
    sepet = [
        {"urun_id": u1_id, "adet": 40, "birim_fiyat_kurus": 15000, "kdv_orani": 20},
        {"urun_id": u2_id, "adet": 2, "birim_fiyat_kurus": 8000, "kdv_orani": 20},
        {"urun_id": u3_id, "adet": 1, "birim_fiyat_kurus": 50000, "kdv_orani": 20},
    ]
    hesap3 = satis.sepet_hesapla(sepet)
    # Matrah: 600.000 + 16.000 + 50.000 = 666.000 kuruş
    # KDV: 120.000 + 3.200 + 10.000 = 133.200 kuruş
    # Genel Toplam: 799.200 kuruş
    assert hesap3["toplam_matrah"] == 666000
    assert hesap3["toplam_kdv"] == 133200
    assert hesap3["genel_toplam_kurus"] == 799200

    # 3. Sipariş oluşturma ve veritabanı doğrulaması
    sip = satis.siparis_olustur(sepet, kullanici_id=user.id)
    assert sip.ara_toplam_kurus == 666000
    assert sip.kdv_toplam_kurus == 133200
    assert sip.genel_toplam_kurus == 799200

    # Stok düşümü doğrulaması: 100 - 40 = 60
    u1_sonra = us.urun_getir(u1_id)
    assert u1_sonra.stok == 60

    # 4. Stok fazlası satış reddedilmeli
    with pytest.raises(ValueError, match="Yetersiz stok"):
        satis.siparis_olustur([{"urun_id": u1_id, "adet": 65, "birim_fiyat_kurus": 15000, "kdv_orani": 20}])


def test_sorun3_siparisler_sayfasi_kalem_ve_adet_gosterimi(tmp_path):
    """SORUN 3: Sipariş listesinde Kalem Sayısı ve Toplam Adet gösterilmeli, ürün adıyla arama yapılabilmeli."""
    db_path = tmp_path / "test_sorun3.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)

    u1 = us.urun_ekle(Urun(id=None, parca_kodu="BAL-01", ad="Ön Fren Balatası", satis_fiyati_kurus=1000, stok=50))
    u2 = us.urun_ekle(Urun(id=None, parca_kodu="FLT-02", ad="Yağ Filtresi Mann", satis_fiyati_kurus=2000, stok=50))
    u3 = us.urun_ekle(Urun(id=None, parca_kodu="BUJ-03", ad="İridyum Buji", satis_fiyati_kurus=3000, stok=50))

    # 3 kalem, toplam 2 + 5 + 1 = 8 adet
    kalemler = [
        {"urun_id": u1, "adet": 2, "birim_fiyat_kurus": 1000, "kdv_orani": 20},
        {"urun_id": u2, "adet": 5, "birim_fiyat_kurus": 2000, "kdv_orani": 20},
        {"urun_id": u3, "adet": 1, "birim_fiyat_kurus": 3000, "kdv_orani": 20},
    ]
    sip = satis.siparis_olustur(kalemler, kullanici_id=user.id)

    # Listeleme kontrolü
    siparisler = satis.siparisleri_getir()
    assert len(siparisler) == 1
    s = siparisler[0]
    assert s.kalem_sayisi == 3
    assert s.toplam_adet == 8

    # Ürün adıyla filtreleme kontrolü
    filtre_sonuc = satis.siparisleri_getir(urun_ara="Filtresi")
    assert len(filtre_sonuc) == 1

    filtre_bos = satis.siparisleri_getir(urun_ara="OlmayanUrun")
    assert len(filtre_bos) == 0


def test_sorun4_tc_ve_telefon_dogrulama():
    """SORUN 4: TC Kimlik algoritması, telefon normalizasyonu, Vergi No ve KVKK maskeleme kuralları."""
    # 1. TC Kimlik Doğrulama
    assert tc_kimlik_dogrula("10000000146") is True  # Geçerli resmi algoritma
    assert tc_kimlik_dogrula("") is True  # Boş TC kabul edilir
    assert tc_kimlik_dogrula(None) is True

    assert tc_kimlik_dogrula("01234567890") is False  # 0 ile başlayamaz
    assert tc_kimlik_dogrula("123456789") is False  # 11 haneden az
    assert tc_kimlik_dogrula("123456789012") is False  # 11 haneden fazla
    assert tc_kimlik_dogrula("1000000014A") is False  # Harf içeremez
    assert tc_kimlik_dogrula("11111111111") is False  # Algoritma geçersiz

    # 2. KVKK Maskeleme
    assert tc_maskele("10000000146") == "100******46"
    assert tc_maskele("") == ""

    # 3. Telefon Doğrulama ve Normalizasyon
    assert telefon_dogrula_ve_normalize("0532 123 45 67") == "05321234567"
    assert telefon_dogrula_ve_normalize("+90 532 123 45 67") == "05321234567"
    assert telefon_dogrula_ve_normalize("905321234567") == "05321234567"
    assert telefon_dogrula_ve_normalize("0 (212) 456 78 90") == "02124567890"
    assert telefon_dogrula_ve_normalize("") == ""

    with pytest.raises(ValueError, match="Geçersiz telefon numarası"):
        telefon_dogrula_ve_normalize("12345")

    with pytest.raises(ValueError, match="Geçersiz telefon numarası"):
        telefon_dogrula_ve_normalize("01234567890")  # Türkiye'de 01XX alan kodu yok

    # 4. Vergi No Doğrulama
    assert vergi_no_dogrula("1234567890") is True
    assert vergi_no_dogrula("") is True
    assert vergi_no_dogrula("12345") is False
    assert vergi_no_dogrula("12345678901") is False

    # 5. E-Posta Doğrulama
    assert eposta_dogrula("info@ornek.com") is True
    assert eposta_dogrula("") is True
    assert eposta_dogrula("hatali_eposta") is False


def test_sorun1_ui_pasif_urun_aktife_alma(qtbot, tmp_path, monkeypatch):
    """SORUN 1 UI Testi: Ürünler sayfasında pasif filtreleme, satır durumu ve aktife alma butonu."""
    from PySide6.QtWidgets import QMessageBox

    from app.ui.pages.urunler_page import UrunlerPage

    db_path = tmp_path / "test_ui_sorun1.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    admin_user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    ss = StokServisi(db_path)

    u_id = us.urun_ekle(Urun(id=None, parca_kodu="PRC-100", ad="Debriyaj Seti", alis_fiyati_kurus=50000, satis_fiyati_kurus=80000, stok=10))

    page = UrunlerPage(us, ss, aktif_kullanici=admin_user)
    qtbot.addWidget(page)
    page.show()

    # 1. Başlangıçta 1 ürün var
    assert page.tablo.rowCount() == 1
    assert "✅ Aktif" in page.tablo.item(0, 12).text()

    # 2. Pasife al
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    page.tablo.selectRow(0)
    page.urun_pasife_al()

    # Aktif filtresinde artık görünmemeli
    assert page.tablo.rowCount() == 0

    # 3. 'Yalnızca Pasifler' filtresine geç
    page.cmb_aktiflik.setCurrentIndex(1)  # pasif
    assert page.tablo.rowCount() == 1
    assert "⛔ Pasif" in page.tablo.item(0, 12).text()

    # 4. Pasif ürün seçildiğinde 'Aktife Al' butonu görünmeli
    page.tablo.selectRow(0)
    assert page.btn_aktife_al.isVisible() is True
    assert page.btn_sil.isVisible() is False

    # 5. Aktife al butonuna bas
    page.urun_aktife_al()

    # Pasif listesinde kalmamalı
    assert page.tablo.rowCount() == 0

    # Tekrar aktif listesine geç
    page.cmb_aktiflik.setCurrentIndex(0)
    assert page.tablo.rowCount() == 1
    assert "✅ Aktif" in page.tablo.item(0, 12).text()
    page.close()


def test_sorun2_ui_satis_sayfasi_adet_artisi_ve_anlik_guncelleme(qtbot, tmp_path, monkeypatch):
    """SORUN 2 UI Testi: Sepette adet 1'den 40'a çıkarılınca satır ve genel toplamlar anında güncellenmeli."""
    from PySide6.QtWidgets import QMessageBox

    from app.ui.pages.satis_page import SatisPage

    db_path = tmp_path / "test_ui_sorun2.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)
    ms = MusteriServisi(db_path)

    # 100 stok, 100,00 TL satış fiyatı (%20 KDV dahil 120,00 TL)
    u_id = us.urun_ekle(Urun(id=None, parca_kodu="DSK-200", ad="Brembo Disk", alis_fiyati_kurus=6000, satis_fiyati_kurus=10000, stok=100, kdv_orani=20))

    page = SatisPage(satis, us, ms, aktif_kullanici=user)
    qtbot.addWidget(page)
    page.show()

    # 1. Barkodla 1 adet ekle
    page.txt_barkod_ara.setText("DSK-200")
    page.urun_hizli_bul_ve_ekle()

    assert page.tablo_sepet.rowCount() == 1
    # 1 adet için: Matrah 100 TL, KDV 20 TL, Toplam 120,00 TL
    assert "120,00 ₺" in page.tablo_sepet.item(0, 7).text()
    assert "100,00 ₺" in page.lbl_ara_toplam.text()
    assert "20,00 ₺" in page.lbl_kdv_toplam.text()
    assert "120,00 ₺" in page.lbl_genel_toplam.text()

    # 2. Adedi 40 yap (Hücre spinbox veya fonksiyon üzerinden)
    page.sepet_adet_degisti(0, 40)

    # 40 adet için: Matrah 4.000,00 TL, KDV 800,00 TL, Genel Toplam 4.800,00 TL
    assert "4.800,00 ₺" in page.tablo_sepet.item(0, 7).text()
    assert "4.000,00 ₺" in page.lbl_ara_toplam.text()
    assert "800,00 ₺" in page.lbl_kdv_toplam.text()
    assert "4.800,00 ₺" in page.lbl_genel_toplam.text()

    # 3. Satışı onayla
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    page.satisi_tamamla()

    # Sepet boşalmış olmalı
    assert page.tablo_sepet.rowCount() == 0
    # Stok 100 - 40 = 60'a düşmüş olmalı
    assert us.urun_getir(u_id).stok == 60

    # 4. Adet 0 olunca satırın otomatik silinmesi kontrolü
    page.txt_barkod_ara.setText("DSK-200")
    page.urun_hizli_bul_ve_ekle()
    assert page.tablo_sepet.rowCount() == 1
    page.sepet_adet_degisti(0, 0)
    assert page.tablo_sepet.rowCount() == 0

    page.close()


def test_sorun3_ui_siparisler_sayfasi_ve_detay_iptal(qtbot, tmp_path, monkeypatch):
    """SORUN 3 UI Testi: Siparişler tablosunda Kalem/Toplam Adet sütunları, ürün araması ve detaydan iptal."""
    from PySide6.QtWidgets import QMessageBox

    from app.ui.pages.siparisler_page import SiparisDetayDiyalog, SiparislerPage

    db_path = tmp_path / "test_ui_sorun3.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    us = UrunServisi(db_path)
    satis = SatisServisi(db_path)
    ms = MusteriServisi(db_path)

    u1 = us.urun_ekle(Urun(id=None, parca_kodu="PRC-A", ad="Ateşleme Bobini", satis_fiyati_kurus=5000, stok=50))
    u2 = us.urun_ekle(Urun(id=None, parca_kodu="PRC-B", ad="Hava Filtresi Bosch", satis_fiyati_kurus=3000, stok=50))

    satis.siparis_olustur([
        {"urun_id": u1, "adet": 3, "birim_fiyat_kurus": 5000, "kdv_orani": 20},
        {"urun_id": u2, "adet": 4, "birim_fiyat_kurus": 3000, "kdv_orani": 20},
    ], kullanici_id=user.id)

    page = SiparislerPage(satis, ms, aktif_kullanici=user)
    qtbot.addWidget(page)
    page.show()

    # 1. 11 sütun ve Kalem/Adet değerleri
    assert page.tablo.columnCount() == 11
    assert page.tablo.rowCount() == 1
    assert page.tablo.item(0, 4).text() == "2"  # Kalem sayısı
    assert page.tablo.item(0, 5).text() == "7"  # Toplam adet (3+4)

    # 2. Ürün araması filtresi
    page.txt_urun_ara.setText("Bobini")
    assert page.tablo.rowCount() == 1

    page.txt_urun_ara.setText("OlmayanUrun")
    assert page.tablo.rowCount() == 0
    page.txt_urun_ara.clear()

    # 3. Detay penceresi ve iptal butonu testi
    sip = satis.siparisleri_getir()[0]
    detay_dlg = SiparisDetayDiyalog(sip, satis_servisi=satis, aktif_kullanici=user)
    qtbot.addWidget(detay_dlg)
    detay_dlg.show()

    assert detay_dlg.btn_iptal.isEnabled() is True
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    detay_dlg.siparis_iptal_et()

    # Sipariş iptal edildi, stoklar iade alındı
    sip_sonra = satis.siparis_detay_getir(sip.id)
    assert sip_sonra.durum == "iptal"
    assert us.urun_getir(u1).stok == 50
    assert us.urun_getir(u2).stok == 50

    detay_dlg.close()
    page.close()


def test_sorun4_ui_musteri_tc_maskeleme_ve_uyari_rozeti(qtbot, tmp_path):
    """SORUN 4 UI Testi: Müşteri listesinde KVKK maskelemesi, geçersiz TC rozeti ve formatlı telefon."""
    from app.ui.pages.musteriler_page import MusterilerPage

    db_path = tmp_path / "test_ui_sorun4.db"
    run_migrations(db_path)

    ms = MusteriServisi(db_path)

    # 1. Geçerli TC ve telefonlu müşteri
    ms.musteri_ekle(Musteri(id=None, ad_soyad="Ali Veli", telefon="05321234567", vergi_no_tc="10000000146"))

    # 2. Eski veritabanından kalmış geçersiz TC'li müşteri (direkt DB insert ile)
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO musteri (ad_soyad, telefon, vergi_no_tc, aktif) VALUES ('Hatalı Müşteri', '05559998877', '11111111111', 1)")
    conn.commit()
    conn.close()

    page = MusterilerPage(ms)
    qtbot.addWidget(page)
    page.show()

    assert page.tablo.rowCount() == 2

    # Satır 0: Geçerli müşteri -> TC maskeli görünmeli ("100******46")
    tc_0 = page.tablo.item(0, 4).text()
    assert tc_0 == "100******46"
    assert "Geçersiz" not in tc_0

    # Satır 1: Geçersiz TCKN'li müşteri -> Maskeli + "Geçersiz TC" rozeti olmalı
    tc_1 = page.tablo.item(1, 4).text()
    assert "111******11" in tc_1
    assert "Geçersiz TC" in tc_1

    # Telefon format kontrolü
    assert page.tablo.item(0, 2).text() == "0532 123 45 67"

    page.close()

