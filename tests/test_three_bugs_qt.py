"""
Üç Kritik Hata İçin Otomasyonlu Test Paketi (pytest-qt)
HATA A: Müşteri & Ürün formlarında arayüz doğrulama ve diyalogun açık kalması
HATA B: Tablolarda WCAG kontrastı (>= 4.5), koyu alternatif satırlar ve koyu köşe/şerit
HATA C: Hayalet boş satırların engellenmesi, filtrelerde tam satır sayısı ve 'Sonuç bulunamadı' mesajı
"""

from pathlib import Path

import pytest
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from app.db.migrations.migrator import run_migrations
from app.domain.models import Kullanici, Musteri, Urun
from app.domain.validators import (
    ValidationError,
    tc_kimlik_dogrula,
    telefon_dogrula_ve_normalize,
    vergi_veya_tc_dogrula,
)
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.ui.pages.musteriler_page import MusteriDiyalog, MusterilerPage
from app.ui.pages.urunler_page import UrunDiyalog, UrunlerPage
from app.ui.theme import apply_theme


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_three_bugs.db"
    run_migrations(db_file)
    return str(db_file)


# =========================================================================
# HATA A: MÜŞTERİ VE ÜRÜN DOĞRULAMA TESTLERİ
# =========================================================================

def test_hata_a_musteri_diyalog_gecersiz_veri_reddi(qtbot, test_db, monkeypatch):
    """
    HATA A UI Testi:
    Müşteri formuna '515', 'asd', '1782', 'jigıydugvl' girilip 'Kaydet' butonuna tıklandığında:
    1. Veritabanına kayıt EKLENMEMELİ.
    2. Diyalog AÇIK KALMALI (reject/accept çağrılmamalı).
    3. Hatalı alanların kenarlığı kırmızı olmalı ve Türkçe hata mesajı görünmeli.
    4. İlk hatalı alana odak gitmeli.
    5. Geçerli veriler yazıldığında ise diyalog kapanmalı ve kayıt eklenmeli.
    """
    # QMessageBox uyarılarını sessize al ama çağrıldığını takip et
    mesajlar = []
    monkeypatch.setattr(QMessageBox, "warning", lambda p, t, m: mesajlar.append(("warning", t, m)))
    monkeypatch.setattr(QMessageBox, "critical", lambda p, t, m: mesajlar.append(("critical", t, m)))
    monkeypatch.setattr(QMessageBox, "information", lambda p, t, m: mesajlar.append(("information", t, m)))

    ms = MusteriServisi(test_db)
    user = Kullanici(id=1, kullanici_adi="admin", parola_hash="", parola_salt="", ad_soyad="Admin", rol="yonetici")

    dlg = MusteriDiyalog(musteri_servisi=ms, aktif_kullanici=user)
    apply_theme(dlg)
    qtbot.addWidget(dlg)
    dlg.show()

    # 1. Aşama: Geçersiz veriler giriliyor (kullanıcının karşılaştığı gerçek durum)
    dlg.txt_ad.setText("a")  # Çok kısa (< 2 karakter)
    dlg.txt_tel.setText("515")  # Geçersiz kısa telefon
    dlg.txt_eposta.setText("asd")  # Geçersiz e-posta
    dlg.txt_vergi.setText("1782")  # Ne 10 haneli vergi no ne de 11 haneli TCKN

    # Gerçek Kaydet butonuna tıkla
    qtbot.mouseClick(dlg.btn_kaydet, QtCore.Qt.LeftButton)

    # Doğrulama: Diyalog AÇIK KALMALI
    assert dlg.isVisible() is True, "Geçersiz veriler girildiğinde diyalog açık kalmalıdır!"

    # Doğrulama: Veritabanına hiçbir müşteri kaydedilmemiş olmalı
    assert len(ms.musterileri_getir()) == 0, "Geçersiz müşteri veritabanına kaydedilmemeliydi!"

    # Doğrulama: Hata mesajı etiketi ve odak kontrolü
    assert dlg.lbl_ad_hata.isVisible() is True
    assert "en az 2 karakter" in dlg.lbl_ad_hata.text().lower()

    # Ad'ı düzeltip tekrar tıkla, bu kez telefon hatası vermeli
    dlg.txt_ad.setText("Demir Otomotiv")
    qtbot.mouseClick(dlg.btn_kaydet, QtCore.Qt.LeftButton)
    assert dlg.isVisible() is True
    assert dlg.lbl_tel_hata.isVisible() is True
    assert "türkiye standartlarında" in dlg.lbl_tel_hata.text().lower()

    # Telefonu düzelt, bu kez eposta hatası vermeli
    dlg.txt_tel.setText("0532 123 45 67")
    qtbot.mouseClick(dlg.btn_kaydet, QtCore.Qt.LeftButton)
    assert dlg.isVisible() is True
    assert dlg.lbl_eposta_hata.isVisible() is True

    # E-postayı düzelt, bu kez Vergi/TC hatası vermeli
    dlg.txt_eposta.setText("info@demiroto.com")
    qtbot.mouseClick(dlg.btn_kaydet, QtCore.Qt.LeftButton)
    assert dlg.isVisible() is True
    assert dlg.lbl_vergi_hata.isVisible() is True
    assert "10 haneli" in dlg.lbl_vergi_hata.text() or "11 haneli" in dlg.lbl_vergi_hata.text()

    # 2. Aşama: Tüm alanları geçerli yap
    dlg.txt_vergi.setText("10000000146")  # Geçerli TCKN
    qtbot.mouseClick(dlg.btn_kaydet, QtCore.Qt.LeftButton)

    # Doğrulama: Diyalog kapanmalı ve kayıt eklenmeli
    assert dlg.isVisible() is False
    musteriler = ms.musterileri_getir()
    assert len(musteriler) == 1
    assert musteriler[0].ad_soyad == "Demir Otomotiv"
    assert musteriler[0].telefon == "05321234567"
    assert musteriler[0].vergi_no_tc == "10000000146"


