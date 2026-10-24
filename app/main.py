"""
Oto Yedek Parça Otomasyonu - Tek Giriş Noktası (Main Entry Point)
Tek QApplication örneği, tek örnek kilidi, migrasyon kontrolü ve modern arayüz.
"""

import sys
from pathlib import Path

# Proje kök dizinini sys.path'e ekle
KOK_DIZIN = Path(__file__).resolve().parent.parent
if str(KOK_DIZIN) not in sys.path:
    sys.path.insert(0, str(KOK_DIZIN))

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox

from app.config import APP_NAME, APP_VERSION, DEFAULT_DB_PATH, ensure_app_dirs
from app.db.connection import check_db_health, get_db_connection
from app.db.legacy_import import import_legacy_database
from app.db.migrations.migrator import run_migrations
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.rapor_servisi import RaporServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.services.yedek_servisi import YedekServisi
from app.ui.main_window import MainWindow
from app.ui.pages.login_dialog import LoginDialog
from app.ui.theme import apply_theme
from app.utils.logging import install_exception_handler, setup_logging


def tek_ornek_kilidi_al(app: QApplication) -> QtCore.QSharedMemory:
    """
    Uygulamanın aynı anda iki kez açılıp veritabanını kilitlemesini önler.
    Windows üzerinde QSharedMemory tabanlı tek örnek kontrolü uygular.
    """
    shared_mem = QtCore.QSharedMemory("OtoYedekParca_TekOrnek_Kilidi")
    if not shared_mem.create(1):
        QMessageBox.warning(
            None,
            "Uygulama Zaten Açık",
            f"{APP_NAME} zaten çalışıyor!\n"
            "Lütfen görev çubuğundaki açık pencereyi kontrol ediniz."
        )
        sys.exit(0)
    return shared_mem


def main():
    # 1. High-DPI Ayarları (1366x768 ve %125-150 ölçekleme için)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    # 2. Loglama ve Hata Yakalama
    logger = setup_logging()
    install_exception_handler()
    logger.info("Uygulama başlatılıyor: %s v%s", APP_NAME, APP_VERSION)

    # 3. Tek QApplication Örneği
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    apply_theme(app)

    # 4. Tek Örnek Kilidi
    app._shared_mem = tek_ornek_kilidi_al(app)

    # 5. Dizinler ve Veritabanı Hazırlığı
    ensure_app_dirs()

    try:
        # Migrasyonları çalıştır
        run_migrations(DEFAULT_DB_PATH)

        # Sağlık kontrolü
        saglikli, mesaj = check_db_health(DEFAULT_DB_PATH)
        if not saglikli:
            logger.critical("Veritabanı sağlık kontrolü başarısız: %s", mesaj)
            QMessageBox.critical(
                None,
                "Veritabanı Hatası",
                f"Veritabanında tutarsızlık tespit edildi:\n{mesaj}\n"
                "Lütfen yedek klasöründen en son sağlam yedeği geri yükleyiniz."
            )

        # Eski veritabanı göç kontrolü
        conn = get_db_connection(DEFAULT_DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT deger FROM ayar WHERE anahtar = 'legacy_import_tamamlandi'")
        row = cur.fetchone()
        legacy_tamamlandi = row and row["deger"] == "1"
        conn.close()

        if not legacy_tamamlandi:
            # Varsa legacy/urunler12.db veya urunler12.db dosyasını aktar
            legacy_adaylari = [
                KOK_DIZIN / "legacy" / "urunler12.db",
                KOK_DIZIN / "urunler12.db"
            ]
            for aday in legacy_adaylari:
                if aday.exists():
                    logger.info("Eski veritabanı tespit edildi, göç başlatılıyor: %s", aday)
                    import_legacy_database(aday, DEFAULT_DB_PATH)
                    break

    except Exception as e:
        logger.exception("Başlatma sırasında kritik hata: %s", e)
        QMessageBox.critical(None, "Kritik Başlatma Hatası", f"Veritabanı hazırlığı başarısız oldu:\n{e}")
        sys.exit(1)

    # 6. Servisleri Başlat
    kimlik_servisi = KimlikServisi(DEFAULT_DB_PATH)
    urun_servisi = UrunServisi(DEFAULT_DB_PATH)
    stok_servisi = StokServisi(DEFAULT_DB_PATH)
    satis_servisi = SatisServisi(DEFAULT_DB_PATH)
    musteri_servisi = MusteriServisi(DEFAULT_DB_PATH)
    yedek_servisi = YedekServisi(DEFAULT_DB_PATH)
    rapor_servisi = RaporServisi(DEFAULT_DB_PATH)

    # 7. Giriş Ekranı (İlk açılışta sihirbaz gelir)
    login_dlg = LoginDialog(kimlik_servisi)
    apply_theme(login_dlg)

    if login_dlg.exec_() != QtWidgets.QDialog.Accepted:
        logger.info("Kullanıcı giriş yapmadan çıkış yaptı.")
        sys.exit(0)

    aktif_kullanici = login_dlg.giris_yapan_kullanici
    logger.info("Giriş başarılı: %s (%s)", aktif_kullanici.kullanici_adi, aktif_kullanici.rol)

    # 8. Ana Pencereyi Göster
    pencere = MainWindow(
        urun_servisi=urun_servisi,
        stok_servisi=stok_servisi,
        satis_servisi=satis_servisi,
        musteri_servisi=musteri_servisi,
        kimlik_servisi=kimlik_servisi,
        yedek_servisi=yedek_servisi,
        rapor_servisi=rapor_servisi,
        aktif_kullanici=aktif_kullanici,
        db_path=DEFAULT_DB_PATH
    )
    pencere.show()

    # Kapanışta otomatik günlük yedek al
    def kapanis_yedegi():
        try:
            yedek_servisi.yedek_al()
            logger.info("Kapanış otomatik yedeği alındı.")
        except Exception as e:
            logger.warning("Kapanış yedeği alınamadı: %s", e)

    app.aboutToQuit.connect(kapanis_yedegi)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
