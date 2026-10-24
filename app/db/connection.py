"""
SQLite Veritabanı Bağlantı ve Sağlık Kontrolü Modülü
"""

import sqlite3
from pathlib import Path
from typing import Optional, Union
from app.config import DEFAULT_DB_PATH, ensure_app_dirs
import logging

logger = logging.getLogger("otoyedekparca")


def get_db_connection(db_path: Optional[Union[Path, str]] = None) -> sqlite3.Connection:
    """
    Güvenli SQLite bağlantısı üretir.
    - foreign_keys = ON
    - journal_mode = WAL
    - busy_timeout = 5000 ms
    - synchronous = NORMAL
    - row_factory = sqlite3.Row
    """
    if db_path is None:
        ensure_app_dirs()
        target_path = DEFAULT_DB_PATH
    else:
        target_path = Path(db_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row

    # Bağlantı PRAGMA ayarları
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    # Bellek içi veritabanlarında WAL uygulanamaz
    if str(target_path) != ":memory:":
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
        except sqlite3.OperationalError:
            pass

    return conn


def check_db_health(db_path: Optional[Union[Path, str]] = None) -> tuple[bool, str]:
    """
    Veritabanı sağlık kontrolünü yürütür (PRAGMA quick_check).
    Dönüş: (saglikli_mi, aciklama)
    """
    try:
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA quick_check;")
        res = cur.fetchall()
        conn.close()

        if res and res[0][0] == "ok":
            return (True, "Veritabanı bütünlüğü sağlam (OK)")
        else:
            hata = ", ".join([str(r[0]) for r in res])
            return (False, f"Bozukluk tespit edildi: {hata}")
    except Exception as e:
        logger.error("Veritabanı sağlık kontrolünde hata: %s", e)
        return (False, str(e))
