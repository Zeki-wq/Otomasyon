"""
Faz 4 Arayüz ve Yetkilendirme Testleri (pytest-qt)
Giriş sihirbazı, cari hesaplar, tahsilat, rol kısıtlamaları, yedekleme ve ekran görüntüleri.
"""

from pathlib import Path

import pytest
from PyQt5.QtWidgets import QMessageBox

from app.db.migrations.migrator import run_migrations
from app.domain.models import Kullanici, Musteri
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.yedek_servisi import YedekServisi
from app.ui.pages.ayarlar_page import AyarlarPage
from app.ui.pages.login_dialog import LoginDialog
from app.ui.pages.musteriler_page import MusterilerPage
from app.ui.theme import apply_theme


@pytest.fixture
def faz4_db(tmp_path):
    db_file = tmp_path / "faz4_test.db"
    run_migrations(db_file)
    return str(db_file)


def test_login_dialog_ilk_kurulum_ve_giris(qtbot, faz4_db, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok)

    kimlik_srv = KimlikServisi(faz4_db)
    ekran_dir = Path("docs/ekran")
    ekran_dir.mkdir(parents=True, exist_ok=True)

    # 1. İlk Kurulum Sihirbazı Testi
    dlg_sihirbaz = LoginDialog(kimlik_srv)
    apply_theme(dlg_sihirbaz)
    qtbot.addWidget(dlg_sihirbaz)
    dlg_sihirbaz.show()

    assert dlg_sihirbaz.ilk_kurulum is True

    # Ekran görüntüsü al
    dlg_sihirbaz.grab().save(str(ekran_dir / "login_dialog.png"))
    assert (ekran_dir / "login_dialog.png").exists()

    # Formu doldur ve yöneticiyi oluştur
    dlg_sihirbaz.txt_ad_soyad.setText("Dükkan Sahibi")
    dlg_sihirbaz.txt_kullanici_adi.setText("admin")
    dlg_sihirbaz.txt_parola.setText("123456")
    dlg_sihirbaz.txt_parola_tekrar.setText("123456")
    dlg_sihirbaz.islem_yap()

    assert kimlik_srv.kullanici_sayisi() == 1
    assert dlg_sihirbaz.giris_yapan_kullanici is not None
    assert dlg_sihirbaz.giris_yapan_kullanici.rol == "yonetici"


def test_musteriler_page_ve_tahsilat_ui(qtbot, faz4_db, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    musteri_srv = MusteriServisi(faz4_db)
    m_id = musteri_srv.musteri_ekle(Musteri(
        id=None,
        ad_soyad="Kardeşler Oto Servis",
        telefon="0212 555 4433",
        bakiye_kurus=150000  # 1.500 TL açık borç
    ))

    ekran_dir = Path("docs/ekran")
    page = MusterilerPage(musteri_srv)
    apply_theme(page)
    page.resize(1100, 650)
    qtbot.addWidget(page)
    page.show()

    assert page.tablo.rowCount() == 1

    # Ekran görüntüsü al
    page.grab().save(str(ekran_dir / "musteriler_page.png"))
    assert (ekran_dir / "musteriler_page.png").exists()

    # Tahsilat yap
    musteri_srv.tahsilat_yap(m_id, 50000, "nakit", "Elden ödeme")
    page.listeyi_guncelle()

    # Kalan borç 1.000 TL olmalı
    assert musteri_srv.musteri_getir(m_id).bakiye_kurus == 100000


def test_ayarlar_page_yetkilendirme_ve_yedekleme_ui(qtbot, faz4_db, tmp_path, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    kimlik_srv = KimlikServisi(faz4_db)
    yedek_srv = YedekServisi(faz4_db, tmp_path / "backups")

    admin_user = Kullanici(id=1, kullanici_adi="admin", parola_hash="", parola_salt="", ad_soyad="Admin", rol="yonetici")
    personel_user = Kullanici(id=2, kullanici_adi="personel", parola_hash="", parola_salt="", ad_soyad="Personel", rol="personel")

    ekran_dir = Path("docs/ekran")

    # 1. Personel rolü ile sayfa açıldığında: Kullanıcı yönetimi kilitli
    page_personel = AyarlarPage(yedek_srv, kimlik_srv, faz4_db, aktif_kullanici=personel_user)
    apply_theme(page_personel)
    page_personel.resize(1100, 650)
    qtbot.addWidget(page_personel)
    page_personel.show()

    # Ayarları değiştirmeyi dene -> yetkisiz işlem uyarısı
    page_personel.ayarlari_kaydet()

    # 2. Yönetici rolü ile sayfa açıldığında: Tam yetkili
    page_admin = AyarlarPage(yedek_srv, kimlik_srv, faz4_db, aktif_kullanici=admin_user)
    apply_theme(page_admin)
    page_admin.resize(1100, 650)
    qtbot.addWidget(page_admin)
    page_admin.show()

    # Ekran görüntüsü al
    page_admin.grab().save(str(ekran_dir / "ayarlar_page.png"))
    assert (ekran_dir / "ayarlar_page.png").exists()

    # Yedek al ve listele
    page_admin.manuel_yedek_al()
    assert page_admin.tablo_yedek.rowCount() >= 1

    # Sağlık kontrolü
    page_admin.saglik_kontrolu_yap()
