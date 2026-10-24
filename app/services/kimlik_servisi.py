"""
Kimlik Doğrulama ve Kullanıcı Yönetim Servisi
Şifreler PBKDF2-HMAC-SHA256 ve rastgele 16 bayt salt ile hash'lenir.
"""

import hashlib
import os
import sqlite3
from pathlib import Path

from app.db.connection import get_db_connection
from app.domain.models import Kullanici


class KimlikServisi:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    @staticmethod
    def _hash_parola(parola: str, salt: bytes) -> str:
        """PBKDF2-HMAC-SHA256 ile 100.000 iterasyonlu şifre hash'i üretir."""
        hashed = hashlib.pbkdf2_hmac("sha256", parola.encode("utf-8"), salt, 100000)
        return hashed.hex()

    def kullanici_sayisi(self) -> int:
        """Kayıtlı aktif kullanıcı sayısını döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kullanici WHERE aktif = 1")
        sayi = cur.fetchone()[0]
        conn.close()
        return sayi

    def kullanici_olustur(
        self,
        kullanici_adi: str,
        parola: str,
        ad_soyad: str,
        rol: str = "personel"
    ) -> Kullanici:
        """Yeni bir kullanıcı oluşturur."""
        kullanici_adi = kullanici_adi.strip().lower()
        if not kullanici_adi or len(kullanici_adi) < 3:
            raise ValueError("Kullanıcı adı en az 3 karakter olmalıdır.")
        if not parola or len(parola) < 4:
            raise ValueError("Parola en az 4 karakter olmalıdır.")
        if rol not in ("yonetici", "personel"):
            raise ValueError("Geçersiz rol. Sadece 'yonetici' veya 'personel' olabilir.")

        salt_bytes = os.urandom(16)
        salt_hex = salt_bytes.hex()
        parola_hash = self._hash_parola(parola, salt_bytes)

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            with conn:
                cur.execute("""
                    INSERT INTO kullanici (kullanici_adi, parola_hash, parola_salt, ad_soyad, rol, aktif)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (kullanici_adi, parola_hash, salt_hex, ad_soyad.strip(), rol))
                yeni_id = cur.lastrowid
            conn.close()
            return Kullanici(
                id=yeni_id,
                kullanici_adi=kullanici_adi,
                parola_hash=parola_hash,
                parola_salt=salt_hex,
                ad_soyad=ad_soyad.strip(),
                rol=rol,
                aktif=1
            )
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"'{kullanici_adi}' kullanıcı adı zaten kullanımda.")

    def giris_yap(self, kullanici_adi: str, parola: str) -> Kullanici | None:
        """Kullanıcı adı ve parola doğrulaması yapar."""
        kullanici_adi = kullanici_adi.strip().lower()
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, kullanici_adi, parola_hash, parola_salt, ad_soyad, rol, aktif
            FROM kullanici
            WHERE kullanici_adi = ? AND aktif = 1
        """, (kullanici_adi,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        salt_bytes = bytes.fromhex(row["parola_salt"])
        hesaplanan_hash = self._hash_parola(parola, salt_bytes)

        if hesaplanan_hash == row["parola_hash"]:
            return Kullanici(
                id=row["id"],
                kullanici_adi=row["kullanici_adi"],
                parola_hash=row["parola_hash"],
                parola_salt=row["parola_salt"],
                ad_soyad=row["ad_soyad"],
                rol=row["rol"],
                aktif=row["aktif"]
            )
        return None

    def kullanicilari_listele(self) -> list[Kullanici]:
        """Tüm kullanıcıları listeler."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, kullanici_adi, parola_hash, parola_salt, ad_soyad, rol, aktif
            FROM kullanici ORDER BY id ASC
        """)
        rows = cur.fetchall()
        conn.close()
        return [
            Kullanici(
                id=r["id"],
                kullanici_adi=r["kullanici_adi"],
                parola_hash=r["parola_hash"],
                parola_salt=r["parola_salt"],
                ad_soyad=r["ad_soyad"],
                rol=r["rol"],
                aktif=r["aktif"]
            )
            for r in rows
        ]
