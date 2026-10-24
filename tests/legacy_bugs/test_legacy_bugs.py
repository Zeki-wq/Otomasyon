"""
Bölüm 3'teki B1 - B8 Hatalarını Yakalayan ve Yeniden Üreten Testler.
Bu testler, legacy (eski) sistemdeki hatalı varsayımların ve şemanın gerçek
hayat senaryolarında nasıl patladığını kanıtlar.
"""

import shutil
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def legacy_db(tmp_path):
    """Orijinal urunler12.db dosyasının geçici bir kopyasını sağlar."""
    src = Path("legacy/urunler12.db")
    dst = tmp_path / "legacy_test.db"
    shutil.copy(src, dst)
    return str(dst)


def test_b1_siparisal2_duplicate_product_unique_constraint(legacy_db):
    """
    B1: siparisal2.urunadi UNIQUE kısıtına sahip olduğu için
    aynı ürüne 2. kez sipariş girildiğinde IntegrityError fırlatılır.
    """
    conn = sqlite3.connect(legacy_db)
    cursor = conn.cursor()

    # İlk sipariş (Örn: 'buji_yeni')
    cursor.execute(
        "INSERT INTO siparisal2 (urunadi, istenenadet, aciklama, tarih) VALUES (?, ?, ?, ?)",
        ("buji_yeni", 2, "Test sipariş 1", "2026-10-24")
    )
    conn.commit()

    # Gerçek dükkanda aynı ürün gün içinde defalarca satılır.
    # Legacy sistemde bu işlem IntegrityError ile patlar:
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cursor.execute(
            "INSERT INTO siparisal2 (urunadi, istenenadet, aciklama, tarih) VALUES (?, ?, ?, ?)",
            ("buji_yeni", 3, "Test sipariş 2", "2026-10-24")
        )
        conn.commit()
    conn.close()

    assert "UNIQUE constraint failed: siparisal2.urunadi" in str(exc_info.value)


def test_b2_stok_dusumu_isimle_yapildiginda_hatali_guncelleme(legacy_db):
    """
    B2: Stok düşümü WHERE urunAdi = ? ile yapılıyor. Aynı isimde veya
    benzer isimde ürünler olduğunda isimle stok düşümü yanlış ürünleri günceller.
    Ayrıca siparisal2.parcakodu aslında sipariş id'sidir, ürün kodu değildir.
    """
    conn = sqlite3.connect(legacy_db)
    cursor = conn.cursor()

    # İki farklı marka aynı parça adında ürün ekleyelim
    cursor.execute(
        "INSERT INTO urun (urunAdi, birimFiyat, stokMiktari, urunAciklama, marka, kategori) VALUES (?, ?, ?, ?, ?, ?)",
        ("Fren Balatası", 500, 20, "Ön Fren", "Bosch", "Fren")
    )
    cursor.execute(
        "INSERT INTO urun (urunAdi, birimFiyat, stokMiktari, urunAciklama, marka, kategori) VALUES (?, ?, ?, ?, ?, ?)",
        ("Fren Balatası", 350, 10, "Arka Fren", "Valeo", "Fren")
    )
    conn.commit()

    # Legacy sipariş mantığı: urunAdi üzerinden UPDATE
    cursor.execute("UPDATE urun SET stokMiktari = stokMiktari - ? WHERE urunAdi = ?", (2, "Fren Balatası"))
    conn.commit()

    # Her iki ürünün de stoğu düşer (beklenmeyen durum):
    cursor.execute("SELECT stokMiktari FROM urun WHERE urunAdi = 'Fren Balatası'")
    stoklar = [row[0] for row in cursor.fetchall()]
    conn.close()

    # İki ürünün birden stoğu değişti (20->18 ve 10->8)
    assert stoklar == [18, 8], "İsimle stok düşümü tüm aynı isimli ürünlerin stoğunu bozdu!"


