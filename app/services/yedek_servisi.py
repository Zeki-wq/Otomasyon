"""
Veritabanı Yedekleme ve Geri Yükleme Servisi
SQLite Online Backup API (conn.backup) kullanarak çalışır durumdaki veritabanını
hiçbir kilitlenme veya veri kaybı olmaksızın güvenle yedekler ve geri yükler.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
import logging
from app.config import DEFAULT_DB_PATH, BACKUP_DIR, MAX_BACKUP_COUNT, ensure_app_dirs
from app.db.connection import get_db_connection, check_db_health

logger = logging.getLogger("otoyedekparca")


class YedekServisi:
    def __init__(self, db_path: Optional[Union[Path, str]] = None, backup_dir: Optional[Union[Path, str]] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR

    def yedek_al(self, ozel_hedef_dizin: Optional[Union[Path, str]] = None) -> Path:
        """
        SQLite backup API ile canlı, tutarlı ve eksiksiz veritabanı yedeği alır.
        Son MAX_BACKUP_COUNT (30) yedeği korur, daha eskileri temizler.
        """
        ensure_app_dirs()
        hedef_klasor = Path(ozel_hedef_dizin) if ozel_hedef_dizin else self.backup_dir
        hedef_klasor.mkdir(parents=True, exist_ok=True)

        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        yedek_dosyasi = hedef_klasor / f"yedek_{zaman_damgasi}.db"

        kaynak_conn = get_db_connection(self.db_path)
        hedef_conn = sqlite3.connect(str(yedek_dosyasi))

        try:
            # SQLite Online Backup API
            kaynak_conn.backup(hedef_conn, pages=100)
            hedef_conn.close()
            kaynak_conn.close()

            logger.info("Yedek başarıyla alındı: %s", yedek_dosyasi)

            # Yedek rotasyonu uygula (yalnızca standart backup_dir içindeyse)
            if hedef_klasor == self.backup_dir:
                self._eski_yedekleri_temizle()

            return yedek_dosyasi
        except Exception as e:
            hedef_conn.close()
            kaynak_conn.close()
            if yedek_dosyasi.exists():
                yedek_dosyasi.unlink(missing_ok=True)
            logger.error("Yedek alma sırasında hata: %s", e)
            raise RuntimeError(f"Yedek alınamadı: {e}") from e

    def yedekten_geri_yukle(self, yedek_dosyasi: Union[Path, str]) -> bool:
        """
        Seçilen bir yedek dosyasından veritabanını geri yükler.
        Geri yükleme öncesinde mevcut aktif veritabanının güvenlik yedeğini alır.
        """
        yedek_path = Path(yedek_dosyasi)
        if not yedek_path.exists():
            raise FileNotFoundError(f"Yedek dosyası bulunamadı: {yedek_path}")

        # Yedek dosyasının sağlamlığını doğrula
        saglikli, mesaj = check_db_health(yedek_path)
        if not saglikli:
            raise ValueError(f"Geri yüklenmek istenen yedek dosyası bozuk: {mesaj}")

        # 1. Geri yüklemeden önce mevcut DB'nin güvenlik yedeğini al
        if self.db_path.exists():
            try:
                self.yedek_al()
            except Exception as e:
                logger.warning("Geri yükleme öncesi otomatik yedek alınırken hata: %s", e)

        # 2. Yedek dosyasından aktif veritabanına geri yükleme
        try:
            # WAL modundaki bağlantıları checkpoint ile temizle ve kapat
            wal_file = Path(str(self.db_path) + "-wal")
            shm_file = Path(str(self.db_path) + "-shm")

            # Mevcut DB dosyasını ve WAL dosyalarını kaldırıp yedeği kopyala
            if self.db_path.exists():
                self.db_path.unlink()
            if wal_file.exists():
                wal_file.unlink(missing_ok=True)
            if shm_file.exists():
                shm_file.unlink(missing_ok=True)

            shutil.copy2(str(yedek_path), str(self.db_path))

            # Bağlantıyı açıp PRAGMA journal_mode = WAL ayarını yeniden tesis et
            conn = get_db_connection(self.db_path)
            conn.close()

            logger.info("Veritabanı %s yedeğinden başarıyla geri yüklendi.", yedek_path)
            return True
        except Exception as e:
            logger.error("Geri yükleme hatası: %s", e)
            raise RuntimeError(f"Geri yükleme başarısız: {e}") from e

    def mevcut_yedekleri_listele(self) -> List[Dict[str, Any]]:
        """Varsayılan yedek klasöründeki yedekleri tarihe göre sıralı listeler."""
        if not self.backup_dir.exists():
            return []

        yedek_dosyalari = sorted(
            self.backup_dir.glob("yedek_*.db"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        sonuclar = []
        for dosya in yedek_dosyalari:
            stat = dosya.stat()
            boyut_kb = stat.st_size / 1024
            tarih_str = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S")
            sonuclar.append({
                "dosya_adi": dosya.name,
                "yol": str(dosya.absolute()),
                "boyut_kb": round(boyut_kb, 1),
                "tarih": tarih_str,
                "mtime": stat.st_mtime
            })
        return sonuclar

    def _eski_yedekleri_temizle(self):
        """MAX_BACKUP_COUNT'tan eski yedekleri siler."""
        try:
            yedek_dosyalari = sorted(
                self.backup_dir.glob("yedek_*.db"),
                key=lambda x: x.stat().st_mtime
            )
            fazlalik = len(yedek_dosyalari) - MAX_BACKUP_COUNT
            if fazlalik > 0:
                for eski_yedek in yedek_dosyalari[:fazlalik]:
                    eski_yedek.unlink(missing_ok=True)
                    logger.info("Eski yedek silindi (rotasyon): %s", eski_yedek.name)
        except Exception as e:
            logger.warning("Yedek rotasyonu sırasında uyarı: %s", e)
