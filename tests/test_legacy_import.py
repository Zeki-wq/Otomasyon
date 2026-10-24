"""
Eski Veritabanı (legacy/urunler12.db) Kayıpsız Taşıma Testleri
Faz 1 Kapısı: 2 ürün ve 17 sipariş eksiksiz taşınır, mükerrer oluşmaz.
"""

from pathlib import Path

from app.db.connection import get_db_connection
from app.db.legacy_import import import_legacy_database


def test_legacy_database_migration_zero_data_loss(tmp_path):
    target_db = tmp_path / "yeni_test.db"
    legacy_db = Path("legacy/urunler12.db")

    assert legacy_db.exists(), "Orijinal urunler12.db dosyası bulunamadı!"

    # 1. Göçü çalıştır
    sonuc = import_legacy_database(legacy_db, target_db)

    assert sonuc.basarili is True
    assert sonuc.urun_sayisi == 2, f"Beklenen 2 ürün, aktarılan {sonuc.urun_sayisi}"
    assert sonuc.siparis_sayisi == 17, f"Beklenen 17 sipariş, aktarılan {sonuc.siparis_sayisi}"

    # Veritabanı içeriğini doğrula
    conn = get_db_connection(target_db)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM urun")
    urun_count = cur.fetchone()[0]
    assert urun_count == 2, "Yeni urun tablosundaki satır sayısı 2 olmalıdır."

    cur.execute("SELECT COUNT(*) FROM siparis")
    siparis_count = cur.fetchone()[0]
    assert siparis_count == 17, "Yeni siparis tablosundaki satır sayısı 17 olmalıdır."

    cur.execute("SELECT COUNT(*) FROM siparis_kalem")
    kalem_count = cur.fetchone()[0]
    assert kalem_count == 17, "Yeni siparis_kalem tablosundaki satır sayısı 17 olmalıdır."

    # Stok hareketlerini doğrula (2 ürün için açılış stokları kaydedilmiş olmalı)
    cur.execute("SELECT COUNT(*) FROM stok_hareket WHERE referans_tipi = 'acilis_stogu'")
    hareket_count = cur.fetchone()[0]
    assert hareket_count == 2, "2 ürün için açılış stok hareketi oluşturulmalıdır."

    conn.close()

    # 2. İkinci kez çalıştırıldığında (Idempotency) mükerrer kayıt oluşmamalıdır
    sonuc_2 = import_legacy_database(legacy_db, target_db)
    assert sonuc_2.basarili is True

    conn = get_db_connection(target_db)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM urun")
    assert cur.fetchone()[0] == 2, "İkinci çalıştırmada ürünler çoğalmamalıdır."

    cur.execute("SELECT COUNT(*) FROM siparis")
    assert cur.fetchone()[0] == 17, "İkinci çalıştırmada siparişler çoğalmamalıdır."

    cur.execute("SELECT COUNT(*) FROM siparis_kalem")
    assert cur.fetchone()[0] == 17, "İkinci çalıştırmada sipariş kalemleri çoğalmamalıdır."

    conn.close()
