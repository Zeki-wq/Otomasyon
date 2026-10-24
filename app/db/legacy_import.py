"""
Eski Veritabanından (urunler12.db) Kayıpsız Veri Taşıma Modülü
Orijinal tablolardaki 2 ürün ve 17 sipariş kaydını yeni ilişkisel şemaya taşır.
İşlem idempotent'tir (birden fazla kez güvenle çağrılabilir).
"""

import sqlite3
from pathlib import Path
from typing import Optional, Union, NamedTuple
import logging
from app.db.connection import get_db_connection
from app.db.migrations.migrator import run_migrations

logger = logging.getLogger("otoyedekparca")


class LegacyImportResult(NamedTuple):
    basarili: bool
    urun_sayisi: int
    siparis_sayisi: int
    eslesen_siparis_sayisi: int
    eslesmeyen_siparis_sayisi: int
    mesaj: str


def import_legacy_database(
    legacy_db_path: Union[Path, str],
    target_db_path: Optional[Union[Path, str]] = None
) -> LegacyImportResult:
    """
    Eski SQLite veritabanındaki verileri yeni veritabanına taşır.
    - Şemayı günceller
    - Eski ürünleri aktarır ve stok hareketine açılış stoğu yazar
    - Eski siparişleri siparis ve siparis_kalem olarak aktarır
    - Eşleşmeyen sipariş kalemlerini isim kopyasıyla korur
    - İki kez çalıştırılırsa mükerrer kayıt oluşturmaz
    """
    legacy_file = Path(legacy_db_path)
    if not legacy_file.exists():
        return LegacyImportResult(
            basarili=False,
            urun_sayisi=0,
            siparis_sayisi=0,
            eslesen_siparis_sayisi=0,
            eslesmeyen_siparis_sayisi=0,
            mesaj=f"Eski veritabanı dosyası bulunamadı: {legacy_file}"
        )

    # Önce hedef veritabanında migrasyonların çalıştığından emin ol
    run_migrations(target_db_path)

    # Eski DB'ye bağlan
    conn_leg = sqlite3.connect(str(legacy_file))
    cur_leg = conn_leg.cursor()

    # Yeni DB'ye bağlan
    conn_new = get_db_connection(target_db_path)
    cur_new = conn_new.cursor()

    urun_sayisi = 0
    siparis_sayisi = 0
    eslesen_siparis_sayisi = 0
    eslesmeyen_siparis_sayisi = 0

    try:
        with conn_new:
            # 1. Kategori ve Marka Haritalarını Al
            cur_new.execute("SELECT id, ad FROM kategori")
            kategori_map = {row["ad"].lower(): row["id"] for row in cur_new.fetchall()}

            cur_new.execute("SELECT id, ad FROM marka")
            marka_map = {row["ad"].lower(): row["id"] for row in cur_new.fetchall()}

            # 2. ÜRÜN TABLOSUNU AKTAR
            cur_leg.execute("SELECT urunKodu, urunAdi, birimFiyat, stokMiktari, urunAciklama, marka, kategori FROM urun")
            eski_urunler = cur_leg.fetchall()

            for row in eski_urunler:
                eski_kod, eski_ad, eski_fiyat, eski_stok, eski_ack, eski_marka, eski_kat = row

                parca_kodu = f"PRC-{eski_kod:04d}" if isinstance(eski_kod, int) else f"PRC-{eski_kod}"
                ad = str(eski_ad).strip() if eski_ad else "İsimsiz Ürün"
                fiyat_kurus = int(eski_fiyat * 100) if eski_fiyat else 0
                stok = max(0, int(eski_stok)) if eski_stok else 0
                aciklama = str(eski_ack or "").strip()

                # Marka ve kategori ID bul veya oluştur
                kat_id = None
                if eski_kat and str(eski_kat).strip():
                    kat_adi = str(eski_kat).strip()
                    kat_id = kategori_map.get(kat_adi.lower())
                    if not kat_id:
                        cur_new.execute("INSERT OR IGNORE INTO kategori (ad) VALUES (?)", (kat_adi,))
                        cur_new.execute("SELECT id FROM kategori WHERE ad = ?", (kat_adi,))
                        kat_id = cur_new.fetchone()["id"]
                        kategori_map[kat_adi.lower()] = kat_id

                marka_id = None
                if eski_marka and str(eski_marka).strip():
                    m_adi = str(eski_marka).strip()
                    marka_id = marka_map.get(m_adi.lower())
                    if not marka_id:
                        cur_new.execute("INSERT OR IGNORE INTO marka (ad) VALUES (?)", (m_adi,))
                        cur_new.execute("SELECT id FROM marka WHERE ad = ?", (m_adi,))
                        marka_id = cur_new.fetchone()["id"]
                        marka_map[m_adi.lower()] = marka_id

                # Ürün var mı kontrol et (idempotency)
                cur_new.execute("SELECT id FROM urun WHERE parca_kodu = ?", (parca_kodu,))
                var_urun = cur_new.fetchone()

                if not var_urun:
                    cur_new.execute("""
                        INSERT INTO urun (
                            parca_kodu, ad, kategori_id, marka_id,
                            alis_fiyati_kurus, satis_fiyati_kurus, kdv_orani,
                            stok, kritik_stok, aciklama, aktif
                        ) VALUES (?, ?, ?, ?, ?, ?, 20, ?, 5, ?, 1)
                    """, (parca_kodu, ad, kat_id, marka_id, fiyat_kurus, fiyat_kurus, stok, aciklama))

                    urun_id = cur_new.lastrowid

                    # Açılış stok hareketi oluştur
                    cur_new.execute("""
                        INSERT INTO stok_hareket (
                            urun_id, hareket_tipi, adet_degisim, onceki_stok, sonraki_stok,
                            referans_tipi, referans_id, aciklama
                        ) VALUES (?, 'giris', ?, 0, ?, 'acilis_stogu', ?, 'Eski veritabanı açılış stoğu')
                    """, (urun_id, stok, stok, urun_id))

                    urun_sayisi += 1
                else:
                    urun_sayisi += 1

            # Güncel ürün haritası (ad -> (id, parca_kodu, satis_fiyati_kurus))
            cur_new.execute("SELECT id, parca_kodu, ad, satis_fiyati_kurus FROM urun WHERE aktif = 1")
            urun_ad_map = {row["ad"].lower().strip(): (row["id"], row["parca_kodu"], row["satis_fiyati_kurus"]) for row in cur_new.fetchall()}

            # 3. SİPARİŞ TABLOSUNU AKTAR (siparisal2)
            cur_leg.execute("SELECT urunadi, parcakodu, istenenadet, aciklama, tarih, Marka, Kategori FROM siparisal2")
            eski_siparisler = cur_leg.fetchall()

            for row in eski_siparisler:
                eski_urunadi, eski_sip_no, eski_adet, eski_aciklama, eski_tarih, _, _ = row

                siparis_no = f"SIP-LEG-{eski_sip_no}"
                urun_adi_temiz = str(eski_urunadi or "").strip()
                if not urun_adi_temiz:
                    urun_adi_temiz = "İsimsiz Ürün (Legacy)"

                adet = max(1, int(eski_adet)) if eski_adet else 1
                tarih = str(eski_tarih or "2025-01-01").strip()
                aciklama = str(eski_aciklama or "").strip()

                # Eşleşen ürün var mı?
                eslesen = urun_ad_map.get(urun_adi_temiz.lower())
                if eslesen:
                    urun_id, parca_kodu, birim_fiyat = eslesen
                    eslesen_siparis_sayisi += 1
                else:
                    urun_id = None
                    parca_kodu = ""
                    birim_fiyat = 0
                    eslesmeyen_siparis_sayisi += 1

                toplam_fiyat = adet * birim_fiyat
                kdv_tutari = int(toplam_fiyat * 0.20)
                genel_toplam = toplam_fiyat + kdv_tutari

                # Sipariş var mı kontrol et (idempotency)
                cur_new.execute("SELECT id FROM siparis WHERE siparis_no = ?", (siparis_no,))
                var_siparis = cur_new.fetchone()

                if not var_siparis:
                    cur_new.execute("""
                        INSERT INTO siparis (
                            siparis_no, musteri_id, tarih, durum, odeme_tipi,
                            ara_toplam_kurus, kdv_toplam_kurus, genel_toplam_kurus, aciklama
                        ) VALUES (?, NULL, ?, 'tamamlandi', 'nakit', ?, ?, ?, ?)
                    """, (siparis_no, tarih, toplam_fiyat, kdv_tutari, genel_toplam, f"Eski sistem aktarımı: {aciklama}"))

                    yeni_siparis_id = cur_new.lastrowid

                    cur_new.execute("""
                        INSERT INTO siparis_kalem (
                            siparis_id, urun_id, urun_adi_anlik, parca_kodu_anlik,
                            adet, birim_fiyat_kurus, kdv_orani, toplam_kurus
                        ) VALUES (?, ?, ?, ?, ?, ?, 20, ?)
                    """, (yeni_siparis_id, urun_id, urun_adi_temiz, parca_kodu, adet, birim_fiyat, toplam_fiyat))

                    siparis_sayisi += 1
                else:
                    siparis_sayisi += 1

            # Göç tamamlandı bayrağını işaretle
            cur_new.execute("UPDATE ayar SET deger = '1' WHERE anahtar = 'legacy_import_tamamlandi'")

        conn_new.close()
        conn_leg.close()

        mesaj = (
            f"Eski veritabanı başarıyla aktarıldı: "
            f"{urun_sayisi} ürün, {siparis_sayisi} sipariş "
            f"({eslesen_siparis_sayisi} ürünle eşleşen, {eslesmeyen_siparis_sayisi} tanımsız/geçmiş ürün)."
        )
        logger.info(mesaj)
        return LegacyImportResult(
            basarili=True,
            urun_sayisi=urun_sayisi,
            siparis_sayisi=siparis_sayisi,
            eslesen_siparis_sayisi=eslesen_siparis_sayisi,
            eslesmeyen_siparis_sayisi=eslesmeyen_siparis_sayisi,
            mesaj=mesaj
        )

    except Exception as e:
        conn_new.rollback()
        conn_new.close()
        conn_leg.close()
        logger.error("Legacy import işlemi sırasında hata: %s", e)
        return LegacyImportResult(
            basarili=False,
            urun_sayisi=0,
            siparis_sayisi=0,
            eslesen_siparis_sayisi=0,
            eslesmeyen_siparis_sayisi=0,
            mesaj=f"Hata oluştu, tüm işlemler geri alındı: {e}"
        )
