"""
Müşteri / Cari Hesap ve Tahsilat Servisi
"""

import sqlite3
from pathlib import Path
from typing import Any

from app.db.connection import get_db_connection
from app.domain.models import Musteri


class MusteriServisi:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def musteri_ekle(self, musteri: Musteri) -> int:
        """Yeni cari müşteri ekler."""
        ad_soyad = str(musteri.ad_soyad or "").strip()
        if not ad_soyad:
            raise ValueError("Müşteri adı soyadı boş bırakılamaz.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with conn:
            cur.execute("""
                INSERT INTO musteri (
                    ad_soyad, telefon, eposta, adres, vergi_no_tc, bakiye_kurus, aktif
                ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                ad_soyad,
                str(musteri.telefon or "").strip(),
                str(musteri.eposta or "").strip(),
                str(musteri.adres or "").strip(),
                str(musteri.vergi_no_tc or "").strip(),
                musteri.bakiye_kurus
            ))
            yeni_id = cur.lastrowid
        conn.close()
        return yeni_id

    def musteri_guncelle(self, musteri: Musteri) -> bool:
        """Müşteri iletişim ve vergi bilgilerini günceller."""
        if not musteri.id:
            raise ValueError("Müşteri ID'si gereklidir.")

        ad_soyad = str(musteri.ad_soyad or "").strip()
        if not ad_soyad:
            raise ValueError("Müşteri adı soyadı boş bırakılamaz.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with conn:
            cur.execute("""
                UPDATE musteri SET
                    ad_soyad = ?,
                    telefon = ?,
                    eposta = ?,
                    adres = ?,
                    vergi_no_tc = ?
                WHERE id = ?
            """, (
                ad_soyad,
                str(musteri.telefon or "").strip(),
                str(musteri.eposta or "").strip(),
                str(musteri.adres or "").strip(),
                str(musteri.vergi_no_tc or "").strip(),
                musteri.id
            ))
        conn.close()
        return True

    def musteri_pasife_al(self, musteri_id: int) -> bool:
        """Müşteriyi pasife alır (KVKK / arşiv)."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with conn:
            cur.execute("UPDATE musteri SET aktif = 0 WHERE id = ?", (musteri_id,))
        conn.close()
        return True

    def musteri_getir(self, musteri_id: int) -> Musteri | None:
        """ID ile tek müşteri döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM musteri WHERE id = ?", (musteri_id,))
        row = cur.fetchone()
        conn.close()
        return self._satiri_musteriye_cevir(row) if row else None

    def musterileri_getir(self, arama_metni: str = "", sadece_aktif: bool = True) -> list[Musteri]:
        """Arama ve filtreleme ile müşteri listesini döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        kosullar = []
        parametreler = []

        if sadece_aktif:
            kosullar.append("aktif = 1")

        if arama_metni and arama_metni.strip():
            t = f"%{arama_metni.strip()}%"
            kosullar.append("(ad_soyad LIKE ? OR telefon LIKE ? OR vergi_no_tc LIKE ?)")
            parametreler.extend([t, t, t])

        where_clause = " WHERE " + " AND ".join(kosullar) if kosullar else ""
        sql = f"SELECT * FROM musteri {where_clause} ORDER BY ad_soyad COLLATE NOCASE ASC"

        cur.execute(sql, parametreler)
        rows = cur.fetchall()
        conn.close()

        return [self._satiri_musteriye_cevir(r) for r in rows]

    def tahsilat_yap(
        self,
        musteri_id: int,
        tutar_kurus: int,
        odeme_tipi: str = "nakit",
        aciklama: str = "",
        kullanici_id: int | None = None
    ) -> int:
        """
        Müşteriden tahsilat alır ve cari bakiyesinden düşer.
        Tek transaction içinde atomik yürütülür.
        """
        if tutar_kurus <= 0:
            raise ValueError("Tahsilat tutarı 0'dan büyük olmalıdır.")
        if odeme_tipi not in ("nakit", "kart"):
            raise ValueError("Tahsilat tipi 'nakit' veya 'kart' olmalıdır.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        try:
            with conn:
                cur.execute("SELECT bakiye_kurus FROM musteri WHERE id = ? AND aktif = 1", (musteri_id,))
                m_row = cur.fetchone()
                if not m_row:
                    raise ValueError("Müşteri bulunamadı.")

                cur.execute("""
                    INSERT INTO tahsilat (musteri_id, tutar_kurus, odeme_tipi, aciklama, kullanici_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (musteri_id, tutar_kurus, odeme_tipi, aciklama.strip(), kullanici_id))
                tahsilat_id = cur.lastrowid

                # Müşteri bakiyesinden düş (borcu azalt)
                cur.execute("""
                    UPDATE musteri SET bakiye_kurus = bakiye_kurus - ? WHERE id = ?
                """, (tutar_kurus, musteri_id))

            conn.close()
            return tahsilat_id
        except Exception as e:
            conn.close()
            raise e

    def musteri_ekstresi_getir(self, musteri_id: int) -> list[dict[str, Any]]:
        """Müşterinin veresiye siparişleri ve tahsilatlarını kronolojik ekstre olarak döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        # Veresiye siparişler (Borç)
        cur.execute("""
            SELECT id, tarih, siparis_no as belge_no, 'Veresiye Satış' as islem,
                   genel_toplam_kurus as borc_kurus, 0 as alacak_kurus, aciklama
            FROM siparis
            WHERE musteri_id = ? AND odeme_tipi = 'veresiye' AND durum != 'iptal'
        """, (musteri_id,))
        siparisler = [dict(r) for r in cur.fetchall()]

        # Tahsilatlar (Alacak)
        cur.execute("""
            SELECT id, tarih, ('THS-' || id) as belge_no, ('Tahsilat (' || odeme_tipi || ')') as islem,
                   0 as borc_kurus, tutar_kurus as alacak_kurus, aciklama
            FROM tahsilat
            WHERE musteri_id = ?
        """, (musteri_id,))
        tahsilatlar = [dict(r) for r in cur.fetchall()]

        conn.close()

        tum_islemler = sorted(siparisler + tahsilatlar, key=lambda x: str(x["tarih"]))
        bakiye = 0
        for islem in tum_islemler:
            bakiye += islem["borc_kurus"] - islem["alacak_kurus"]
            islem["yuruyen_bakiye_kurus"] = bakiye

        return tum_islemler

    @staticmethod
    def _satiri_musteriye_cevir(row: sqlite3.Row) -> Musteri:
        return Musteri(
            id=row["id"],
            ad_soyad=row["ad_soyad"],
            telefon=row["telefon"] or "",
            eposta=row["eposta"] or "",
            adres=row["adres"] or "",
            vergi_no_tc=row["vergi_no_tc"] or "",
            bakiye_kurus=row["bakiye_kurus"],
            aktif=row["aktif"]
        )
