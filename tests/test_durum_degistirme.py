"""
Test: Düzenle diyaloglarından ve listelerden ürün ve müşteri aktif/pasif durum değişimi.
Gereksinim:
1. Ürünü pasife al -> satış aramasında çıkmaz -> aktife al -> tekrar çıkar.
2. Stok ve geçmiş siparişler kesinlikle değişmez.
3. "Aktife Al" yetkisi yalnızca yöneticidedir; normal kullanıcı (personel) pasif ürünü aktife alamaz.
4. Gösterilen bilgi/uyarı mesajları tam olarak doğrulanır.
5. Onay diyaloglarında "Hayır" yanıtı verildiğinde durumun değişmediği kanıtlanır.
"""

from PySide6.QtWidgets import QMessageBox

from app.db.migrations.migrator import run_migrations
from app.domain.models import Musteri, Urun
from app.services.kimlik_servisi import KimlikServisi
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi
from app.ui.pages.musteriler_page import MusteriDiyalog
from app.ui.pages.urunler_page import UrunDiyalog, UrunlerPage


def test_urun_duzenle_durum_degistirme(tmp_path, dialog_manager):
    """
    Kapsamlı Doğrulama:
    - Geçmiş siparişi ve stoğu olan bir ürün oluşturulur.
    - Ürün pasife alınır: satış aramasında çıkmaz, geçmiş sipariş ve stok değişmez.
    - Normal (personel) kullanıcının pasif ürünü aktife alması engellenir.
    - Yönetici ürünü aktife alır: satış aramasında tekrar çıkar, bilgi mesajı doğrulanır.
    """
    db_path = tmp_path / "test_urun_durum.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    admin_user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    personel_user = ks.kullanici_olustur("personel", "Personel", "123456", "personel")
    us = UrunServisi(db_path)
    ss = StokServisi(db_path)
    satis_servisi = SatisServisi(db_path)

    # 1. Başlangıçta aktif bir ürün ekle
    baslangic_stok = 15
    u_id = us.urun_ekle(Urun(
        id=None,
        parca_kodu="PRC-999",
        ad="Ön Tampon Demiri",
        alis_fiyati_kurus=100000,
        satis_fiyati_kurus=150000,
        stok=baslangic_stok,
        kdv_orani=20,
        aktif=1
    ), kullanici_id=admin_user.id)

    # 2. Ürüne ait geçmiş bir satış/sipariş oluştur
    sepet = [{"urun_id": u_id, "adet": 2, "birim_fiyat_kurus": 150000, "kdv_orani": 20}]
    siparis = satis_servisi.siparis_olustur(
        kalemler=sepet,
        odeme_tipi="nakit",
        kullanici_id=admin_user.id
    )
    urun_siparis_sonrasi = us.urun_getir(u_id)
    beklenen_stok = baslangic_stok - 2
    assert urun_siparis_sonrasi.stok == beklenen_stok
    assert siparis.id > 0

    # Satış aramasında ürün bulunabilmeli
    assert us.urun_getir_parca_kodu("PRC-999") is not None
    assert len(us.urun_ara(terim="Tampon", sadece_aktif=True)) == 1

    # 3. Ürünü Düzenle Diyaloğu ile Pasife Al
    dlg_pasif = UrunDiyalog(parent=None, urun_servisi=us, urun=urun_siparis_sonrasi, aktif_kullanici=admin_user)
    assert hasattr(dlg_pasif, "cmb_durum"), "UrunDiyalog'da cmb_durum bulunamadı!"
    assert dlg_pasif.cmb_durum.currentData() == 1

    idx_pasif = dlg_pasif.cmb_durum.findData(0)
    dlg_pasif.cmb_durum.setCurrentIndex(idx_pasif)

    dialog_manager.clear()
    dlg_pasif.kaydet()

    # Bilgi mesajının doğrulanması
    assert dialog_manager.has_message("Ürün bilgileri başarıyla güncellendi.", kind="information")

    # Ürün pasif olmalı
    urun_pasif = us.urun_getir(u_id)
    assert urun_pasif.aktif == 0

    # KANIT 1: Pasif ürün satış aramasında ÇIKMAZ
    assert us.urun_getir_parca_kodu("PRC-999") is None
    assert len(us.urun_ara(terim="Tampon", sadece_aktif=True)) == 0

    # KANIT 2: Stok ve geçmiş sipariş DEĞİŞMEZ
    assert urun_pasif.stok == beklenen_stok
    gecmis_siparis = satis_servisi.siparis_detay_getir(siparis.id)
    assert gecmis_siparis is not None
    assert gecmis_siparis.durum == "tamamlandi"
    assert len(gecmis_siparis.kalemler) == 1

    # KANIT 3: "Aktife Al" yalnızca yönetici yetkisindedir (Personel aktife alamaz!)
    dlg_personel = UrunDiyalog(parent=None, urun_servisi=us, urun=urun_pasif, aktif_kullanici=personel_user)
    assert dlg_personel.cmb_durum.isEnabled() is False, "Personel için cmb_durum devre dışı olmalıydı!"

    # Personel zorla aktife alıp kaydetmeye çalışırsa engellenmeli
    dlg_personel.cmb_durum.setEnabled(True)
    dlg_personel.cmb_durum.setCurrentIndex(dlg_personel.cmb_durum.findData(1))
    dialog_manager.clear()
    dlg_personel.kaydet()

    assert dialog_manager.has_message("Yetkisiz İşlem", kind="warning")
    # Ürün hâlâ pasif kalmalı
    assert us.urun_getir(u_id).aktif == 0

    # UrunlerPage üzerinde de personelin aktife alma yetkisi engellenmeli
    page = UrunlerPage(us, ss, aktif_kullanici=personel_user)
    page.cmb_aktiflik.setCurrentIndex(1)  # pasifler
    page.tablo.setCurrentCell(0, 0)
    page.satir_secildi()
    assert page.btn_aktife_al.isVisible() is False

    dialog_manager.clear()
    page.urun_aktife_al()  # Doğrudan çağrılsa bile
    assert dialog_manager.has_message("Yetkisiz İşlem", kind="warning")
    assert us.urun_getir(u_id).aktif == 0
    page.close()

    # KANIT 4: Yönetici ürünü aktife alır -> Tekrar satışta çıkar
    dlg_admin_aktif = UrunDiyalog(parent=None, urun_servisi=us, urun=urun_pasif, aktif_kullanici=admin_user)
    assert dlg_admin_aktif.cmb_durum.isEnabled() is True
    dlg_admin_aktif.cmb_durum.setCurrentIndex(dlg_admin_aktif.cmb_durum.findData(1))

    dialog_manager.clear()
    dlg_admin_aktif.kaydet()

    assert dialog_manager.has_message("Ürün bilgileri başarıyla güncellendi.", kind="information")

    # Ürün tekrar aktif olmalı
    urun_tekrar_aktif = us.urun_getir(u_id)
    assert urun_tekrar_aktif.aktif == 1

    # Satış aramasında tekrar çıkmalı
    assert us.urun_getir_parca_kodu("PRC-999") is not None
    assert len(us.urun_ara(terim="Tampon", sadece_aktif=True)) == 1

    # KANIT 5: Onay kutusunda 'Hayır' denilirse ürün aktif kalmaya devam etmeli
    page_hayir = UrunlerPage(us, ss, aktif_kullanici=admin_user)
    page_hayir.tablo.setCurrentCell(0, 0)
    dialog_manager.set_question_response(QMessageBox.StandardButton.No)
    page_hayir.urun_pasife_al()
    assert us.urun_getir(u_id).aktif == 1
    page_hayir.close()
    dialog_manager.set_question_response(QMessageBox.StandardButton.Yes)


