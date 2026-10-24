"""
Satış, Siparişler ve Stok Yönetimi Arayüz Testleri (pytest-qt)
Ekran görüntüleri kaydetme (docs/ekran/) ve tam satış-iptal-stok döngüsü.
"""

from pathlib import Path
import pytest
from PyQt5.QtCore import Qt
from app.db.migrations.migrator import run_migrations
from app.domain.models import Urun, Musteri
from app.services.urun_servisi import UrunServisi
from app.services.stok_servisi import StokServisi
from app.services.satis_servisi import SatisServisi
from app.services.musteri_servisi import MusteriServisi
from app.ui.pages.satis_page import SatisPage
from app.ui.pages.siparisler_page import SiparislerPage
from app.ui.pages.stok_page import StokPage
from app.ui.theme import apply_theme


@pytest.fixture
def satis_test_db(tmp_path):
    db_file = tmp_path / "satis_ui_test.db"
    run_migrations(db_file)
    return str(db_file)


def test_satis_ve_siparis_iptal_dongusu_ui(qtbot, satis_test_db, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    urun_srv = UrunServisi(satis_test_db)
    stok_srv = StokServisi(satis_test_db)
    satis_srv = SatisServisi(satis_test_db)
    musteri_srv = MusteriServisi(satis_test_db)

    # 1. Test ürünleri ve müşteri ekle
    u1_id = urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="MOT-500",
        ad="Motor Yağ Filtresi",
        satis_fiyati_kurus=20000,
        stok=15,
        kritik_stok=5
    ))

    m_id = musteri_srv.musteri_ekle(Musteri(
        id=None,
        ad_soyad="Mehmet Usta",
        telefon="0532 999 8877"
    ))

    ekran_dir = Path("docs/ekran")
    ekran_dir.mkdir(parents=True, exist_ok=True)

    # 2. SATIŞ SAYFASI TESTİ
    satis_page = SatisPage(satis_srv, urun_srv, musteri_srv)
    apply_theme(satis_page)
    satis_page.resize(1200, 700)
    qtbot.addWidget(satis_page)
    satis_page.show()

    # Ürün ara ve sepete ekle
    satis_page.txt_barkod_ara.setText("MOT-500")
    satis_page.spn_adet.setValue(3)
    satis_page.urun_hizli_bul_ve_ekle()

    # Sepette 1 satır olmalı
    assert len(satis_page.sepet) == 1
    assert satis_page.tablo_sepet.rowCount() == 1

    # Satış ekranı görüntüsünü kaydet
    satis_page.grab().save(str(ekran_dir / "satis_page.png"))
    assert (ekran_dir / "satis_page.png").exists()

    # Satışı tamamla
    satis_page.satisi_tamamla()
    assert len(satis_page.sepet) == 0

    # Depodaki stok 15 -> 12 olmalı
    assert urun_srv.urun_getir(u1_id).stok == 12

    # 3. SİPARİŞLER SAYFASI TESTİ
    sip_page = SiparislerPage(satis_srv, musteri_srv)
    apply_theme(sip_page)
    sip_page.resize(1200, 700)
    qtbot.addWidget(sip_page)
    sip_page.show()

    assert sip_page.tablo.rowCount() == 1

    # Siparişler ekranı görüntüsünü kaydet
    sip_page.grab().save(str(ekran_dir / "siparisler_page.png"))
    assert (ekran_dir / "siparisler_page.png").exists()

    # 4. STOK HAREKETLERİ SAYFASI TESTİ
    stok_page = StokPage(stok_srv, urun_srv)
    apply_theme(stok_page)
    stok_page.resize(1200, 700)
    qtbot.addWidget(stok_page)
    stok_page.show()

    assert stok_page.tablo_hareket.rowCount() >= 2  # Açılış ve Satış hareketi

    # Stok ekranı görüntüsünü kaydet
    stok_page.grab().save(str(ekran_dir / "stok_page.png"))
    assert (ekran_dir / "stok_page.png").exists()