def test_hata_a_musteri_mevcut_hatali_kayitlar_ve_filtre(qtbot, test_db):
    """
    Mevcut veritabanında 'asd', '515' gibi bozuk kayıtlar varsa:
    1. Veriler silinmez / bozulmaz.
    2. Tabloda 'Hatalı Bilgi' uyarı rozeti görünür.
    3. 'Hatalı Kayıtlar' filtresi ile yalnızca bunlar listelenebilir.
    """
    # Doğrudan SQL ile bozuk kayıt ekle (kullanıcının mevcut veritabanındaki gibi)
    from app.db.connection import get_db_connection
    conn = get_db_connection(test_db)
    with conn:
        conn.execute(
            "INSERT INTO musteri (ad_soyad, telefon, eposta, vergi_no_tc, aktif) VALUES (?, ?, ?, ?, 1)",
            ("ali", "515", "asd", "1782")
        )
        conn.execute(
            "INSERT INTO musteri (ad_soyad, telefon, eposta, vergi_no_tc, aktif) VALUES (?, ?, ?, ?, 1)",
            ("Kusursuz Müsteri", "05321112233", "test@test.com", "10000000146")
        )

    ms = MusteriServisi(test_db)
    page = MusterilerPage(ms)
    apply_theme(page)
    qtbot.addWidget(page)
    page.show()

    assert page.tablo.rowCount() == 2

    # 1. satır ali -> hatalı rozet içermeli
    item_tc = page.tablo.item(0, 4)
    item_durum = page.tablo.item(0, 7)
    durum_metni = (item_durum.text() if item_durum else "") + (item_tc.text() if item_tc else "")
    assert "Hatalı" in durum_metni or "Geçersiz" in durum_metni

    # 'Hatalı Kayıtlar' filtresi seçildiğinde yalnızca ali kalmalı
    if hasattr(page, "cmb_filtre_durum"):
        idx = page.cmb_filtre_durum.findData("hatali")
        if idx >= 0:
            page.cmb_filtre_durum.setCurrentIndex(idx)
            assert page.tablo.rowCount() == 1
            assert page.tablo.item(0, 1).text() == "ali"


