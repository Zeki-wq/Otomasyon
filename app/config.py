"""
Uygulama Genel Yapılandırması ve Yollar
"""

import os
import sys
from pathlib import Path

APP_NAME = "Oto Yedek Parça Otomasyonu"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "OtoYedekParca"

# Windows'ta %APPDATA%\OtoYedekParca, diğerlerinde ~/.otoyedekparca
if sys.platform == "win32":
    appdata_base = os.getenv("APPDATA")
    if appdata_base:
        DATA_DIR = Path(appdata_base) / "OtoYedekParca"
    else:
        DATA_DIR = Path.home() / "AppData" / "Roaming" / "OtoYedekParca"
else:
    DATA_DIR = Path.home() / ".otoyedekparca"

DB_FILENAME = "otoyedekparca.db"
DEFAULT_DB_PATH = DATA_DIR / DB_FILENAME
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"
EXPORT_DIR = DATA_DIR / "exports"

DEFAULT_KDV_ORANI = 20
MAX_BACKUP_COUNT = 30


def ensure_app_dirs():
    """Gerekli tüm uygulama dizinlerinin varlığını garanti eder."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
