"""
Domain Varlık (Entity) Modelleri
"""

from dataclasses import dataclass, field


@dataclass
class Kullanici:
    id: int | None
    kullanici_adi: str
    parola_hash: str
    parola_salt: str
    ad_soyad: str
    rol: str = "personel"  # 'yonetici' veya 'personel'
    aktif: int = 1


@dataclass
class Kategori:
    id: int | None
    ad: str


@dataclass
class Marka:
    id: int | None
    ad: str


@dataclass
class Urun:
    id: int | None
    parca_kodu: str
    ad: str
    kategori_id: int | None = None
    marka_id: int | None = None
    barkod: str = ""
    oem_no: str = ""
    alis_fiyati_kurus: int = 0
    satis_fiyati_kurus: int = 0
    kdv_orani: int = 20
    stok: int = 0
    kritik_stok: int = 5
    raf_yeri: str = ""
    aciklama: str = ""
    aktif: int = 1
    olusturma_tarihi: str = ""
    kategori_adi: str = ""
    marka_adi: str = ""


@dataclass
class Musteri:
    id: int | None
    ad_soyad: str
    telefon: str = ""
    eposta: str = ""
    adres: str = ""
    vergi_no_tc: str = ""
    bakiye_kurus: int = 0
    aktif: int = 1


@dataclass
class SiparisKalem:
    id: int | None
    siparis_id: int | None
    urun_id: int | None
    urun_adi_anlik: str
    parca_kodu_anlik: str
    adet: int
    birim_fiyat_kurus: int
    kdv_orani: int
    toplam_kurus: int


@dataclass
class Siparis:
    id: int | None
    siparis_no: str
    musteri_id: int | None
    tarih: str
    durum: str = "tamamlandi"  # 'tamamlandi', 'iptal', 'iade'
    odeme_tipi: str = "nakit"  # 'nakit', 'kart', 'veresiye'
    ara_toplam_kurus: int = 0
    kdv_toplam_kurus: int = 0
    genel_toplam_kurus: int = 0
    aciklama: str = ""
    kullanici_id: int | None = None
    musteri_adi: str = ""
    kullanici_adi: str = ""
    kalem_sayisi: int = 0
    toplam_adet: int = 0
    kalemler: list[SiparisKalem] = field(default_factory=list)


@dataclass
class StokHareket:
    id: int | None
    urun_id: int
    hareket_tipi: str  # 'giris', 'satis', 'iade', 'iptal', 'sayim_duzeltme'
    adet_degisim: int  # Pozitif veya negatif
    onceki_stok: int
    sonraki_stok: int
    referans_tipi: str = "manuel"  # 'siparis', 'mal_kabul', 'acilis_stogu', 'manuel'
    referans_id: int | None = None
    kullanici_id: int | None = None
    tarih: str = ""
    aciklama: str = ""
    urun_adi: str = ""
    parca_kodu: str = ""


@dataclass
class Tahsilat:
    id: int | None
    musteri_id: int
    tutar_kurus: int
    odeme_tipi: str = "nakit"
    tarih: str = ""
    aciklama: str = ""
    kullanici_id: int | None = None
    musteri_adi: str = ""


@dataclass
class Ayar:
    anahtar: str
    deger: str
    aciklama: str = ""