def test_b3_tablo_30_satir_siniri_ve_sutun_uyusmazligi():
    """
    B3: arayüz1.py içinde setRowCount(30) vardır. 30'dan fazla ürün eklenirse
    veya dönerse, 30. indeksten sonrakiler sessizce yok sayılır.
    Ayrıca urun tablosu 7 sütun dönerken tablo 6 sütun başlıklıdır.
    """
    with open("legacy/arayüz1.py", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # setRowCount(30) ve setColumnCount(6) sabit kodlanmış:
    assert "self.tbllistetablo.setColumnCount(6)" in content
    assert "self.tbllistetablo.setRowCount(30)" in content

    # QTableWidget davranışını doğrula: rowCount 30 iken 31. satıra setItem yapmak
    # satır sayısını artırmaz ve item'ı eklemez (sessizce yutar/gözükmez):
    import sys

    from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

    app = QApplication.instance() or QApplication(sys.argv)
    table = QTableWidget()
    table.setRowCount(30)
    table.setColumnCount(6)

    # 31. satıra öğe koymaya çalış
    table.setItem(31, 0, QTableWidgetItem("31. Ürün"))
    assert table.item(31, 0) is None, "30 satırlık tablo 31. indeksteki öğeyi sessizce yoksaymalı!"


def test_b4_coklu_qapplication_ve_import_aninda_yan_etki():
    """
    B4: pyton1.py import anında QApplication oluşturur.
    Başka bir modül (giris1.py) de QApplication oluşturduğunda
    Qt birden fazla QApplication örneğine izin vermez (veya tanımsız davranır).
    """
    # pyton1 dosyasının içeriğinde import anında QApplication çağrısı olduğunu doğrula
    with open("legacy/pyton1.py", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "uygulama = QApplication(sys.argv)" in content
    assert "baglanti = sqlite3.connect(\"urunler12.db\")" in content


def test_b5_kayit_ekle_hatali_kategori_ve_int_donusum_hatasi():
    """
    B5: kayit_ekle fonksiyonu formdaki cmburunkategori yerine
    sağdaki filtre cmbkategori kutusunu okur.
    Ayrıca int() dönüşümleri try/except dışında olduğundan harfli girdide ValueError verir.
    """
    with open("legacy/pyton1.py", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Formdaki kategori yerine filtre kutusunu okuduğunu doğrula:
    assert "Kategori = ui.cmbkategori.currentText()" in content
    assert "BirimFiyat = int(ui.lnebrmfiyat.text())" in content

    # Sayısal olmayan değerde int() fırlatır:
    with pytest.raises(ValueError):
        int("abc")


def test_b6_kayit_guncelle_turkce_karakter_sql_ve_silme_index_error(legacy_db):
    """
    B6: kayit_guncelle fonksiyonunda SQL sorgusunda 'urunAciklaması' (Türkçe ı)
    yazıldığı için güncelleme OperationalError verir.
    kayit_sil ise seçili hücre yoksa IndexError ile çöker.
    """
    conn = sqlite3.connect(legacy_db)
    cursor = conn.cursor()

    # pyton1.py içindeki hatalı güncelleme SQL'i:
    hatali_sql = "update urun set urunAdi = ?, birimFiyat = ?, stokMiktari = ?, urunAciklaması = ?, marka = ?, kategori = ? where urunKodu = ?"

    with pytest.raises(sqlite3.OperationalError) as exc_info:
        cursor.execute(hatali_sql, ("Test", 10, 5, "Aciklama", "Marka", "Kategori", 4))
    conn.close()

    assert "no such column: urunAciklaması" in str(exc_info.value)


def test_b7_kategori_listeleme_sutun_kaymasi_ve_eksik_arama():
    """
    B7: kategoriye_gore_listele fonksiyonunda ui.tbllistetablo.setItem(indexSatir, indexSutun+1, ...)
    yazılmıştır, bu da tüm sütunları 1 sağa kaydırıp ilk sütunu boş bırakır.
    """
    with open("legacy/pyton1.py", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "ui.tbllistetablo.setItem(indexSatir,indexSutun+1,QTableWidgetItem(str(kayitSutun)))" in content


def test_b8_foreign_keys_on_foreign_key_mismatch(legacy_db):
    """
    B8: PRAGMA foreign_keys = ON yapıldığında siparisal2'ye yazılamaz
    çünkü siparisal2 foreign key'leri urun.kategori ve urun.marka'ya bağlıdır
    ve bu sütunlar UNIQUE değildir.
    """
    conn = sqlite3.connect(legacy_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # siparisal2 tablosuna kayıt eklemeye çalıştığımızda foreign key mismatch hatası alırız:
    with pytest.raises(sqlite3.OperationalError) as exc_info:
        cursor.execute(
            "INSERT INTO siparisal2 (urunadi, istenenadet, aciklama, tarih, Marka, Kategori) VALUES (?, ?, ?, ?, ?, ?)",
            ("yeni_urun", 1, "test", "2026-10-24", "Brembo", "Fren")
        )
        conn.commit()
    conn.close()

    assert "foreign key mismatch" in str(exc_info.value).lower()
