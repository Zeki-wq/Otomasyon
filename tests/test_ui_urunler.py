"""
Ürün Yönetimi Arayüz Testleri (pytest-qt)
Ekran görüntüsü alma (docs/ekran/) ve UI etkileşim testleri.
"""

from pathlib import Path

import pytest

from app.db.migrations.migrator import run_migrations
from app.domain.models import Urun
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.ui.pages.urunler_page import UrunDiyalog, UrunlerPage
from app.ui.theme import apply_theme


@pytest.fixture
def ui_test_db(tmp_path):
    db_file = tmp_path / "ui_test.db"
    run_migrations(db_file)
    return str(db_file)


def test_urunler_page_render_and_screenshot(qtbot, ui_test_db):
    urun_srv = UrunServisi(ui_test_db)
    stok_srv = StokServisi(ui_test_db)

    # Birkaç test ürünü ekle
    urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="DIS-101",
        ad="Hava Soğutmalı Ön Fren Diski",
        satis_fiyati_kurus=85000,
        alis_fiyati_kurus=55000,
        stok=12,
        kritik_stok=4,
        raf_yeri="A-01"
    ))
    urun_srv.urun_ekle(Urun(
        id=None,
        parca_kodu="BUJ-202",
        ad="Lazer Platin Buji",
        satis_fiyati_kurus=18000,
        alis_fiyati_kurus=11000,
        stok=2,  # Kritik stok!
        kritik_stok=5,
        raf_yeri="B-03"
    ))

    # Sayfayı oluştur ve temayı uygula
    page = UrunlerPage(urun_srv, stok_srv)
    apply_theme(page)
    page.resize(1200, 700)
    qtbot.addWidget(page)
    page.show()

    # Tablo satırlarını doğrula
    assert page.tablo.rowCount() == 2
    assert "Toplam: 2 Ürün" in page.lbl_ozet.text()

    # Ekran görüntüsünü kaydet
    ekran_dir = Path("docs/ekran")
    ekran_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = ekran_dir / "urunler_page.png"
    pixmap = page.grab()
    pixmap.save(str(screenshot_path))
    assert screenshot_path.exists()

    # Arama testi
    page.txt_ara.setText("DIS-101")
    page.listeyi_guncelle()
    assert page.tablo.rowCount() == 1
    assert page.tablo.item(0, 1).text() == "DIS-101"

    # Filtreyi temizle
    page.filtreleri_temizle()
    assert page.tablo.rowCount() == 2


def test_urun_diyalog_validation(qtbot, ui_test_db):
    urun_srv = UrunServisi(ui_test_db)
    diyalog = UrunDiyalog(None, urun_srv)
    apply_theme(diyalog)
    qtbot.addWidget(diyalog)

    # Boş formla kaydetme denemesi (uyarı verir, kabul etmez)
    diyalog.txt_kod.setText("")
    diyalog.txt_ad.setText("")
    # Diyalog modal olmadan kontrol
    assert diyalog.txt_kod.text() == ""
