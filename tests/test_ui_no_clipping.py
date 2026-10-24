"""
Arayüz Metin Kırpılma ve Boyut Doğrulama Testleri (UI No-Clipping Regression Tests)
Her sayfa ve diyalogdaki QLineEdit, QComboBox, QDateEdit, QSpinBox ve QPushButton
bileşenlerinin yüksekliklerinin ve metin genişliklerinin tam sığdığını,
metinlerin üstten/alttan/yandan kırpılmadığını ve '?' yardım butonunun kapatıldığını doğrular.
"""

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from app.db.migrations.migrator import run_migrations
from app.domain.models import Musteri, Urun
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.rapor_servisi import RaporServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.services.yedek_servisi import YedekServisi
from app.ui.main_window import MainWindow
from app.ui.pages.login_dialog import LoginDialog
from app.ui.pages.musteriler_page import EkstreDiyalog, MusteriDiyalog, TahsilatDiyalog
from app.ui.pages.siparisler_page import SiparisDetayDiyalog
from app.ui.pages.urunler_page import UrunDiyalog
from app.ui.theme import apply_theme


def _kirpilma_denetimi_yap(pencere_adi: str, widget_root):
    """
    Belirtilen kök bileşen içindeki tüm giriş ve buton bileşenlerini
    font metrics ve sizeHint seviyesinde denetler.
    Kırpılan bir bileşen bulunursa anlaşılır hata mesajıyla assert eder.
    """
    hatalar = []

    # 1. QLineEdit Denetimi
    for le in widget_root.findChildren(QLineEdit):
        if not le.isVisible():
            continue
        parent = le.parentWidget()
        if isinstance(parent, (QSpinBox, QDoubleSpinBox, QDateEdit)):
            p_h = parent.height()
            p_sh = parent.sizeHint().height()
            fm_h = parent.fontMetrics().height()
            if p_h < (p_sh - 1) or p_h < (fm_h + 8):
                hatalar.append(
                    f"[{pencere_adi}] {type(parent).__name__} boyutu yetersiz: "
                    f"height={p_h} < sizeHint={p_sh} (font_h={fm_h})"
                )
            continue

        h = le.height()
        sh = le.sizeHint().height()
        fm = le.fontMetrics()
        fm_h = fm.height()
        metin = le.text() or le.placeholderText() or ""

        if h < (sh - 1) or h < (fm_h + 8):
            hatalar.append(
                f"[{pencere_adi}] QLineEdit dikey kırpılma: ph='{metin}', "
                f"actual_height={h} < sizeHint_height={sh} (font_height={fm_h})"
            )

    # 2. QComboBox Denetimi
    for cb in widget_root.findChildren(QComboBox):
        if not cb.isVisible():
            continue
        h = cb.height()
        sh = cb.sizeHint().height()
        if h < (sh - 1):
            hatalar.append(
                f"[{pencere_adi}] QComboBox dikey kırpılma: name='{cb.objectName()}', "
                f"actual_height={h} < sizeHint_height={sh}"
            )

    # 3. QPushButton Denetimi (Yükseklik ve Metin Genişliği)
    for btn in widget_root.findChildren(QPushButton):
        if not btn.isVisible():
            continue
        h = btn.height()
        sh = btn.sizeHint().height()
        w = btn.width()
        metin = btn.text()
        fm = btn.fontMetrics()
        fm_w = fm.horizontalAdvance(metin)

        if h < (sh - 1):
            hatalar.append(
                f"[{pencere_adi}] QPushButton yükseklik kırpılma: text='{metin}', "
                f"actual_height={h} < sizeHint_height={sh}"
            )

        if w > 0 and metin and w < (fm_w + 6):
            hatalar.append(
                f"[{pencere_adi}] QPushButton yatay metin taşması: text='{metin}', "
                f"actual_width={w} < text_width={fm_w}"
            )

    assert not hatalar, "Arayüzde kırpılan / sığmayan bileşenler tespit edildi:\n" + "\n".join(hatalar)


