"""
20.000 Ürün Performans ve Hızlı Arama Testleri
Faz 2 Kapısı: 20.000 üründe tamamına erişilir, arama < 100 ms sürer.
"""

import time

import pytest

from app.db.connection import get_db_connection
from app.db.migrations.migrator import run_migrations
from app.services.urun_servisi import UrunServisi


@pytest.fixture(scope="module")
def perf_db(tmp_path_factory):
    """20.000 sentetik ürün içeren performans veritabanı hazırlar."""
    db_file = tmp_path_factory.mktemp("perf") / "perf_20k.db"
    run_migrations(db_file)

    conn = get_db_connection(db_file)
    cur = conn.cursor()

    # 20.000 ürünü toplu insert (batch) ile hızlıca oluştur
    batch_size = 5000
    total = 20000

    parcalar = ["Fren Balatasi", "Buji", "Yag Filtresi", "Hava Filtresi", "Debriyaj Seti",
                "Amortisor", "Salincak", "Rot Basi", "V Kayisi", "Triger Seti"]
    marka_adlari = ["Bosch", "Valeo", "Brembo", "TRW", "Mann Filter", "Delphi", "Sachs"]

    # Marka ve kategori haritaları
    cur.execute("SELECT id FROM kategori")
    kat_ids = [r["id"] for r in cur.fetchall()] or [1]

    cur.execute("SELECT id FROM marka")
    marka_ids = [r["id"] for r in cur.fetchall()] or [1]

    for start in range(0, total, batch_size):
        rows = []
        for i in range(start + 1, start + batch_size + 1):
            parca_kodu = f"PRC-{i:06d}"
            barkod = f"869{i:010d}"
            oem_no = f"OEM-{i:05d}"
            ad = f"{parcalar[i % len(parcalar)]} {i}"
            kat_id = kat_ids[i % len(kat_ids)]
            marka_id = marka_ids[i % len(marka_ids)]
            alis = (i % 500 + 50) * 100
            satis = alis + 3000
            stok = i % 100

            rows.append((
                parca_kodu, barkod, oem_no, ad, kat_id, marka_id,
                alis, satis, 20, stok, 5, "Raf-1", "Sentetik test ürünü", 1
            ))

        cur.executemany("""
            INSERT INTO urun (
                parca_kodu, barkod, oem_no, ad, kategori_id, marka_id,
                alis_fiyati_kurus, satis_fiyati_kurus, kdv_orani, stok,
                kritik_stok, raf_yeri, aciklama, aktif
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

    conn.close()
    return str(db_file)


def test_20k_toplam_urun_sayisi_ve_sayfalama(perf_db):
    """20.000 ürünün tamamına erişilebildiğini ve sayfalandığını doğrular."""
    urun_srv = UrunServisi(perf_db)

    toplam = urun_srv.toplam_urun_sayisi()
    assert toplam == 20000, f"Beklenen 20.000 ürün, bulunan {toplam}"

    # İlk sayfa
    sayfa_1 = urun_srv.urun_ara(limit=50, offset=0)
    assert len(sayfa_1) == 50

    # Ortanca sayfa (10.000. kayıt civarı)
    sayfa_orta = urun_srv.urun_ara(limit=50, offset=10000)
    assert len(sayfa_orta) == 50

    # Son sayfa (19.950 - 20.000)
    sayfa_son = urun_srv.urun_ara(limit=50, offset=19950)
    assert len(sayfa_son) == 50


def test_20k_arama_hizi_100ms_alti(perf_db):
    """
    Kısmi arama hızının 50.000/20.000 üründe 100 ms'nin altında olduğunu doğrular.
    """
    urun_srv = UrunServisi(perf_db)

    arama_terimleri = [
        "PRC-005",        # Kod araması
        "Buji",           # İsim araması
        "869000000",      # Barkod araması
        "OEM-01",         # OEM araması
        "Fren Balatasi"   # İki kelimeli isim araması
    ]

    for terim in arama_terimleri:
        t0 = time.perf_counter()
        sonuclar = urun_srv.urun_ara(terim=terim, limit=50)
        sure_ms = (time.perf_counter() - t0) * 1000

        assert len(sonuclar) > 0, f"'{terim}' için sonuç bulunamadı!"
        assert sure_ms < 100.0, f"Arama çok yavaş sürdü: {sure_ms:.2f} ms (Hedef: < 100 ms)"
