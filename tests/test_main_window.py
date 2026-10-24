"""
Ana Pencere (MainWindow) ve Entegrasyon Arayüz Testleri (pytest-qt)
Tüm sekmeler arası geçiş, ekran görüntüsü alma ve genel arayüz doğrulaması.
"""

from pathlib import Path

import pytest

from app.db.migrations.migrator import run_migrations
from app.domain.models import Kullanici, Urun
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.rapor_servisi import RaporServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.services.yedek_servisi import YedekServisi
from app.ui.main_window import MainWindow


@pytest.fixture
def main_win_db(tmp_path):
    db_file = tmp_path / "main_win_test.db"
    run_migrations(db_file)
    return str(db_file)


def test_main_window_navigation_and_screenshots(qtbot, main_win_db):
    urun_srv = UrunServisi(main_win_db)
    stok_srv = StokServisi(main_win_db)
    satis_srv = SatisServisi(main_win_db)
    musteri_srv = MusteriServisi(main_win_db)
    kimlik_srv = KimlikServisi(main_win_db)
    yedek_srv = YedekServisi(main_win_db)
    rapor_srv = RaporServisi(main_win_db)

    # Örnek veri ekle
    urun_srv.urun_ekle(Urun(id=None, parca_kodu="TEST-01", ad="Deneme Parça", stok=10))

    admin_user = Kullanici(
        id=1,
        kullanici_adi="admin",
        parola_hash="",
        parola_salt="",
        ad_soyad="Ahmet Usta (Dükkan Sahibi)",
        rol="yonetici"
    )

    win = MainWindow(
        urun_servisi=urun_srv,
        stok_servisi=stok_srv,
        satis_servisi=satis_srv,
        musteri_servisi=musteri_srv,
        kimlik_servisi=kimlik_srv,
        yedek_servisi=yedek_srv,
        rapor_servisi=rapor_srv,
        aktif_kullanici=admin_user,
        db_path=main_win_db
    )
    qtbot.addWidget(win)
    win.show()

    ekran_dir = Path("docs/ekran")
    ekran_dir.mkdir(parents=True, exist_ok=True)

    # Ana panel ekran görüntüsü
    win.sayfa_degistir("dashboard")
    win.grab().save(str(ekran_dir / "dashboard_page.png"))
    assert (ekran_dir / "dashboard_page.png").exists()

    # Tam ana pencere görüntüsü
    win.grab().save(str(ekran_dir / "main_window.png"))
    assert (ekran_dir / "main_window.png").exists()

    # Tüm sekmeler arası gezintiyi test et
    sekmeler = ["satis", "urunler", "siparisler", "musteriler", "stok", "raporlar", "ayarlar", "dashboard"]
    for sekme in sekmeler:
        win.sayfa_degistir(sekme)
        assert win.stack.currentWidget() == win.sayfa_haritasi[sekme]
