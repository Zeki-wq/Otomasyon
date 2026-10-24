"""
Veritabanı Şeması ve Migrasyon Testleri
"""

import sqlite3
import pytest
from app.db.connection import get_db_connection, check_db_health
from app.db.migrations.migrator import run_migrations


def test_migrations_fresh_db(tmp_path):
    db_file = tmp_path / "migrasyon_test.db"

    # Migrasyon çalıştır
    version = run_migrations(db_file)
    assert version >= 1

    # Sağlık kontrolü
    saglikli, mesaj = check_db_health(db_file)
    assert saglikli is True

    # Tabloların oluştuğunu doğrula
    conn = get_db_connection(db_file)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablolar = {r["name"] for r in cur.fetchall()}
    conn.close()

    beklenen_tablolar = {
        "ayar", "kullanici", "kategori", "marka", "urun",
        "musteri", "siparis", "siparis_kalem", "stok_hareket",
        "tahsilat", "tedarikci", "mal_kabul", "mal_kabul_kalem", "denetim_log"
    }
    assert beklenen_tablolar.issubset(tablolar)


def test_check_stok_non_negative_constraint(tmp_path):
    """CHECK(stok >= 0) kısıtının çalıştığını doğrular."""
    db_file = tmp_path / "stok_constraint_test.db"
    run_migrations(db_file)

    conn = get_db_connection(db_file)
    cur = conn.cursor()

    # Negatif stoklu ürün eklemeye çalış
    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            cur.execute("""
                INSERT INTO urun (parca_kodu, ad, stok, satis_fiyati_kurus)
                VALUES ('TEST-001', 'Test Parça', -5, 1000)
            """)
    conn.close()