def test_musteri_duzenle_durum_degistirme(tmp_path, dialog_manager):
    """Müşteri düzenleme diyaloğunda hesap durumu değiştirilebilmeli."""
    db_path = tmp_path / "test_musteri_durum.db"
    run_migrations(db_path)

    ks = KimlikServisi(db_path)
    user = ks.kullanici_olustur("admin", "Admin", "123456", "yonetici")
    ms = MusteriServisi(db_path)

    m_id = ms.musteri_ekle(Musteri(
        id=None,
        ad_soyad="Ahmet Demir",
        telefon="0555 123 45 67",
        eposta="ahmet@example.com",
        vergi_no_tc="11111111110",
        adres="Oto Sanayi Sit.",
        aktif=0
    ))
    ms.musteri_pasife_al(m_id)
    musteri = ms.musteri_getir(m_id)
    assert musteri.aktif == 0

    dlg = MusteriDiyalog(parent=None, musteri_servisi=ms, musteri=musteri, aktif_kullanici=user)
    assert hasattr(dlg, "cmb_durum")
    assert dlg.cmb_durum.currentData() == 0

    idx_aktif = dlg.cmb_durum.findData(1)
    dlg.cmb_durum.setCurrentIndex(idx_aktif)

    dialog_manager.clear()
    dlg.kaydet()

    guncel_m = ms.musteri_getir(m_id)
    assert guncel_m.aktif == 1
    assert dialog_manager.has_message("Müşteri bilgileri güncellendi.", kind="information")
