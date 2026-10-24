"""
Para, Kuruş ve KDV Dönüşüm Modülü
Tüm parasal değerler veritabanında ve bellek içinde tamsayı kuruş (INTEGER) olarak saklanır.
"""

from decimal import Decimal, ROUND_HALF_UP
import re


def kurus_to_tl_str(kurus: int, sembol: bool = True) -> str:
    """
    Kuruş değerini Türkçe para formatına çevirir.
    Örnek: 123450 -> '1.234,50 ₺' veya '1.234,50'
    """
    if kurus is None:
        kurus = 0

    is_negative = kurus < 0
    abs_kurus = abs(kurus)
    lira = abs_kurus // 100
    krs = abs_kurus % 100

    # Lira kısmını binlik ayraçlı formatla (1234 -> '1.234')
    lira_str = f"{lira:,}".replace(",", ".")
    krs_str = f"{krs:02d}"

    sign = "-" if is_negative else ""
    suffix = " ₺" if sembol else ""
    return f"{sign}{lira_str},{krs_str}{suffix}"


def tl_str_to_kurus(metin: str) -> int:
    """
    Kullanıcıdan gelen para metnini kuruş tamsayısına çevirir.
    '1.234,50 ₺', '1234,50', '1234.50', '1234', '50' gibi formatları güvenle işler.
    """
    if not metin:
        return 0

    temiz = str(metin).strip().replace("₺", "").replace("TL", "").replace("tl", "").strip()
    if not temiz:
        return 0

    # Negatif işareti kontrolü
    is_negative = temiz.startswith("-")
    if is_negative:
        temiz = temiz[1:].strip()

    # Eğer hem '.' hem ',' varsa: '1.234,50' -> nokta binlik, virgül ondalık
    if "." in temiz and "," in temiz:
        temiz = temiz.replace(".", "").replace(",", ".")
    elif "," in temiz:
        # '1234,50' -> '1234.50'
        temiz = temiz.replace(",", ".")
    elif "." in temiz:
        # Nokta tek başına ondalık mı yoksa binlik mi?
        parts = temiz.split(".")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            # '1234.5' veya '1234.50' -> ondalık
            pass
        elif len(parts) > 2:
            # '1.234.567' -> binlik
            temiz = temiz.replace(".", "")
        else:
            # Tek nokta var: eğer virgülden sonra 3 basamak varsa binlik olabilir (örn '1.000')
            if len(parts[1]) == 3 and int(parts[0]) > 0:
                temiz = temiz.replace(".", "")

    try:
        dec = Decimal(temiz)
        kurus_dec = (dec * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        sonuc = int(kurus_dec)
        return -sonuc if is_negative else sonuc
    except Exception:
        # Sayısal olmayan karakterleri temizleyip tekrar dene
        rakamlar = re.sub(r"[^\d]", "", temiz)
        if not rakamlar:
            return 0
        return int(rakamlar) * 100


def kdv_hesapla(matrah_kurus: int, kdv_orani: int = 20) -> tuple[int, int]:
    """
    Verilen matrah (kuruş) ve KDV oranı üzerinden KDV tutarını ve toplamı hesaplar.
    Dönüş: (kdv_tutari_kurus, toplam_kurus)
    """
    if matrah_kurus <= 0 or kdv_orani <= 0:
        return (0, matrah_kurus)

    d_matrah = Decimal(matrah_kurus)
    d_oran = Decimal(kdv_orani) / Decimal(100)
    d_kdv = (d_matrah * d_oran).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    kdv_tutari = int(d_kdv)
    toplam = matrah_kurus + kdv_tutari
    return (kdv_tutari, toplam)


def kdv_dahilden_ayir(toplam_kurus: int, kdv_orani: int = 20) -> tuple[int, int]:
    """
    KDV dahil toplam tutardan matrahı ve KDV tutarını hesaplar.
    Dönüş: (matrah_kurus, kdv_tutari_kurus)
    """
    if toplam_kurus <= 0 or kdv_orani <= 0:
        return (toplam_kurus, 0)

    d_toplam = Decimal(toplam_kurus)
    d_carpan = Decimal(1) + (Decimal(kdv_orani) / Decimal(100))
    d_matrah = (d_toplam / d_carpan).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    matrah = int(d_matrah)
    kdv_tutari = toplam_kurus - matrah
    return (matrah, kdv_tutari)
