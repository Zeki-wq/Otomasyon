"""
Para ve KDV Hesaplama Testleri
"""

from app.domain.money import (
    kdv_dahilden_ayir,
    kdv_hesapla,
    kurus_to_tl_str,
    tl_str_to_kurus,
)


def test_kurus_to_tl_str():
    assert kurus_to_tl_str(123450) == "1.234,50 ₺"
    assert kurus_to_tl_str(123450, sembol=False) == "1.234,50"
    assert kurus_to_tl_str(0) == "0,00 ₺"
    assert kurus_to_tl_str(50) == "0,50 ₺"
    assert kurus_to_tl_str(100) == "1,00 ₺"
    assert kurus_to_tl_str(-500) == "-5,00 ₺"
    assert kurus_to_tl_str(100000000) == "1.000.000,00 ₺"


def test_tl_str_to_kurus():
    assert tl_str_to_kurus("1.234,50 ₺") == 123450
    assert tl_str_to_kurus("1234,50") == 123450
    assert tl_str_to_kurus("1234.50") == 123450
    assert tl_str_to_kurus("1234") == 123400
    assert tl_str_to_kurus("0,50") == 50
    assert tl_str_to_kurus("0.05") == 5
    assert tl_str_to_kurus("-150,00") == -15000
    assert tl_str_to_kurus("") == 0
    assert tl_str_to_kurus(None) == 0


def test_kdv_hesapla():
    # 100,00 TL matrah, %20 KDV -> 20,00 TL KDV, 120,00 TL toplam
    kdv, toplam = kdv_hesapla(10000, 20)
    assert kdv == 2000
    assert toplam == 12000

    # Kuruşlu yuvarlama (ROUND_HALF_UP testi)
    # 12,35 TL matrah, %20 KDV -> 1235 * 0.20 = 247 kuruş KDV
    kdv, toplam = kdv_hesapla(1235, 20)
    assert kdv == 247
    assert toplam == 1482


def test_kdv_dahilden_ayir():
    # 120,00 TL KDV dahil, %20 KDV -> 100,00 TL matrah, 20,00 TL KDV
    matrah, kdv = kdv_dahilden_ayir(12000, 20)
    assert matrah == 10000
    assert kdv == 2000
