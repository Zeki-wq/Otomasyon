"""
Veri Doğrulama ve Normalizasyon Modülü (Validators)
TCKN resmi algoritması, telefon normalizasyonu, vergi no, e-posta ve sayısal kontroller.
"""

import re
from typing import Any


def tc_kimlik_dogrula(tc: str | None) -> bool:
    """
    TC Kimlik Numarası resmi algoritma doğrulaması.
    - Boş ise kabul edilir (müşteri vermek istemeyebilir).
    - Doluysa tam 11 hane ve rakam olmalı.
    - İlk hane '0' olamaz.
    - 10. hane = ((1,3,5,7,9. haneler toplamı * 7) - (2,4,6,8. haneler toplamı)) % 10
    - 11. hane = (1..10. haneler toplamı) % 10
    """
    if tc is None:
        return True
    s = str(tc).strip()
    if not s:
        return True

    if len(s) != 11 or not s.isdigit():
        return False

    if s[0] == "0":
        return False

    d = [int(c) for c in s]

    tekler = sum(d[0:9:2])
    ciftler = sum(d[1:8:2])
    d10 = ((tekler * 7 - ciftler) % 10 + 10) % 10
    if d10 != d[9]:
        return False

    d11 = sum(d[:10]) % 10
    if d11 != d[10]:
        return False

    return True


def tc_maskele(tc: str | None) -> str:
    """
    KVKK uyumlu TC Kimlik No maskelemesi: ilk 3 ve son 2 hane açık, ortası yıldızlı.
    Örn: 100******46
    """
    if not tc:
        return ""
    s = str(tc).strip()
    if len(s) == 11:
        return f"{s[:3]}******{s[-2:]}"
    if len(s) > 4:
        return f"{s[:2]}***{s[-2:]}"
    return s


def telefon_dogrula_ve_normalize(tel: str | None) -> str:
    """
    Türkiye telefon numaralarını doğrular ve standart '05XXXXXXXXX' / '02XXXXXXXXX' biçimine normalize eder.
    - Boş ise '' döner.
    - Kabul edilen girişler: '0532 123 45 67', '+90 532 123 45 67', '905321234567', '0 (212) 456 78 90' vb.
    - Geçersiz ise ValueError fırlatır.
    """
    if tel is None:
        return ""
    s = str(tel).strip()
    if not s:
        return ""

    # Sadece rakamları ayıkla
    rakamlar = re.sub(r"\D", "", s)

    # 90 veya +90 ile başlıyorsa temizle
    if rakamlar.startswith("90") and len(rakamlar) == 12:
        rakamlar = "0" + rakamlar[2:]
    elif len(rakamlar) == 10 and not rakamlar.startswith("0"):
        rakamlar = "0" + rakamlar

    if len(rakamlar) != 11 or not rakamlar.startswith("0"):
        raise ValueError(
            "Geçersiz telefon numarası! Türkiye standartlarında 11 haneli (05XX veya 02XX) girilmelidir."
        )

    # Geçerli Türkiye alan kodları (05=cep, 02,03,04=sabit, 0850=kurumsal)
    if rakamlar[:2] not in ("05", "02", "03", "04") and not rakamlar.startswith("0850"):
        raise ValueError(
            "Geçersiz telefon numarası! Alan kodu Türkiye standartlarına (05XX, 02XX, 03XX, 04XX, 0850) uymalıdır."
        )

    return rakamlar


def telefon_formatla(tel: str | None) -> str:
    """
    Normalize edilmiş telefonu okunaklı '05XX XXX XX XX' formatına çevirir.
    """
    if not tel:
        return ""
    s = re.sub(r"\D", "", str(tel))
    if len(s) == 11:
        return f"{s[:4]} {s[4:7]} {s[7:9]} {s[9:]}"
    return str(tel)


def vergi_no_dogrula(vno: str | None) -> bool:
    """Vergi Kimlik Numarası doğrulaması (10 haneli rakam). Boş ise kabul edilir."""
    if vno is None:
        return True
    s = str(vno).strip()
    if not s:
        return True
    return len(s) == 10 and s.isdigit()


def eposta_dogrula(eposta: str | None) -> bool:
    """Temel e-posta biçimi doğrulaması. Boş ise kabul edilir."""
    if eposta is None:
        return True
    s = str(eposta).strip()
    if not s:
        return True
    regex = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return bool(re.match(regex, s))


def sayisal_fiyat_dogrula(deger_str: Any, alan_adi: str = "Fiyat") -> int:
    """
    Virgüllü ('12,50') veya noktalı ('12.50') stringi kuruş (int) cinsine çevirir ve doğrular.
    Negatif veya sayı dışı değerlerde ValueError fırlatır.
    """
    if deger_str is None:
        return 0
    s = str(deger_str).strip().replace("₺", "").replace("TL", "").strip()
    if not s:
        return 0

    s = s.replace(" ", "")
    # Eğer hem nokta hem virgül varsa (örn 1.250,50): noktaları at
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        val = float(s)
    except ValueError as e:
        raise ValueError(f"'{alan_adi}' alanı geçerli bir sayı olmalıdır!") from e

    if val < 0:
        raise ValueError(f"'{alan_adi}' negatif olamaz!")

    return int(round(val * 100))
