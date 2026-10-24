"""
Satış, Sepet ve Sipariş Yönetim Servisi
Tüm stok düşümü ve sipariş kayıtları tek transaction içinde atomik yürütülür.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from app.db.connection import get_db_connection
from app.domain.models import Siparis, SiparisKalem
from app.domain.money import kdv_hesapla


class SatisServisi:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def siparis_olustur(
        self,
        kalemler: list[dict[str, Any]],
        musteri_id: int | None = None,
        odeme_tipi: str = "nakit",
        aciklama: str = "",
        kullanici_id: int | None = None
    ) -> Siparis:
        """
        Sepetteki kalemlerle yeni sipariş oluşturur.
        İşlem atomiktir: Stok kontrolü -> Sipariş kaydı -> Stok düşümü -> Stok hareketi.
        Herhangi bir kalemde yetersiz stok veya hata varsa HİÇBİR DEĞİŞİKLİK YAPILMAZ.
        """
        if not kalemler:
            raise ValueError("Sipariş için en az 1 ürün kalemi olmalıdır.")

        if odeme_tipi not in ("nakit", "kart", "veresiye"):
            raise ValueError("Geçersiz ödeme tipi. 'nakit', 'kart' veya 'veresiye' olmalıdır.")

        if odeme_tipi == "veresiye" and not musteri_id:
            raise ValueError("Veresiye satış yapılabilmesi için bir müşteri seçilmelidir.")

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        try:
            with conn:
                # 1. Müşteri Kontrolü (varsa)
                musteri_adi = ""
                if musteri_id:
                    cur.execute("SELECT ad_soyad FROM musteri WHERE id = ? AND aktif = 1", (musteri_id,))
                    m_row = cur.fetchone()
                    if not m_row:
                        raise ValueError("Seçilen müşteri bulunamadı veya pasif durumda.")
                    musteri_adi = m_row["ad_soyad"]

                # 2. Ürünlerin ve Stokların Atomik Doğrulaması
                onayli_kalemler = []
                toplam_matrah = 0
                toplam_kdv = 0

                for item in kalemler:
                    urun_id = item.get("urun_id")
                    adet = int(item.get("adet", 1))
                    if adet <= 0:
                        raise ValueError("Ürün adedi 0'dan büyük olmalıdır.")

                    cur.execute("""
                        SELECT id, parca_kodu, ad, stok, satis_fiyati_kurus, kdv_orani
                        FROM urun
                        WHERE id = ? AND aktif = 1
                    """, (urun_id,))
                    urun_row = cur.fetchone()

                    if not urun_row:
                        raise ValueError(f"ID {urun_id} numaralı ürün depoda bulunamadı!")

                    mevcut_stok = urun_row["stok"]
                    if mevcut_stok < adet:
                        raise ValueError(
                            f"Yetersiz stok! '{urun_row['ad']}' için depoda {mevcut_stok} adet var, "
                            f"{adet} adet istendi."
                        )

                    # Birim fiyat verilmemişse veritabanındaki satış fiyatını al
                    birim_fiyat = item.get("birim_fiyat_kurus")
                    if birim_fiyat is None or birim_fiyat < 0:
                        birim_fiyat = urun_row["satis_fiyati_kurus"]

                    kdv_orani = item.get("kdv_orani")
                    if kdv_orani is None:
                        kdv_orani = urun_row["kdv_orani"]

                    kalem_matrah = adet * birim_fiyat
                    kalem_kdv, _ = kdv_hesapla(kalem_matrah, kdv_orani)

                    toplam_matrah += kalem_matrah
                    toplam_kdv += kalem_kdv

                    onayli_kalemler.append({
                        "urun_id": urun_row["id"],
                        "parca_kodu": urun_row["parca_kodu"],
                        "ad": urun_row["ad"],
                        "adet": adet,
                        "mevcut_stok": mevcut_stok,
                        "birim_fiyat_kurus": birim_fiyat,
                        "kdv_orani": kdv_orani,
                        "toplam_kurus": kalem_matrah
                    })

                genel_toplam = toplam_matrah + toplam_kdv

                # 3. Benzersiz Sipariş Numarası Üret
                simdi_str = datetime.now().strftime("%Y%m%d%H%M%S")
                cur.execute("SELECT COUNT(*) FROM siparis")
                toplam_sip = cur.fetchone()[0] + 1
                siparis_no = f"SIP-{simdi_str}-{toplam_sip:04d}"

                # 4. Sipariş Başlığını Kaydet
                cur.execute("""
                    INSERT INTO siparis (
                        siparis_no, musteri_id, tarih, durum, odeme_tipi,
                        ara_toplam_kurus, kdv_toplam_kurus, genel_toplam_kurus,
                        aciklama, kullanici_id
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, 'tamamlandi', ?, ?, ?, ?, ?, ?)
                """, (
                    siparis_no,
                    musteri_id,
                    odeme_tipi,
                    toplam_matrah,
                    toplam_kdv,
                    genel_toplam,
                    aciklama.strip(),
                    kullanici_id
                ))
                siparis_id = cur.lastrowid

                # 5. Kalemleri Kaydet, Stokları Düş ve Stok Hareketlerini Yaz
                olusturulan_kalemler = []
                for k in onayli_kalemler:
                    cur.execute("""
                        INSERT INTO siparis_kalem (
                            siparis_id, urun_id, urun_adi_anlik, parca_kodu_anlik,
                            adet, birim_fiyat_kurus, kdv_orani, toplam_kurus
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        siparis_id,
                        k["urun_id"],
                        k["ad"],
                        k["parca_kodu"],
                        k["adet"],
                        k["birim_fiyat_kurus"],
                        k["kdv_orani"],
                        k["toplam_kurus"]
                    ))
                    kalem_id = cur.lastrowid

                    olusturulan_kalemler.append(
                        SiparisKalem(
                            id=kalem_id,
                            siparis_id=siparis_id,
                            urun_id=k["urun_id"],
                            urun_adi_anlik=k["ad"],
                            parca_kodu_anlik=k["parca_kodu"],
                            adet=k["adet"],
                            birim_fiyat_kurus=k["birim_fiyat_kurus"],
                            kdv_orani=k["kdv_orani"],
                            toplam_kurus=k["toplam_kurus"]
                        )
                    )

                    # Stok düşümü
                    yeni_stok = k["mevcut_stok"] - k["adet"]
                    cur.execute("UPDATE urun SET stok = ? WHERE id = ?", (yeni_stok, k["urun_id"]))

                    # Stok hareketi defterine kaydet
                    cur.execute("""
                        INSERT INTO stok_hareket (
                            urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                            referans_tipi, referans_id, kullanici_id, aciklama
                        ) VALUES (?, 'satis', ?, ?, ?, 'siparis', ?, ?, ?)
                    """, (
                        k["urun_id"],
                        -k["adet"],
                        k["mevcut_stok"],
                        yeni_stok,
                        siparis_id,
                        kullanici_id,
                        f"Satış siparişi #{siparis_no}"
                    ))

                # 6. Veresiye ise Müşteri Bakiyesini Artır
                if odeme_tipi == "veresiye" and musteri_id:
                    cur.execute("""
                        UPDATE musteri
                        SET bakiye_kurus = bakiye_kurus + ?
                        WHERE id = ?
                    """, (genel_toplam, musteri_id))

            conn.close()

            return Siparis(
                id=siparis_id,
                siparis_no=siparis_no,
                musteri_id=musteri_id,
                tarih=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                durum="tamamlandi",
                odeme_tipi=odeme_tipi,
                ara_toplam_kurus=toplam_matrah,
                kdv_toplam_kurus=toplam_kdv,
                genel_toplam_kurus=genel_toplam,
                aciklama=aciklama,
                kullanici_id=kullanici_id,
                musteri_adi=musteri_adi,
                kalemler=olusturulan_kalemler
            )

        except Exception as e:
            conn.close()
            raise e

    def siparis_iptal_et(
        self,
        siparis_id: int,
        aciklama: str = "",
        kullanici_id: int | None = None
    ) -> bool:
        """
        Siparişi iptal eder ve tüm kalemlerin stoğunu atomik olarak geri iade eder.
        Veresiye satılmışsa müşteri bakiyesinden geri düşer.
        """
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        try:
            with conn:
                cur.execute("SELECT * FROM siparis WHERE id = ?", (siparis_id,))
                siparis = cur.fetchone()
                if not siparis:
                    raise ValueError("Sipariş bulunamadı.")

                if siparis["durum"] == "iptal":
                    raise ValueError("Bu sipariş zaten iptal edilmiş.")

                siparis_no = siparis["siparis_no"]
                odeme_tipi = siparis["odeme_tipi"]
                genel_toplam = siparis["genel_toplam_kurus"]
                musteri_id = siparis["musteri_id"]

                # Durumu iptal yap
                cur.execute("UPDATE siparis SET durum = 'iptal' WHERE id = ?", (siparis_id,))

                # Kalemleri al
                cur.execute("SELECT * FROM siparis_kalem WHERE siparis_id = ?", (siparis_id,))
                kalemler = cur.fetchall()

                for kalem in kalemler:
                    urun_id = kalem["urun_id"]
                    adet = kalem["adet"]

                    if urun_id:
                        cur.execute("SELECT stok FROM urun WHERE id = ?", (urun_id,))
                        u_row = cur.fetchone()
                        if u_row:
                            onceki_stok = u_row["stok"]
                            sonraki_stok = onceki_stok + adet

                            cur.execute("UPDATE urun SET stok = ? WHERE id = ?", (sonraki_stok, urun_id))

                            cur.execute("""
                                INSERT INTO stok_hareket (
                                    urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                                    referans_tipi, referans_id, kullanici_id, aciklama
                                ) VALUES (?, 'iptal', ?, ?, ?, 'siparis', ?, ?, ?)
                            """, (
                                urun_id,
                                adet,
                                onceki_stok,
                                sonraki_stok,
                                siparis_id,
                                kullanici_id,
                                f"İptal edilen sipariş #{siparis_no}: {aciklama}"
                            ))

                # Veresiye ise borcu geri düş
                if odeme_tipi == "veresiye" and musteri_id:
                    cur.execute("""
                        UPDATE musteri
                        SET bakiye_kurus = bakiye_kurus - ?
                        WHERE id = ?
                    """, (genel_toplam, musteri_id))

            conn.close()
            return True

        except Exception as e:
            conn.close()
            raise e

    def siparisleri_getir(
        self,
        musteri_id: int | None = None,
        durum: str | None = None,
        baslangic_tarih: str | None = None,
        bitis_tarih: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Siparis]:
        """Filtreli sipariş listesini döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        kosullar = []
        parametreler = []

        if musteri_id:
            kosullar.append("s.musteri_id = ?")
            parametreler.append(musteri_id)

        if durum:
            kosullar.append("s.durum = ?")
            parametreler.append(durum)

        if baslangic_tarih:
            kosullar.append("s.tarih >= ?")
            parametreler.append(baslangic_tarih)

        if bitis_tarih:
            kosullar.append("s.tarih <= ?")
            parametreler.append(f"{bitis_tarih} 23:59:59")

        where_clause = " WHERE " + " AND ".join(kosullar) if kosullar else ""
        sql = f"""
            SELECT s.*, m.ad_soyad as musteri_adi, k.ad_soyad as kullanici_adi
            FROM siparis s
            LEFT JOIN musteri m ON s.musteri_id = m.id
            LEFT JOIN kullanici k ON s.kullanici_id = k.id
            {where_clause}
            ORDER BY s.id DESC
            LIMIT ? OFFSET ?
        """
        parametreler.extend([limit, offset])

        cur.execute(sql, parametreler)
        rows = cur.fetchall()
        conn.close()

        return [
            Siparis(
                id=r["id"],
                siparis_no=r["siparis_no"],
                musteri_id=r["musteri_id"],
                tarih=str(r["tarih"]),
                durum=r["durum"],
                odeme_tipi=r["odeme_tipi"],
                ara_toplam_kurus=r["ara_toplam_kurus"],
                kdv_toplam_kurus=r["kdv_toplam_kurus"],
                genel_toplam_kurus=r["genel_toplam_kurus"],
                aciklama=r["aciklama"] or "",
                kullanici_id=r["kullanici_id"],
                musteri_adi=r["musteri_adi"] or "Perakende Müşteri",
                kullanici_adi=r["kullanici_adi"] or ""
            )
            for r in rows
        ]

    def siparis_detay_getir(self, siparis_id: int) -> Siparis | None:
        """Tek siparişi kalemleriyle birlikte döner."""
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT s.*, m.ad_soyad as musteri_adi, k.ad_soyad as kullanici_adi
            FROM siparis s
            LEFT JOIN musteri m ON s.musteri_id = m.id
            LEFT JOIN kullanici k ON s.kullanici_id = k.id
            WHERE s.id = ?
        """, (siparis_id,))
        s_row = cur.fetchone()

        if not s_row:
            conn.close()
            return None

        cur.execute("""
            SELECT * FROM siparis_kalem WHERE siparis_id = ? ORDER BY id ASC
        """, (siparis_id,))
        k_rows = cur.fetchall()
        conn.close()

        kalemler = [
            SiparisKalem(
                id=k["id"],
                siparis_id=k["siparis_id"],
                urun_id=k["urun_id"],
                urun_adi_anlik=k["urun_adi_anlik"],
                parca_kodu_anlik=k["parca_kodu_anlik"] or "",
                adet=k["adet"],
                birim_fiyat_kurus=k["birim_fiyat_kurus"],
                kdv_orani=k["kdv_orani"],
                toplam_kurus=k["toplam_kurus"]
            )
            for k in k_rows
        ]

        return Siparis(
            id=s_row["id"],
            siparis_no=s_row["siparis_no"],
            musteri_id=s_row["musteri_id"],
            tarih=str(s_row["tarih"]),
            durum=s_row["durum"],
            odeme_tipi=s_row["odeme_tipi"],
            ara_toplam_kurus=s_row["ara_toplam_kurus"],
            kdv_toplam_kurus=s_row["kdv_toplam_kurus"],
            genel_toplam_kurus=s_row["genel_toplam_kurus"],
            aciklama=s_row["aciklama"] or "",
            kullanici_id=s_row["kullanici_id"],
            musteri_adi=s_row["musteri_adi"] or "Perakende Müşteri",
            kullanici_adi=s_row["kullanici_adi"] or "",
            kalemler=kalemler
        )
