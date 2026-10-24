"""
Veritabanı Şema Migrasyon Yöneticisi
PRAGMA user_version ile sıralı .sql migrasyonlarını uygular.
"""

from datetime import datetime
import logging
from pathlib import Path
import sqlite3

from app.db.connection import get_db_connection

logger = logging.getLogger("otoyedekparca")
MIGRATIONS_DIR = Path(__file__).parent



def run_migrations(db_path: Path | str | None = None) -> int:
    """
    Tüm bekleyen SQL migrasyonlarını sırayla çalıştırır.
    Mevcut bir veritabanı (user_version > 0) yeni sürüme güncelleniyorsa,
    migrasyona başlamadan ÖNCE otomatik güvenlik yedeği alır.
    Herhangi bir migrasyon adımı başarısız olursa, otomatik olarak alınan
    güvenlik yedeğini geri yükler ve anlaşılır bir hata fırlatır.
    Dönüş: Son şema versiyonu
    """
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA user_version;")
    current_version = cur.fetchone()[0]

    # MIGRATIONS_DIR içindeki NNNN_*.sql dosyalarını sırala
    sql_files = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    pending_files = [f for f in sql_files if int(f.name.split("_")[0]) > current_version]

    if not pending_files:
        conn.close()
        return current_version

    backup_path = None
    target_path = Path(db_path) if db_path else None

    # Eğer mevcut veritabanı zaten kullanımda idiyse (v > 0) ve yeni migrasyon varsa:
    if current_version > 0 and target_path and target_path.exists():
        backup_dir = target_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"upgrade_pre_v{current_version}_{zaman}.db"
        logger.info("Şema güncellemesi öncesi otomatik güvenlik yedeği alınıyor: %s", backup_path)
        try:
            b_conn = sqlite3.connect(str(backup_path))
            conn.backup(b_conn)
            b_conn.close()
            logger.info("Güncelleme öncesi otomatik yedek başarıyla oluşturuldu: %s", backup_path)
        except Exception as be:
            logger.warning("Güncelleme öncesi otomatik yedek alınamadı: %s", be)
            backup_path = None

    for sql_file in pending_files:
        version_num = int(sql_file.name.split("_")[0])
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
            conn.close()
            logger.error("Migrasyon hatası (%s): %s", sql_file.name, e)

            # Başarısız olursa ve güvenlik yedeği varsa yedeği geri yükle
            if backup_path and backup_path.exists() and target_path:
                logger.warning("Migrasyon başarısız oldu, otomatik yedek geri yükleniyor: %s -> %s", backup_path, target_path)
                try:
                    # Target DB'yi yedeğin kopyasıyla değiştir
                    shutil_conn = sqlite3.connect(str(backup_path))
                    restore_conn = sqlite3.connect(str(target_path))
                    shutil_conn.backup(restore_conn)
                    restore_conn.close()
                    shutil_conn.close()
                    logger.info("Başarısız migrasyon sonrası veritabanı önceki sürüme güvenle geri döndürüldü.")
                except Exception as restore_err:
                    logger.critical("Otomatik yedeği geri yüklerken hata: %s", restore_err)

            raise RuntimeError(
                f"Veritabanı güncellemesi ({sql_file.name}) sırasında hata oluştu:\n{e}\n"
                + ("Önceki veritabanı yedeğiniz güvenle geri yüklendi." if backup_path else "")
            ) from e

    conn.close()
    return current_version

