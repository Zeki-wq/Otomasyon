"""
Excel İçe/Dışa Aktarma (openpyxl) ve Satış Bilgi Fişi PDF Üretimi (reportlab)
"""

from pathlib import Path
from typing import List, Dict, Any, NamedTuple, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.domain.models import Urun, Siparis, Musteri
from app.domain.money import kurus_to_tl_str, tl_str_to_kurus
from app.services.urun_servisi import UrunServisi


class ExcelImportResult(NamedTuple):
    toplam_satir: int
    eklenen_adet: int
    guncellenen_adet: int
    hatali_satirlar: List[Dict[str, Any]]
    mesaj: str


def urunleri_excele_aktar(urunler: List[Urun], dosya_yolu: Path) -> Path:
    """Verilen ürün listesini biçimlendirilmiş bir Excel (.xlsx) dosyasına aktarır."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Parça Listesi"

    basliklar = [
        "Parça Kodu", "Barkod", "OEM No", "Ürün Adı",
        "Marka", "Kategori", "Alış Fiyatı (TL)", "Satış Fiyatı (TL)",
        "KDV (%)", "Stok", "Kritik Stok", "Raf Yeri", "Açıklama"
    ]
    ws.append(basliklar)

    # Başlık Stili
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F232A", end_color="1F232A", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")

    for col_idx in range(1, len(basliklar) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    # Satırları Ekle
    for u in urunler:
        alis_tl = u.alis_fiyati_kurus / 100.0
        satis_tl = u.satis_fiyati_kurus / 100.0
        ws.append([
            u.parca_kodu,
            u.barkod,
            u.oem_no,
            u.ad,
            u.marka_adi,
            u.kategori_adi,
            alis_tl,
            satis_tl,
            u.kdv_orani,
            u.stok,
            u.kritik_stok,
            u.raf_yeri,
            u.aciklama
        ])

    # Sütun Genişliklerini Otomatik Ayarla
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    dosya_yolu.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(dosya_yolu))
    return dosya_yolu


def urunleri_excelden_ice_aktar(dosya_yolu: Path, urun_servisi: UrunServisi) -> ExcelImportResult:
    """
    Excel dosyasından 5.000+ satırlık ürünleri okur ve veritabanına aktarır.
    Hatalı veya eksik satırları atlayarak raporlar; geçerli olanları güvenle ekler/günceller.
    """
    wb = openpyxl.load_workbook(str(dosya_yolu), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows or len(rows) < 2:
        return ExcelImportResult(0, 0, 0, [], "Excel dosyasında veri satırı bulunamadı.")

    # Başlık satırını atla
    veri_satirlari = rows[1:]
    toplam_satir = len(veri_satirlari)

    eklenen = 0
    guncellenen = 0
    hatali_satirlar = []

    # Mevcut marka ve kategorileri haritala
    kategori_map = {k.ad.lower(): k.id for k in urun_servisi.kategorileri_getir()}
    marka_map = {m.ad.lower(): m.id for m in urun_servisi.markalari_getir()}

    for satir_no, row in enumerate(veri_satirlari, start=2):
        if not row or not any(row):
            continue

        try:
            parca_kodu = str(row[0] or '').strip().upper()
            if not parca_kodu:
                hatali_satirlar.append({"satir": satir_no, "kod": "-", "hata": "Parça kodu boş."})
                continue

            ad = str(row[3] or '').strip()
            if not ad:
                hatali_satirlar.append({"satir": satir_no, "kod": parca_kodu, "hata": "Ürün adı boş."})
                continue

            barkod = str(row[1] or '').strip()
            oem_no = str(row[2] or '').strip().upper()
            marka_adi = str(row[4] or '').strip()
            kategori_adi = str(row[5] or '').strip()

            # Fiyat dönüşümleri
            alis_val = row[6] if len(row) > 6 else 0
            satis_val = row[7] if len(row) > 7 else 0
            alis_kurus = tl_str_to_kurus(str(alis_val))
            satis_kurus = tl_str_to_kurus(str(satis_val))

            if satis_kurus < 0:
                hatali_satirlar.append({"satir": satir_no, "kod": parca_kodu, "hata": "Satış fiyatı negatif olamaz."})
                continue

            # KDV ve Stok
            try:
                kdv = int(row[8]) if len(row) > 8 and row[8] is not None else 20
            except Exception:
                kdv = 20

            try:
                stok = int(row[9]) if len(row) > 9 and row[9] is not None else 0
                if stok < 0:
                    hatali_satirlar.append({"satir": satir_no, "kod": parca_kodu, "hata": "Stok miktarı negatif olamaz."})
                    continue
            except Exception:
                stok = 0

            try:
                kritik = int(row[10]) if len(row) > 10 and row[10] is not None else 5
            except Exception:
                kritik = 5

            raf_yeri = str(row[11] or '').strip() if len(row) > 11 else ''
            aciklama = str(row[12] or '').strip() if len(row) > 12 else ''

            # Marka ID bul veya oluştur
            m_id = None
            if marka_adi:
                m_id = marka_map.get(marka_adi.lower())
                if not m_id:
                    m_id = urun_servisi.marka_ekle(marka_adi)
                    marka_map[marka_adi.lower()] = m_id

            # Kategori ID bul veya oluştur
            k_id = None
            if kategori_adi:
                k_id = kategori_map.get(kategori_adi.lower())
                if not k_id:
                    k_id = urun_servisi.kategori_ekle(kategori_adi)
                    kategori_map[kategori_adi.lower()] = k_id

            # Ürün var mı kontrol et
            mevcut_urun = urun_servisi.urun_getir_parca_kodu(parca_kodu)
            if mevcut_urun:
                mevcut_urun.ad = ad
                mevcut_urun.barkod = barkod
                mevcut_urun.oem_no = oem_no
                mevcut_urun.marka_id = m_id
                mevcut_urun.kategori_id = k_id
                mevcut_urun.alis_fiyati_kurus = alis_kurus
                mevcut_urun.satis_fiyati_kurus = satis_kurus
                mevcut_urun.kdv_orani = kdv
                mevcut_urun.kritik_stok = kritik
                mevcut_urun.raf_yeri = raf_yeri
                mevcut_urun.aciklama = aciklama
                urun_servisi.urun_guncelle(mevcut_urun)
                guncellenen += 1
            else:
                yeni = Urun(
                    id=None,
                    parca_kodu=parca_kodu,
                    ad=ad,
                    barkod=barkod,
                    oem_no=oem_no,
                    marka_id=m_id,
                    kategori_id=k_id,
                    alis_fiyati_kurus=alis_kurus,
                    satis_fiyati_kurus=satis_kurus,
                    kdv_orani=kdv,
                    stok=stok,
                    kritik_stok=kritik,
                    raf_yeri=raf_yeri,
                    aciklama=aciklama
                )
                urun_servisi.urun_ekle(yeni)
                eklenen += 1

        except Exception as e:
            hatali_satirlar.append({"satir": satir_no, "kod": str(row[0] or '-'), "hata": str(e)})

    mesaj = f"İçe aktarma tamamlandı: {eklenen} yeni eklendi, {guncellenen} güncellendi, {len(hatali_satirlar)} hatalı satır atlandı."
    return ExcelImportResult(
        toplam_satir=toplam_satir,
        eklenen_adet=eklenen,
        guncellenen_adet=guncellenen,
        hatali_satirlar=hatali_satirlar,
        mesaj=mesaj
    )


def satis_fisi_pdf_olustur(
    siparis: Siparis,
    dosya_yolu: Path,
    dukkan_bilgisi: Optional[Dict[str, str]] = None
) -> Path:
    """
    Satış siparişi için şık bir A4/Termal Bilgi Fişi PDF dosyası üretir.
    Üzerinde 'Bilgi fişidir, mali değeri yoktur.' yasal ibaresi bulunur.
    """
    dosya_yolu.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(dosya_yolu),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=16,
        alignment=1,  # Center
        textColor=colors.HexColor("#1e1f26"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=9,
        alignment=1,  # Center
        textColor=colors.HexColor("#57606f"),
        spaceAfter=12
    )
    legal_warning_style = ParagraphStyle(
        "LegalWarning",
        parent=styles["Normal"],
        fontSize=11,
        alignment=1,  # Center
        textColor=colors.HexColor("#c0392b"),
        fontName="Helvetica-Bold",
        spaceAfter=15
    )

    story = []

    # Dükkan Bilgisi
    info = dukkan_bilgisi or {}
    dukkan_adi = info.get("dukkan_adi", "OTO YEDEK PARÇA")
    tel = info.get("telefon", "")
    adres = info.get("adres", "")

    story.append(Paragraph(f"<b>{dukkan_adi}</b>", title_style))
    story.append(Paragraph(f"{adres} | Tel: {tel}", subtitle_style))
    story.append(Paragraph("*** BİLGİ FİŞİDİR, MALİ DEĞERİ YOKTUR ***", legal_warning_style))
    story.append(Spacer(1, 10))

    # Fiş Bilgileri Tablosu
    meta_data = [
        [f"Sipariş No: {siparis.siparis_no}", f"Tarih: {siparis.tarih}"],
        [f"Müşteri: {siparis.musteri_adi}", f"Ödeme Yolu: {siparis.odeme_tipi.upper()}"]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#2f3640")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Kalemler Tablosu
    kalem_data = [["Kod", "Ürün Adı", "Adet", "Birim Fiyat", "KDV", "Toplam"]]
    for k in siparis.kalemler:
        kalem_data.append([
            k.parca_kodu_anlik,
            k.urun_adi_anlik,
            str(k.adet),
            kurus_to_tl_str(k.birim_fiyat_kurus),
            f"%{k.kdv_orani}",
            kurus_to_tl_str(k.toplam_kurus)
        ])

    # Toplam satırları
    kalem_data.append(["", "", "", "", "Ara Toplam:", kurus_to_tl_str(siparis.ara_toplam_kurus)])
    kalem_data.append(["", "", "", "", "KDV Toplamı:", kurus_to_tl_str(siparis.kdv_toplam_kurus)])
    kalem_data.append(["", "", "", "", "GENEL TOPLAM:", kurus_to_tl_str(siparis.genel_toplam_kurus)])

    kalem_table = Table(kalem_data, colWidths=[80, 200, 45, 65, 45, 85])
    kalem_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2f3640")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, len(siparis.kalemler)), 0.5, colors.HexColor("#dcdde1")),
        ('LINEBELOW', (4, -3), (-1, -1), 1, colors.HexColor("#2f3640")),
        ('FONTNAME', (4, -3), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, -1), (-1, -1), 11),
        ('TEXTCOLOR', (4, -1), (-1, -1), colors.HexColor("#27ae60")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kalem_table)

    story.append(Spacer(1, 25))
    story.append(Paragraph(info.get("fis_alti_notu", "Bizi tercih ettiğiniz için teşekkür ederiz."), subtitle_style))

    doc.build(story)
    return dosya_yolu
