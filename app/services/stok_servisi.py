"""
Stok Hareketleri, Envanter ve Kritik Stok Servisi
"""

from pathlib import Path

from app.db.connection import get_db_connection
from app.domain.models import StokHareket, Urun


class StokServisi:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def stok_duzeltme_yap(
        self,
        urun_id: int,
        yeni_stok: int,
        aciklama: str,
        kullanici_id: int | None = None
    ) -> bool:
        """
        Sayım sonrası veya manuel stok düzeltmesi yapar.
        Tek transaction içinde stok güncellenir ve stok hareketine kaydedilir.
        """
        if yeni_stok < 0:
            raise ValueError("Stok miktarı negatif olamaz.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            with conn:
                cur.execute("SELECT stok FROM urun WHERE id = ?", (urun_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("Ürün bulunamadı.")

                onceki_stok = row["stok"]
                degisim = yeni_stok - onceki_stok

                if degisim == 0:
                    conn.close()
                    return True

                cur.execute("UPDATE urun SET stok = ? WHERE id = ?", (yeni_stok, urun_id))

                cur.execute("""
                    INSERT INTO stok_hareket (
                        urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                        referans_tipi, referans_id, kullanici_id, aciklama
                    ) VALUES (?, 'sayim_duzeltme', ?, ?, ?, 'manuel', NULL, ?, ?)
                """, (urun_id, degisim, onceki_stok, yeni_stok, kullanici_id, aciklama.strip()))

            conn.close()
            return True
        except Exception as e:
            conn.close()
            raise e

    def stok_hareketlerini_getir(
        self,
        urun_id: int | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[StokHareket]:
        """Stok hareket defterini döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        sql = """
            SELECT sh.*, u.ad as urun_adi, u.parca_kodu
            FROM stok_hareket sh
            JOIN urun u ON sh.urun_id = u.id
        """
        parametreler = []
        if urun_id:
            sql += " WHERE sh.urun_id = ?"
            parametreler.append(urun_id)

        sql += " ORDER BY sh.id DESC LIMIT ? OFFSET ?"
        parametreler.extend([limit, offset])

        cur.execute(sql, parametreler)
        rows = cur.fetchall()
        conn.close()

        return [
            StokHareket(
                id=r["id"],
                urun_id=r["urun_id"],
                hareket_tipi=r["hareket_tipi"],
                adet_degisim=r["adet_degisim"],
                onceki_stok=r["onceki_stok"],
                sonraki_stok=r["sonraki_stok"],
                referans_tipi=r["referans_tipi"],
                referans_id=r["referans_id"],
                kullanici_id=r["kullanici_id"],
                tarih=str(r["tarih"]),
                aciklama=r["aciklama"] or "",
                urun_adi=r["urun_adi"],
                parca_kodu=r["parca_kodu"]
            )
            for r in rows
        ]

    def kritik_stok_urunleri_getir(self) -> list[Urun]:
        """Stoğu kritik seviyenin altında veya eşit olan aktif ürünleri döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.*, k.ad as kategori_adi, m.ad as marka_adi
            FROM urun u
            LEFT JOIN kategori k ON u.kategori_id = k.id
            LEFT JOIN marka m ON u.marka_id = m.id
            WHERE u.aktif = 1 AND u.stok <= u.kritik_stok
            ORDER BY u.stok ASC
        """)
        rows = cur.fetchall()
        conn.close()
        from app.services.urun_servisi import UrunServisi
        return [UrunServisi._satiri_urune_cevir(r) for r in rows]

    def kritik_stok_sayisi(self) -> int:
        """Kritik stoktaki ürün sayısını döner (rozet gösterimi için)."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM urun WHERE aktif = 1 AND stok <= kritik_stok")
        sayi = cur.fetchone()[0]
        conn.close()
        return sayi

    def toplam_stok_degeri(self) -> dict:
        """Depodaki toplam ürün, toplam adet, maliyet değeri ve satış değerini hesaplar."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) as toplam_kalem,
                COALESCE(SUM(stok), 0) as toplam_adet,
                COALESCE(SUM(stok * alis_fiyati_kurus), 0) as maliyet_kurus,
                COALESCE(SUM(stok * satis_fiyati_kurus), 0) as satis_kurus
            FROM urun
            WHERE aktif = 1
        """)
        row = cur.fetchone()
        conn.close()
        return {
            "toplam_kalem": row["toplam_kalem"],
            "toplam_adet": row["toplam_adet"],
            "maliyet_kurus": row["maliyet_kurus"],
            "satis_kurus": row["satis_kurus"]
        }