def test_login_dialog_no_clipping(qtbot, tmp_path):
    """İlk kurulum sihirbazı ve normal giriş ekranında metin kırpılması olmamalıdır."""
    db_path = tmp_path / "test_login.db"
    run_migrations(db_path)
    ks = KimlikServisi(db_path)

    # 1. İlk kurulum modu
    dlg_kurulum = LoginDialog(ks)
    apply_theme(dlg_kurulum)
    qtbot.addWidget(dlg_kurulum)
    dlg_kurulum.show()
    qtbot.waitExposed(dlg_kurulum)

    # '?' yardım butonu kapatılmış olmalı
    assert not (dlg_kurulum.windowFlags() & QtCore.Qt.WindowContextHelpButtonHint)
    _kirpilma_denetimi_yap("LoginDialog (Ilk Kurulum)", dlg_kurulum)
    dlg_kurulum.close()

    # 2. Normal giriş modu
    ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    dlg_giris = LoginDialog(ks)
    apply_theme(dlg_giris)
    qtbot.addWidget(dlg_giris)
    dlg_giris.show()
    qtbot.waitExposed(dlg_giris)

    assert not (dlg_giris.windowFlags() & QtCore.Qt.WindowContextHelpButtonHint)
    _kirpilma_denetimi_yap("LoginDialog (Giris)", dlg_giris)
    dlg_giris.close()


def test_tum_diyaloglar_no_clipping(qtbot, tmp_path):
    """Tüm QDialog pencerelerinde metin kırpılması ve '?' butonu olmamalıdır."""
    db_path = tmp_path / "test_diag.db"
    run_migrations(db_path)

    us = UrunServisi(db_path)
    ms = MusteriServisi(db_path)
    satis = SatisServisi(db_path)
    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")

    u_id = us.urun_ekle(Urun(id=None, parca_kodu="BRM-001", ad="Brembo Disk", alis_fiyati_kurus=1000, satis_fiyati_kurus=1500, kdv_orani=20, stok=10))
    urun_obj = us.urun_getir(u_id)

    m_id = ms.musteri_ekle(Musteri(id=None, ad_soyad="Ahmet Usta", telefon="05321234567"))
    musteri_obj = ms.musteri_getir(m_id)

    siparis = satis.siparis_olustur([{"urun_id": u_id, "adet": 1, "birim_fiyat": 1500, "kdv_orani": 20}], musteri_id=m_id, kullanici_id=user.id)

    diyaloglar = [
        ("UrunDiyalog (Yeni)", UrunDiyalog(None, us)),
        ("UrunDiyalog (Duzenle)", UrunDiyalog(None, us, urun_obj)),
        ("MusteriDiyalog", MusteriDiyalog(None, ms)),
        ("TahsilatDiyalog", TahsilatDiyalog(musteri_obj, ms)),
        ("EkstreDiyalog", EkstreDiyalog(musteri_obj, ms)),
        ("SiparisDetayDiyalog", SiparisDetayDiyalog(siparis)),
    ]

    for ad, dlg in diyaloglar:
        apply_theme(dlg)
        qtbot.addWidget(dlg)
        dlg.show()
        qtbot.waitExposed(dlg)

        # Context help butonu kapalı olmalı
        assert not (dlg.windowFlags() & QtCore.Qt.WindowContextHelpButtonHint), f"{ad} penceresinde '?' butonu kapatılmamış!"
        _kirpilma_denetimi_yap(ad, dlg)
        dlg.close()


def test_main_window_tum_sayfalar_no_clipping(qtbot, tmp_path):
    """MainWindow içindeki 8 sayfanın tamamında giriş ve buton kırpılması olmamalıdır."""
    db_path = tmp_path / "test_mw.db"
    run_migrations(db_path)

    us = UrunServisi(db_path)
    ss = StokServisi(db_path)
    satis = SatisServisi(db_path)
    ms = MusteriServisi(db_path)
    ks = KimlikServisi(db_path)
    ys = YedekServisi(db_path)
    rs = RaporServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")

    mw = MainWindow(us, ss, satis, ms, ks, ys, rs, user, db_path)
    apply_theme(mw)
    qtbot.addWidget(mw)
    mw.show()
    qtbot.waitExposed(mw)

    for sayfa_kodu in ["dashboard", "satis", "urunler", "siparisler", "musteriler", "stok", "raporlar", "ayarlar"]:
        mw.sayfa_degistir(sayfa_kodu)
        qtbot.waitExposed(mw.stack.currentWidget())
        _kirpilma_denetimi_yap(f"MainWindow Sayfa: {sayfa_kodu}", mw.stack.currentWidget())

    mw.close()
