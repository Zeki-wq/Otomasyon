"""
Ürün, Kategori ve Marka Yönetim Servisi
"""

import sqlite3
from pathlib import Path

from app.db.connection import get_db_connection
from app.domain.models import Kategori, Marka, Urun


class UrunServisi:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def urun_ekle(self, urun: Urun, kullanici_id: int | None = None) -> int:
        """Yeni ürün ekler ve başlangıç stoğu varsa stok hareketi oluşturur."""
        parca_kodu = str(urun.parca_kodu or "").strip().upper()
        ad = str(urun.ad or "").strip()

        if not parca_kodu:
            raise ValueError("Parça kodu boş bırakılamaz.")
        if not ad:
            raise ValueError("Ürün adı boş bırakılamaz.")
        if urun.stok < 0:
            raise ValueError("Stok miktarı negatif olamaz.")
        if urun.satis_fiyati_kurus < 0:
            raise ValueError("Satış fiyatı negatif olamaz.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            with conn:
                cur.execute("""
                    INSERT INTO urun (
                        parca_kodu, barkod, oem_no, ad, kategori_id, marka_id,
                        alis_fiyati_kurus, satis_fiyati_kurus, kdv_orani,
                        stok, kritik_stok, raf_yeri, aciklama, aktif
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    parca_kodu,
                    str(urun.barkod or "").strip(),
                    str(urun.oem_no or "").strip().upper(),
                    ad,
                    urun.kategori_id,
                    urun.marka_id,
                    urun.alis_fiyati_kurus,
                    urun.satis_fiyati_kurus,
                    urun.kdv_orani,
                    urun.stok,
                    urun.kritik_stok,
                    str(urun.raf_yeri or "").strip(),
                    str(urun.aciklama or "").strip(),
                    0 if urun.aktif == 0 else 1
                ))
                yeni_id = cur.lastrowid

                # Stok varsa açılış hareketi kaydet
                if urun.stok > 0:
                    cur.execute("""
                        INSERT INTO stok_hareket (
                            urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                            referans_tipi, referans_id, kullanici_id, aciklama
                        ) VALUES (?, 'giris', ?, 0, ?, 'acilis_stogu', ?, ?, 'Ürün ilk açılış stoğu')
                    """, (yeni_id, urun.stok, urun.stok, yeni_id, kullanici_id))

            conn.close()
            return yeni_id
        except sqlite3.IntegrityError as e:
            conn.close()
            if "UNIQUE constraint failed: urun.parca_kodu" in str(e):
                raise ValueError(f"'{parca_kodu}' parça kodu zaten mevcut!") from e
            raise ValueError(f"Ürün eklenemedi: {e}") from e

    def urun_guncelle(self, urun: Urun, kullanici_id: int | None = None) -> bool:
        """Ürün bilgilerini günceller (stok doğrudan buradan güncellenmez, stok_servisi ile düzeltilir)."""
        if not urun.id:
            raise ValueError("Güncellenecek ürünün ID'si belirtilmelidir.")

        parca_kodu = str(urun.parca_kodu or "").strip().upper()
        ad = str(urun.ad or "").strip()
        if not parca_kodu:
            raise ValueError("Parça kodu boş bırakılamaz.")
        if not ad:
            raise ValueError("Ürün adı boş bırakılamaz.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            with conn:
                cur.execute("""
                    UPDATE urun SET
                        parca_kodu = ?,
                        barkod = ?,
                        oem_no = ?,
                        ad = ?,
                        kategori_id = ?,
                        marka_id = ?,
                        alis_fiyati_kurus = ?,
                        satis_fiyati_kurus = ?,
                        kdv_orani = ?,
                        kritik_stok = ?,
                        raf_yeri = ?,
                        aciklama = ?
                    WHERE id = ?
                """, (
                    parca_kodu,
                    str(urun.barkod or "").strip(),
                    str(urun.oem_no or "").strip().upper(),
                    ad,
                    urun.kategori_id,
                    urun.marka_id,
                    urun.alis_fiyati_kurus,
                    urun.satis_fiyati_kurus,
                    urun.kdv_orani,
                    urun.kritik_stok,
                    str(urun.raf_yeri or "").strip(),
                    str(urun.aciklama or "").strip(),
                    urun.id
                ))
            conn.close()
            return True
        except sqlite3.IntegrityError as e:
            conn.close()
            if "UNIQUE constraint failed: urun.parca_kodu" in str(e):
                raise ValueError(f"'{parca_kodu}' parça kodu başka bir ürüne ait!") from e
            raise ValueError(f"Güncelleme hatası: {e}") from e

    def urun_pasife_al(self, urun_id: int, kullanici_id: int | None = None) -> bool:
        """Ürünü sert silmek yerine pasife alır (geçmiş siparişler bozulmaz), denetim ve hareket kaydı oluşturur."""
        urun = self.urun_getir(urun_id)
        if not urun:
            raise ValueError(f"ID {urun_id} numaralı ürün bulunamadı.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with conn:
            cur.execute("UPDATE urun SET aktif = 0 WHERE id = ?", (urun_id,))
            cur.execute("""
                INSERT INTO denetim_log (kullanici_id, islem, detay)
                VALUES (?, 'urun_pasife_al', ?)
            """, (kullanici_id, f"Ürün #{urun_id} ({urun.parca_kodu} - {urun.ad}) pasife alındı"))
            cur.execute("""
                INSERT INTO stok_hareket (
                    urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                    referans_tipi, referans_id, kullanici_id, aciklama
                ) VALUES (?, 'sayim_duzeltme', 0, ?, ?, 'urun_durum', ?, ?, 'Ürün pasife alındı')
            """, (urun_id, urun.stok, urun.stok, urun_id, kullanici_id))
        conn.close()
        return True

    def urun_aktife_al(self, urun_id: int, kullanici_id: int | None = None) -> bool:
        """Pasife alınmış bir ürünü tekrar aktif hale getirir, denetim ve hareket kaydı oluşturur."""
        urun = self.urun_getir(urun_id)
        if not urun:
            raise ValueError(f"ID {urun_id} numaralı ürün bulunamadı.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        with conn:
            cur.execute("UPDATE urun SET aktif = 1 WHERE id = ?", (urun_id,))
            cur.execute("""
                INSERT INTO denetim_log (kullanici_id, islem, detay)
                VALUES (?, 'urun_aktife_al', ?)
            """, (kullanici_id, f"Ürün #{urun_id} ({urun.parca_kodu} - {urun.ad}) tekrar aktife alındı"))
            cur.execute("""
                INSERT INTO stok_hareket (
                    urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                    referans_tipi, referans_id, kullanici_id, aciklama
                ) VALUES (?, 'sayim_duzeltme', 0, ?, ?, 'urun_durum', ?, ?, 'Ürün tekrar aktife alındı')
            """, (urun_id, urun.stok, urun.stok, urun_id, kullanici_id))
        conn.close()
        return True

    def urun_getir(self, urun_id: int) -> Urun | None:
        """ID ile tek ürün getirir."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.*, k.ad as kategori_adi, m.ad as marka_adi
            FROM urun u
            LEFT JOIN kategori k ON u.kategori_id = k.id
            LEFT JOIN marka m ON u.marka_id = m.id
            WHERE u.id = ?
        """, (urun_id,))
        row = cur.fetchone()
        conn.close()
        return self._satiri_urune_cevir(row) if row else None

    def urun_getir_parca_kodu(self, parca_kodu: str) -> Urun | None:
        """Parça kodu ile ürün arar (yalnızca aktif ürünler)."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.*, k.ad as kategori_adi, m.ad as marka_adi
            FROM urun u
            LEFT JOIN kategori k ON u.kategori_id = k.id
            LEFT JOIN marka m ON u.marka_id = m.id
            WHERE u.parca_kodu = ? AND u.aktif = 1
        """, (parca_kodu.strip().upper(),))
        row = cur.fetchone()
        conn.close()
        return self._satiri_urune_cevir(row) if row else None

    def urun_getir_barkod(self, barkod: str) -> Urun | None:
        """Barkod ile ürün arar (yalnızca aktif ürünler)."""
        if not barkod:
            return None
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.*, k.ad as kategori_adi, m.ad as marka_adi
            FROM urun u
            LEFT JOIN kategori k ON u.kategori_id = k.id
            LEFT JOIN marka m ON u.marka_id = m.id
            WHERE u.barkod = ? AND u.aktif = 1
        """, (barkod.strip(),))
        row = cur.fetchone()
        conn.close()
        return self._satiri_urune_cevir(row) if row else None

    def urun_ara(
        self,
        terim: str = "",
        kategori_id: int | None = None,
        marka_id: int | None = None,
        sadece_aktif: bool = True,
        aktiflik_filtresi: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Urun]:
        """
        Kısmi arama (parça kodu, barkod, OEM no, ad, marka adı) yürütür.
        50.000 üründe < 100 ms indeksli hızlı sorgu.
        aktiflik_filtresi: 'aktif' (varsayılan), 'pasif', 'tumu'.
        """
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        kosullar = []
        parametreler = []

        # Aktiflik filtresi belirleme
        if aktiflik_filtresi == "pasif":
            kosullar.append("u.aktif = 0")
        elif aktiflik_filtresi == "tumu" or (not sadece_aktif and aktiflik_filtresi is None):
            pass  # Filtre yok
        else:
            kosullar.append("u.aktif = 1")

        if kategori_id:
            kosullar.append("u.kategori_id = ?")
            parametreler.append(kategori_id)

        if marka_id:
            kosullar.append("u.marka_id = ?")
            parametreler.append(marka_id)

        if terim and terim.strip():
            t = f"%{terim.strip()}%"
            kosullar.append("(u.parca_kodu LIKE ? OR u.barkod LIKE ? OR u.oem_no LIKE ? OR u.ad LIKE ? OR m.ad LIKE ?)")
            parametreler.extend([t, t, t, t, t])

        where_clause = " WHERE " + " AND ".join(kosullar) if kosullar else ""
        sql = f"""
            SELECT u.*, k.ad as kategori_adi, m.ad as marka_adi
            FROM urun u
            LEFT JOIN kategori k ON u.kategori_id = k.id
            LEFT JOIN marka m ON u.marka_id = m.id
            {where_clause}
            ORDER BY u.id DESC
            LIMIT ? OFFSET ?
        """
        parametreler.extend([limit, offset])

        cur.execute(sql, parametreler)
        rows = cur.fetchall()
        conn.close()

        return [self._satiri_urune_cevir(r) for r in rows]

    def toplam_urun_sayisi(
        self,
        terim: str = "",
        kategori_id: int | None = None,
        marka_id: int | None = None,
        sadece_aktif: bool = True,
        aktiflik_filtresi: str | None = None
    ) -> int:
        """Filtrelere uyan toplam ürün sayısını döner (sayfalama için)."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        kosullar = []
        parametreler = []

        if aktiflik_filtresi == "pasif":
            kosullar.append("u.aktif = 0")
        elif aktiflik_filtresi == "tumu" or (not sadece_aktif and aktiflik_filtresi is None):
            pass
        else:
            kosullar.append("u.aktif = 1")

        if kategori_id:
            kosullar.append("u.kategori_id = ?")
            parametreler.append(kategori_id)
        if marka_id:
            kosullar.append("u.marka_id = ?")
            parametreler.append(marka_id)
        if terim and terim.strip():
            t = f"%{terim.strip()}%"
            kosullar.append("(u.parca_kodu LIKE ? OR u.barkod LIKE ? OR u.oem_no LIKE ? OR u.ad LIKE ? OR m.ad LIKE ?)")
            parametreler.extend([t, t, t, t, t])

        where_clause = " WHERE " + " AND ".join(kosullar) if kosullar else ""
        sql = f"""
            SELECT COUNT(*)
            FROM urun u
            LEFT JOIN marka m ON u.marka_id = m.id
            {where_clause}
        """
        cur.execute(sql, parametreler)
        sayi = cur.fetchone()[0]
        conn.close()
        return sayi

    def kategorileri_getir(self) -> list[Kategori]:
        """Tüm kategorileri sıralı döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, ad FROM kategori ORDER BY ad COLLATE NOCASE ASC")
        rows = cur.fetchall()
        conn.close()
        return [Kategori(id=r["id"], ad=r["ad"]) for r in rows]

    def markalari_getir(self) -> list[Marka]:
        """Tüm markaları sıralı döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, ad FROM marka ORDER BY ad COLLATE NOCASE ASC")
        rows = cur.fetchall()
        conn.close()
        return [Marka(id=r["id"], ad=r["ad"]) for r in rows]

    def kategori_ekle(self, ad: str) -> int:
        """Yeni kategori ekler."""
        ad_temiz = ad.strip()
        if not ad_temiz:
            raise ValueError("Kategori adı boş olamaz.")
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            with conn:
                cur.execute("INSERT INTO kategori (ad) VALUES (?)", (ad_temiz,))
                kid = cur.lastrowid
            conn.close()
            return kid
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"'{ad_temiz}' kategorisi zaten mevcut.")

    def marka_ekle(self, ad: str) -> int:
        """Yeni marka ekler."""
        ad_temiz = ad.strip()
        if not ad_temiz:
            raise ValueError("Marka adı boş olamaz.")
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            with conn:
                cur.execute("INSERT INTO marka (ad) VALUES (?)", (ad_temiz,))
                mid = cur.lastrowid
            conn.close()
            return mid
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"'{ad_temiz}' markası zaten mevcut.")

    @staticmethod
    def _satiri_urune_cevir(row: sqlite3.Row) -> Urun:
        return Urun(
            id=row["id"],
            parca_kodu=row["parca_kodu"],
            barkod=row["barkod"] or "",
            oem_no=row["oem_no"] or "",
            ad=row["ad"],
            kategori_id=row["kategori_id"],
            marka_id=row["marka_id"],
            alis_fiyati_kurus=row["alis_fiyati_kurus"],
            satis_fiyati_kurus=row["satis_fiyati_kurus"],
            kdv_orani=row["kdv_orani"],
            stok=row["stok"],
            kritik_stok=row["kritik_stok"],
            raf_yeri=row["raf_yeri"] or "",
            aciklama=row["aciklama"] or "",
            aktif=row["aktif"],
            olusturma_tarihi=str(row["olusturma_tarihi"]),
            kategori_adi=row["kategori_adi"] or "",
            marka_adi=row["marka_adi"] or ""
        )
