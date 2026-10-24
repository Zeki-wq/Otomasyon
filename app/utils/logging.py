"""
Loglama ve Yakalanmamış Hata Yönetimi
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import LOG_DIR, ensure_app_dirs

logger = logging.getLogger("otoyedekparca")


def setup_logging(log_dir: Path = LOG_DIR) -> logging.Logger:
    """Uygulama loglama altyapısını başlatır (RotatingFileHandler + Console)."""
    ensure_app_dirs()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger.setLevel(logging.INFO)

    # Varsa önceki handler'ları temizle
    if logger.hasHandlers():
        logger.handlers.clear()

    # Dosya Loglayıcı (5 MB max, 5 yedek)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Konsol Loglayıcı
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Loglama sistemi başlatıldı. Hedef: %s", log_file)
    return logger


def install_exception_handler():
    """Yakalanmamış istisnaları log'a yazar ve uygulamanın sessizce çökmesini önler."""
    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Yakalanmamış İstisna Meydana Geldi!", exc_info=(exc_type, exc_value, exc_traceback))

        # Eğer Qt çalışıyorsa şık bir hata diyaloğu göster
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance()
            if app:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Beklenmeyen Hata")
                msg.setText("Uygulamada beklenmeyen bir hata oluştu.")
                msg.setInformativeText(f"{exc_type.__name__}: {exc_value}\n\nDetaylar log dosyasına kaydedildi.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
        except Exception:
            pass

    sys.excepthook = excepthook
