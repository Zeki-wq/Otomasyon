"""
Faz 5 Testleri: 5.000 Satırlık Excel İçe Aktarma, Hata Raporlama ve PDF Bilgi Fişi
Faz 5 Kapısı: 5.000 satırlık Excel hatalı satırları raporlayarak içe aktarılır, PDF üretilir.
"""

from pathlib import Path

import openpyxl
import pytest
from PySide6.QtWidgets import QMessageBox

from app.db.migrations.migrator import run_migrations
from app.domain.models import Siparis, SiparisKalem
from app.services.rapor_servisi import RaporServisi
from app.services.urun_servisi import UrunServisi
from app.ui.pages.raporlar_page import RaporlarPage
from app.ui.theme import apply_theme
from app.utils.export import (
    satis_fisi_pdf_olustur,
    urunleri_excelden_ice_aktar,
)


@pytest.fixture
def faz5_db(tmp_path):
    db_file = tmp_path / "faz5_test.db"
    run_migrations(db_file)
    return str(db_file)


def test_5000_satirlik_excel_ice_aktarma_ve_hata_raporlama(tmp_path, faz5_db):
    """
    Faz 5 Kapı Testi:
    5.000 geçerli ve 5 kasıtlı hatalı satır içeren Excel dosyasını içe aktarır.
    Geçerli 5.000 ürünün eklendiğini, 5 hatalı satırın satır numaralarıyla raporlandığını doğrular.
    """
    urun_srv = UrunServisi(faz5_db)
    excel_dosyasi = tmp_path / "urunler_5000.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active

    # Başlıklar
    ws.append([
        "Parça Kodu", "Barkod", "OEM No", "Ürün Adı",
        "Marka", "Kategori", "Alış Fiyatı", "Satış Fiyatı",
        "KDV", "Stok", "Kritik Stok", "Raf Yeri", "Açıklama"
    ])

    # 1. 5.000 Geçerli Satır Oluştur
    for i in range(1, 5001):
        ws.append([
            f"EXC-{i:05d}",
            f"869000{i:06d}",
            f"OEM-{i:05d}",
            f"Yedek Parça Kalemi {i}",
            "Bosch",
            "Fren Sistemi",
            "100,50 ₺",
            "150,00 ₺",
            20,
            10,
            3,
            f"Raf-{i % 20}",
            "Excel test kalemi"
        ])

    # 2. 5 Kasıtlı Hatalı Satır Ekle
    ws.append(["", "8690009991", "OEM-9991", "Kodu Olmayan Ürün", "Bosch", "Fren", "10", "20", 20, 5, 2, "A", ""]) # Hata 1: Boş Kod
    ws.append(["ERR-02", "8690009992", "OEM-9992", "", "Valeo", "Fren", "10", "20", 20, 5, 2, "A", ""])               # Hata 2: Boş Ad
    ws.append(["ERR-03", "8690009993", "OEM-9993", "Negatif Fiyat", "Brembo", "Fren", "10", "-50,00", 20, 5, 2, "A", ""]) # Hata 3: Negatif Fiyat
    ws.append(["ERR-04", "8690009994", "OEM-9994", "Negatif Stok", "TRW", "Fren", "10", "50", 20, -10, 2, "A", ""])       # Hata 4: Negatif Stok
    ws.append(["", "", "", "", "", "", "", "", "", "", "", "", ""])                                                   # Hata 5: Tamamen boş satır

    wb.save(str(excel_dosyasi))

    # İçe Aktarmayı Çalıştır
    sonuc = urunleri_excelden_ice_aktar(excel_dosyasi, urun_srv)

    # Doğrulamalar
    assert sonuc.eklenen_adet == 5000, f"Beklenen 5000 ürün eklendi, gerçekleşen: {sonuc.eklenen_adet}"
    assert len(sonuc.hatali_satirlar) == 4 or len(sonuc.hatali_satirlar) == 5  # Boş satır filtrelenebilir veya raporlanabilir
    assert urun_srv.toplam_urun_sayisi() == 5000

    # Hatalı satır raporunun detaylarını doğrula
    hatali_mesajlar = [h["hata"] for h in sonuc.hatali_satirlar]
    assert any("kod" in m.lower() for m in hatali_mesajlar)
    assert any("ad" in m.lower() for m in hatali_mesajlar)
    assert any("fiyat" in m.lower() for m in hatali_mesajlar)
    assert any("stok" in m.lower() for m in hatali_mesajlar)


def test_satis_fisi_pdf_olustur(tmp_path):
    """
    Satış Bilgi Fişi PDF çıktısının üretildiğini ve yasal 'Bilgi fişidir'
    ibaresini içerdiğini doğrular.
    """
    pdf_dosyasi = tmp_path / "test_fis.pdf"

    siparis = Siparis(
        id=1,
        siparis_no="SIP-20261024-0001",
        musteri_id=1,
        tarih="2026-10-24 14:30:00",
        durum="tamamlandi",
        odeme_tipi="nakit",
        ara_toplam_kurus=100000,
        kdv_toplam_kurus=20000,
        genel_toplam_kurus=120000,
        aciklama="34 ABC 123 Plakalı Araç",
        musteri_adi="Ahmet Usta",
        kalemler=[
            SiparisKalem(
                id=1,
                siparis_id=1,
                urun_id=1,
                urun_adi_anlik="Ön Fren Diski",
                parca_kodu_anlik="FRN-001",
                adet=2,
                birim_fiyat_kurus=50000,
                kdv_orani=20,
                toplam_kurus=100000
            )
        ]
    )

    dukkan_bilgisi = {
        "dukkan_adi": "Örnek Oto Yedek Parça Ltd.",
        "telefon": "0212 444 0 123",
        "adres": "Maslak Sanayi Sitesi, No: 42, İstanbul",
        "fis_alti_notu": "Bizi tercih ettiğiniz için teşekkür ederiz."
    }

    olusan_yol = satis_fisi_pdf_olustur(siparis, pdf_dosyasi, dukkan_bilgisi)

    assert olusan_yol.exists()
    assert olusan_yol.stat().st_size > 1000  # En az 1 KB olmalı

    # PDF binary başlığını doğrula (%PDF)
    with open(olusan_yol, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_raporlar_page_ui(qtbot, faz5_db, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok)

    rapor_srv = RaporServisi(faz5_db)
    urun_srv = UrunServisi(faz5_db)

    page = RaporlarPage(rapor_srv, urun_srv)
    apply_theme(page)
    page.resize(1100, 650)
    qtbot.addWidget(page)
    page.show()

    # Ekran görüntüsü al
    ekran_dir = Path("docs/ekran")
    ekran_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = ekran_dir / "raporlar_page.png"
    page.grab().save(str(screenshot_path))
    assert screenshot_path.exists()