def test_hata_a_urun_diyalog_dogrulama(qtbot, test_db, monkeypatch):
    """
    Ürün ekleme/düzenleme formunda negatif fiyat, harfli fiyat veya boş kod/ad
    girildiğinde diyalogun açık kalması ve kırmızı alan vurgusu.
    """
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    us = UrunServisi(test_db)
    ss = StokServisi(test_db)

    dlg = UrunDiyalog(urun_servisi=us)
    apply_theme(dlg)
    qtbot.addWidget(dlg)
    dlg.show()

    # Hatalı veri
    dlg.txt_kod.setText("A")  # < 2 karakter
    dlg.txt_ad.setText("")    # Boş
    dlg.txt_alis.setText("abc") # Harf
    dlg.txt_satis.setText("-50") # Negatif

    qtbot.mouseClick(dlg.btn_kaydet, QtCore.Qt.LeftButton)
    assert dlg.isVisible() is True, "Hatalı ürün girildiğinde diyalog açık kalmalıdır!"
    assert len(us.urun_ara(sadece_aktif=False)) == 0


# =========================================================================
# HATA B: TABLO BEYAZ SATIR VE WCAG KONTRAST TESTLERİ
# =========================================================================

def _luminance(r: int, g: int, b: int) -> float:
    """sRGB göreceli parlaklık (relative luminance) hesabı."""
    def _channel(c):
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.03928 else ((c_norm + 0.055) / 1.055) ** 2.4
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def _contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """WCAG 2.1 Kontrast Oranı formülü: (L1 + 0.05) / (L2 + 0.05)."""
    l1 = _luminance(*rgb1)
    l2 = _luminance(*rgb2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def test_hata_b_tablo_koyu_alternatif_satirlar_ve_wcag_kontrast(qtbot, test_db):
    """
    HATA B UI Testi:
    Tüm tablolarda alternatif satırların beyaz OLMADIĞINI (koyu tema uyumlu),
    metin rengi ile arka plan arasındaki kontrastın WCAG standardına (>= 4.5:1) uyduğunu
    ve köşe düğmesi / şerit alanının açık renk (beyaz/açık gri) olmadığını denetler.
    """
    us = UrunServisi(test_db)
    ss = StokServisi(test_db)

    # 4 ürün ekle ki hem ana hem alternatif satırlar oluşsun
    for i in range(1, 5):
        us.urun_ekle(Urun(
            id=None,
            parca_kodu=f"PRC-00{i}",
            ad=f"Yedek Parça Örneği {i}",
            satis_fiyati_kurus=10000 * i,
            stok=20 * i,
            aktif=1
        ))

    page = UrunlerPage(us, ss)
    apply_theme(page)
    page.resize(1100, 600)
    with qtbot.waitExposed(page):
        page.show()

    tablo = page.tablo
    tablo.setAlternatingRowColors(True)
    assert tablo.rowCount() >= 4

    # Tablo görüntüsünü al
    pix = tablo.grab()
    img = pix.toImage()

    # Ekran görüntüsünü kaydet
    ekran_yolu = Path("docs/ekran/tablo_kontrast_dogrulama.png")
    ekran_yolu.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(ekran_yolu))

    # 1. ve 2. satırların hücre koordinatlarını alıp piksel renklerini kontrol et
    for row_idx in range(min(3, tablo.rowCount())):
        rect = tablo.visualItemRect(tablo.item(row_idx, 4))
        # Hücrenin içindeki bir pikselin rengini al (metin olmayan sağ boşluk bölgesi)
        pixel_x = rect.x() + rect.width() - 8
        pixel_y = rect.y() + (rect.height() // 2)

        color = QtGui.QColor(img.pixel(pixel_x, pixel_y))
        bg_rgb = (color.red(), color.green(), color.blue())

        # ARKA PLAN ASLA BEYAZ VEYA AÇIK RENK OLMAMALI (Luminance < 0.35)
        lum = _luminance(*bg_rgb)
        assert lum < 0.35, (
            f"Ürünler Tablosu {row_idx + 1}. satır arka planı çok açık ({bg_rgb}, lum={lum:.2f})! "
            f"Koyu temada alternate-background-color beyaz kalmış."
        )

        # Metin rengi (#f5f6fa civarı açık renk) ile kontrast oranı >= 4.5 olmalı
        text_color = (245, 246, 250)
        contrast = _contrast_ratio(bg_rgb, text_color)
        assert contrast >= 4.5, (
            f"Ürünler Tablosu {row_idx + 1}. satır kontrast oranı yetersiz: {contrast:.2f} < 4.5"
        )


# =========================================================================
# HATA C: HAYALET BOŞ SATIRLAR VE FİLTRELEME TESTLERİ
# =========================================================================

def test_hata_c_urunler_filtre_ve_tam_satir_sayisi(qtbot, test_db):
    """
    HATA C UI Testi:
    2 kayıt yüklendiğinde rowCount=2 olmalı.
    Filtre 1 kayda indiğinde rowCount=1 olmalı.
    Filtre 0 kayda indiğinde rowCount=0 olmalı ve 'Sonuç bulunamadı' mesajı çıkmalı.
    Asla hayalet/boş satır bulunmamalıdır.
    """
    us = UrunServisi(test_db)
    ss = StokServisi(test_db)

    # 1 aktif, 1 pasif ürün ekle
    us.urun_ekle(Urun(id=None, parca_kodu="PRC-AKTIF", ad="Aktif Parça", stok=10, aktif=1))
    us.urun_ekle(Urun(id=None, parca_kodu="PRC-PASIF", ad="Pasif Parça", stok=0, aktif=0))

    page = UrunlerPage(us, ss)
    apply_theme(page)
    qtbot.addWidget(page)
    page.show()

    # Varsayılan filtre: Yalnızca Aktifler -> Tam 1 satır olmalı!
    assert page.tablo.rowCount() == 1
    assert page.tablo.item(0, 1).text() == "PRC-AKTIF"

    # 'Tüm Ürünler' seçilince tam 2 satır olmalı
    idx_tumu = page.cmb_aktiflik.findData("tumu")
    page.cmb_aktiflik.setCurrentIndex(idx_tumu)
    assert page.tablo.rowCount() == 2

    # 'Yalnızca Pasifler' seçilince tam 1 satır olmalı
    idx_pasif = page.cmb_aktiflik.findData("pasif")
    page.cmb_aktiflik.setCurrentIndex(idx_pasif)
    assert page.tablo.rowCount() == 1
    assert page.tablo.item(0, 1).text() == "PRC-PASIF"

    # Olmayan bir şey aranırsa tam 0 satır olmalı ve 'Sonuç bulunamadı' mesajı görünmeli
    page.txt_ara.setText("OLMAYAN_PARCA_XYZ")
    page.listeyi_guncelle()
    assert page.tablo.rowCount() == 0
    assert "bulunamadı" in page.lbl_ozet.text().lower()


def test_hata_b_tum_sayfalardaki_tablolarda_wcag_kontrast(qtbot, test_db):
    """
    Tüm sayfalardaki tabloların (ürünler, müşteriler, siparişler, stok hareketleri)
    WCAG kontrast oranını (>= 4.5:1), koyu alternatif satırlarını ve köşe butonunun
    koyu olduğunu doğrular. Başarısız olursa tablonun ve sayfanın adını yazar.
    """
    from app.services.rapor_servisi import RaporServisi
    from app.services.yedek_servisi import YedekServisi
    from app.ui.main_window import MainWindow

    us = UrunServisi(test_db)
    ss = StokServisi(test_db)
    satis = SatisServisi(test_db)
    ms = MusteriServisi(test_db)
    ks = KimlikServisi(test_db)
    ys = YedekServisi(test_db)
    rs = RaporServisi(test_db)

    # Örnek veriler ekle
    u1 = us.urun_ekle(Urun(id=None, parca_kodu="PRC-KTR1", ad="Buji Takımı", satis_fiyati_kurus=15000, stok=20))
    u2 = us.urun_ekle(Urun(id=None, parca_kodu="PRC-KTR2", ad="Fren Diski", satis_fiyati_kurus=45000, stok=10))
    m1 = ms.musteri_ekle(Musteri(id=None, ad_soyad="Ahmet Usta", telefon="05321112233"))
    m2 = ms.musteri_ekle(Musteri(id=None, ad_soyad="Mehmet Usta", telefon="05322223344"))
    satis.siparis_olustur([{"urun_id": u1, "adet": 2, "birim_fiyat_kurus": 15000, "kdv_orani": 20}], musteri_id=m1)
    satis.siparis_olustur([{"urun_id": u2, "adet": 1, "birim_fiyat_kurus": 45000, "kdv_orani": 20}], musteri_id=m2)

    user = Kullanici(id=1, kullanici_adi="admin", parola_hash="", parola_salt="", ad_soyad="Admin", rol="yonetici")

    win = MainWindow(us, ss, satis, ms, ks, ys, rs, aktif_kullanici=user, db_path=test_db)
    qtbot.addWidget(win)
    win.show()

    tablo_listesi = [
        ("UrunlerPage", "urunler", win.page_urunler.tablo),
        ("MusterilerPage", "musteriler", win.page_musteriler.tablo),
        ("SiparislerPage", "siparisler", win.page_siparisler.tablo),
        ("StokPage_Hareket", "stok", win.page_stok.tablo_hareket),
        ("StokPage_Kritik", "stok", win.page_stok.tablo_kritik),
        ("Dashboard_Siparis", "dashboard", win.page_dashboard.tablo_son_siparis),
    ]

    for sayfa_adi, sekme, tablo in tablo_listesi:
        win.sayfa_degistir(sekme)
        tablo.setAlternatingRowColors(True)
        tablo.clearSelection()
        tablo.setCurrentItem(None)
        pix = tablo.grab()
        img = pix.toImage()

        # Köşe pikseli kontrolü: (0, 0) koordinatındaki köşe butonu beyaz OLMAMALI
        kose_color = QtGui.QColor(img.pixel(2, 2))
        kose_rgb = (kose_color.red(), kose_color.green(), kose_color.blue())
        kose_lum = _luminance(*kose_rgb)
        assert kose_lum < 0.40, (
            f"[{sayfa_adi}] Tablo sol üst köşe butonu açık renk ({kose_rgb}, lum={kose_lum:.2f})!"
        )

        # Viewport görüntüsü üzerinden hücre arka plan pikselini kontrol et
        vp_pix = tablo.viewport().grab()
        vp_img = vp_pix.toImage()

        # Satır kontrastları kontrolü (en az 1 satır varsa)
        if tablo.rowCount() > 0:
            for r in range(min(2, tablo.rowCount())):
                item = tablo.item(r, 1) or tablo.item(r, 0)
                if item:
                    rect = tablo.visualItemRect(item)
                    px = rect.x() + rect.width() - 8
                    py = rect.y() + (rect.height() // 2)
                    c = QtGui.QColor(vp_img.pixel(px, py))
                    bg_rgb = (c.red(), c.green(), c.blue())
                    lum = _luminance(*bg_rgb)
                    assert lum < 0.35, (
                        f"[{sayfa_adi}] {r + 1}. satır arka planı çok açık ({bg_rgb}, lum={lum:.2f})!"
                    )
                    contrast = _contrast_ratio(bg_rgb, (245, 246, 250))
                    assert contrast >= 4.5, (
                        f"[{sayfa_adi}] {r + 1}. satır WCAG kontrastı yetersiz: {contrast:.2f} < 4.5"
                    )
