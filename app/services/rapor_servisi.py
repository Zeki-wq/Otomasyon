"""
Kasa, Ciro, Satış ve En Çok Satanlar Raporlama Servisi
"""

from datetime import date
from pathlib import Path
from typing import Any

from app.db.connection import get_db_connection


class RaporServisi:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def gunluk_kasa_ozeti(self, hedef_tarih: str | None = None) -> dict[str, Any]:
        """
        Belirtilen günün kasa hareketlerini özetler.
        Nakit Satışlar, Kartlı Satışlar, Veresiye Satışlar, Nakit Tahsilatlar, Kartlı Tahsilatlar, Toplam Giriş.
        """
        if not hedef_tarih:
            hedef_tarih = date.today().strftime("%Y-%m-%d")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        # Günlük tamamlanan siparişler
        cur.execute("""
            SELECT odeme_tipi,
                   COALESCE(SUM(genel_toplam_kurus), 0) as toplam_kurus,
                   COUNT(*) as adet
            FROM siparis
            WHERE DATE(tarih) = DATE(?) AND durum = 'tamamlandi'
            GROUP BY odeme_tipi
        """, (hedef_tarih,))
        sip_rows = cur.fetchall()

        nakit_satis_kurus = 0
        kart_satis_kurus = 0
        veresiye_satis_kurus = 0
        toplam_siparis_adedi = 0

        for r in sip_rows:
            toplam_siparis_adedi += r["adet"]
            if r["odeme_tipi"] == "nakit":
                nakit_satis_kurus = r["toplam_kurus"]
            elif r["odeme_tipi"] == "kart":
                kart_satis_kurus = r["toplam_kurus"]
            elif r["odeme_tipi"] == "veresiye":
                veresiye_satis_kurus = r["toplam_kurus"]

        # Günlük tahsilatlar
        cur.execute("""
            SELECT odeme_tipi,
                   COALESCE(SUM(tutar_kurus), 0) as toplam_kurus,
                   COUNT(*) as adet
            FROM tahsilat
            WHERE DATE(tarih) = DATE(?)
            GROUP BY odeme_tipi
        """, (hedef_tarih,))
        tah_rows = cur.fetchall()

        nakit_tahsilat_kurus = 0
        kart_tahsilat_kurus = 0
        for r in tah_rows:
            if r["odeme_tipi"] == "nakit":
                nakit_tahsilat_kurus = r["toplam_kurus"]
            elif r["odeme_tipi"] == "kart":
                kart_tahsilat_kurus = r["toplam_kurus"]

        conn.close()

        net_nakit_kasa = nakit_satis_kurus + nakit_tahsilat_kurus
        net_banka_kart = kart_satis_kurus + kart_tahsilat_kurus
        toplam_ciro = nakit_satis_kurus + kart_satis_kurus + veresiye_satis_kurus

        return {
            "tarih": hedef_tarih,
            "toplam_siparis_adedi": toplam_siparis_adedi,
            "nakit_satis_kurus": nakit_satis_kurus,
            "kart_satis_kurus": kart_satis_kurus,
            "veresiye_satis_kurus": veresiye_satis_kurus,
            "toplam_ciro_kurus": toplam_ciro,
            "nakit_tahsilat_kurus": nakit_tahsilat_kurus,
            "kart_tahsilat_kurus": kart_tahsilat_kurus,
            "net_nakit_kasa_kurus": net_nakit_kasa,
            "net_banka_kart_kurus": net_banka_kart,
            "gunluk_toplam_tahsilat_kurus": net_nakit_kasa + net_banka_kart
        }

    def satis_raporu(self, baslangic: str, bitis: str) -> dict[str, Any]:
        """Tarih aralığında genel satış ve kâr analizini döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COUNT(CASE WHEN durum = 'tamamlandi' THEN 1 END) as tamamlanan_siparis,
                COUNT(CASE WHEN durum = 'iptal' THEN 1 END) as iptal_siparis,
                COALESCE(SUM(CASE WHEN durum = 'tamamlandi' THEN ara_toplam_kurus ELSE 0 END), 0) as toplam_matrah,
                COALESCE(SUM(CASE WHEN durum = 'tamamlandi' THEN kdv_toplam_kurus ELSE 0 END), 0) as toplam_kdv,
                COALESCE(SUM(CASE WHEN durum = 'tamamlandi' THEN genel_toplam_kurus ELSE 0 END), 0) as genel_toplam
            FROM siparis
            WHERE DATE(tarih) >= DATE(?) AND DATE(tarih) <= DATE(?)
        """, (baslangic, bitis))
        row = cur.fetchone()

        # Maliyet ve kâr hesabı
        cur.execute("""
            SELECT COALESCE(SUM(sk.adet * u.alis_fiyati_kurus), 0) as toplam_maliyet
            FROM siparis_kalem sk
            JOIN siparis s ON sk.siparis_id = s.id
            LEFT JOIN urun u ON sk.urun_id = u.id
            WHERE s.durum = 'tamamlandi' AND DATE(s.tarih) >= DATE(?) AND DATE(s.tarih) <= DATE(?)
        """, (baslangic, bitis))
        maliyet_row = cur.fetchone()
        conn.close()

        toplam_maliyet = maliyet_row["toplam_maliyet"]
        brut_kar = row["toplam_matrah"] - toplam_maliyet

        return {
            "baslangic": baslangic,
            "bitis": bitis,
            "tamamlanan_siparis": row["tamamlanan_siparis"],
            "iptal_siparis": row["iptal_siparis"],
            "toplam_matrah_kurus": row["toplam_matrah"],
            "toplam_kdv_kurus": row["toplam_kdv"],
            "genel_toplam_kurus": row["genel_toplam"],
            "toplam_maliyet_kurus": toplam_maliyet,
            "brut_kar_kurus": brut_kar
        }

    def en_cok_satanlar(
        self,
        limit: int = 10,
        baslangic: str | None = None,
        bitis: str | None = None
    ) -> list[dict[str, Any]]:
        """En çok satan ürünleri adet ve ciroya göre sıralar."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        kosullar = ["s.durum = 'tamamlandi'"]
        parametreler = []

        if baslangic:
            kosullar.append("DATE(s.tarih) >= DATE(?)")
            parametreler.append(baslangic)
        if bitis:
            kosullar.append("DATE(s.tarih) <= DATE(?)")
            parametreler.append(bitis)

        where_clause = " WHERE " + " AND ".join(kosullar)
        sql = f"""
            SELECT
                sk.urun_adi_anlik as urun_adi,
                sk.parca_kodu_anlik as parca_kodu,
                SUM(sk.adet) as toplam_adet,
                SUM(sk.toplam_kurus) as toplam_ciro_kurus
            FROM siparis_kalem sk
            JOIN siparis s ON sk.siparis_id = s.id
            {where_clause}
            GROUP BY sk.urun_adi_anlik, sk.parca_kodu_anlik
            ORDER BY toplam_adet DESC
            LIMIT ?
        """
        parametreler.append(limit)

        cur.execute(sql, parametreler)
        rows = cur.fetchall()
        conn.close()

        return [dict(r) for r in rows]
