"""
Veritabanı Şema Migrasyon Yöneticisi
PRAGMA user_version ile sıralı .sql migrasyonlarını uygular.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Union
import logging
from app.db.connection import get_db_connection

logger = logging.getLogger("otoyedekparca")
MIGRATIONS_DIR = Path(__file__).parent


def run_migrations(db_path: Optional[Union[Path, str]] = None) -> int:
    """
    Tüm bekleyen SQL migrasyonlarını sırayla çalıştırır.
    Dönüş: Son şema versiyonu
    """
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA user_version;")
    current_version = cur.fetchone()[0]

    # MIGRATIONS_DIR içindeki NNNN_*.sql dosyalarını sırala
    sql_files = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))

    for sql_file in sql_files:
        version_num = int(sql_file.name.split("_")[0])
        if version_num > current_version:
            logger.info("Migrasyon uygulanıyor: %s (v%d)", sql_file.name, version_num)
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            try:
                # SQLite script tek transaction içinde çalıştırılır
                conn.executescript(sql_content)
                conn.execute(f"PRAGMA user_version = {version_num};")
                conn.commit()
                current_version = version_num
                logger.info("Migrasyon başarıyla uygulandı: v%d", current_version)
            except Exception as e:
                conn.rollback()
                logger.error("Migrasyon hatası (%s): %s", sql_file.name, e)
                conn.close()
                raise RuntimeError(f"Migrasyon hatası ({sql_file.name}): {e}") from e

    conn.close()
    return current_version
