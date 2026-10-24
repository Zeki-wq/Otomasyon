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


import time

class KimlikServisi:
    # Hatalı deneme takibi: kullanici_adi -> [zaman1, zaman2, ...]
    _hatali_denemeler: dict[str, list[float]] = {}
    KILIT_ESIK_SAYISI = 5
    KILIT_SURESI_SANIYE = 300  # 5 dakika

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

    def kalan_kilit_suresi(self, kullanici_adi: str) -> int:
        """Kullanıcının geçici kilit süresinden kalan saniyeyi döner, kilitli değilse 0."""
        kullanici_adi = kullanici_adi.strip().lower()
        denemeler = self._hatali_denemeler.get(kullanici_adi, [])
        simdi = time.time()
        # Son 5 dakikadaki denemeleri filtrele
        gecerli_denemeler = [t for t in denemeler if simdi - t < self.KILIT_SURESI_SANIYE]
        self._hatali_denemeler[kullanici_adi] = gecerli_denemeler
        if len(gecerli_denemeler) >= self.KILIT_ESIK_SAYISI:
            en_eski = gecerli_denemeler[0]
            kalan = int(self.KILIT_SURESI_SANIYE - (simdi - en_eski))
            return max(1, kalan)
        return 0

    def giris_yap(self, kullanici_adi: str, parola: str) -> Kullanici | None:
        """Kullanıcı adı ve parola doğrulaması yapar (5 hatalı denemede 5 dk kilit)."""
        kullanici_adi = kullanici_adi.strip().lower()

        kalan = self.kalan_kilit_suresi(kullanici_adi)
        if kalan > 0:
            dakika = (kalan + 59) // 60
            raise ValueError(
                f"Çok fazla hatalı deneme yapıldı! Güvenlik nedeniyle hesap {dakika} dakika ({kalan} sn) süreyle geçici olarak kilitlendi."
            )

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
            self._hatali_deneme_kaydet(kullanici_adi)
            return None

        salt_bytes = bytes.fromhex(row["parola_salt"])
        hesaplanan_hash = self._hash_parola(parola, salt_bytes)

        if hesaplanan_hash == row["parola_hash"]:
            # Başarılı girişte hatalı denemeleri temizle
            self._hatali_denemeler.pop(kullanici_adi, None)
            return Kullanici(
                id=row["id"],
                kullanici_adi=row["kullanici_adi"],
                parola_hash=row["parola_hash"],
                parola_salt=row["parola_salt"],
                ad_soyad=row["ad_soyad"],
                rol=row["rol"],
                aktif=row["aktif"]
            )

        # Hatalı parola
        self._hatali_deneme_kaydet(kullanici_adi)
        return None

    def _hatali_deneme_kaydet(self, kullanici_adi: str):
        if kullanici_adi not in self._hatali_denemeler:
            self._hatali_denemeler[kullanici_adi] = []
        self._hatali_denemeler[kullanici_adi].append(time.time())

    def parola_degistir(self, kullanici_id: int, eski_parola: str, yeni_parola: str) -> bool:
        """Kullanıcının mevcut parolasını güvenli bir şekilde günceller."""
        if not yeni_parola or len(yeni_parola) < 4:
            raise ValueError("Yeni parola en az 4 karakter olmalıdır.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT parola_hash, parola_salt FROM kullanici WHERE id = ? AND aktif = 1", (kullanici_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Kullanıcı bulunamadı.")

        salt_bytes = bytes.fromhex(row["parola_salt"])
        if self._hash_parola(eski_parola, salt_bytes) != row["parola_hash"]:
            conn.close()
            raise ValueError("Mevcut parola yanlış!")

        yeni_salt_bytes = os.urandom(16)
        yeni_salt_hex = yeni_salt_bytes.hex()
        yeni_hash = self._hash_parola(yeni_parola, yeni_salt_bytes)

        with conn:
            cur.execute("""
                UPDATE kullanici SET parola_hash = ?, parola_salt = ? WHERE id = ?
            """, (yeni_hash, yeni_salt_hex, kullanici_id))
        conn.close()
        return True

    def yonetici_parola_sifirla(self, yeni_parola: str) -> bool:
        """Acil durum yönetici parolası sıfırlama (yerel komut satırı aracı)."""
        if not yeni_parola or len(yeni_parola) < 4:
            raise ValueError("Yeni parola en az 4 karakter olmalıdır.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM kullanici WHERE rol = 'yonetici' AND aktif = 1 ORDER BY id ASC LIMIT 1")
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Aktif yönetici hesabı bulunamadı.")

        yonetici_id = row["id"]
        yeni_salt = os.urandom(16)
        yeni_hash = self._hash_parola(yeni_parola, yeni_salt)

        with conn:
            cur.execute("""
                UPDATE kullanici SET parola_hash = ?, parola_salt = ? WHERE id = ?
            """, (yeni_hash, yeni_salt.hex(), yonetici_id))
        conn.close()
        return True

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
