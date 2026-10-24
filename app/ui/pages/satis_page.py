"""
Hızlı Satış, Sepet ve Kasa Ekranı (Tezgah Akışı)
Barkod okuyucu destekli, çok kalemli sepet, klavye dostu ve anında stok kontrolü.
"""


from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import Urun
from app.domain.money import kdv_hesapla, kurus_to_tl_str
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi
from app.services.urun_servisi import UrunServisi


class SatisPage(QWidget):
    """Tezgahta Hızlı Satış ve Sepet Yönetim Ekranı."""

    def __init__(
        self,
        satis_servisi: SatisServisi,
        urun_servisi: UrunServisi,
        musteri_servisi: MusteriServisi,
        aktif_kullanici=None,
        parent=None
    ):
        super().__init__(parent)
        self.satis_servisi = satis_servisi
        self.urun_servisi = urun_servisi
        self.musteri_servisi = musteri_servisi
        self.aktif_kullanici = aktif_kullanici

        self.sepet = []  # List[dict]: {"urun": Urun, "adet": int, "birim_fiyat_kurus": int, "kdv_orani": int}
        self.secili_hizli_urun: Urun | None = None

        self.init_ui()
        self.musterileri_doldur()

    def init_ui(self):
        ana_layout = QHBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(15)

        # ==========================================
        # SOL TARAF: Ürün Bulma ve Sepet Tablosu
        # ==========================================
        sol_layout = QVBoxLayout()
        sol_layout.setSpacing(10)

        # Üst Panel: Başlık
        baslik = QLabel("🛒 HIZLI SATIŞ & SEPET")
        baslik.setObjectName("headerTitle")
        sol_layout.addWidget(baslik)

        # Ürün Arama / Barkod Kartı
        arama_kart = QFrame()
        arama_kart.setObjectName("cardFrame")
        arama_layout = QHBoxLayout(arama_kart)
        arama_layout.setContentsMargins(12, 10, 12, 10)
        arama_layout.setSpacing(10)

        self.txt_barkod_ara = QLineEdit()
        self.txt_barkod_ara.setPlaceholderText("🔍 Barkod okutun veya parça kodu/adı yazıp Enter'a basın...")
        self.txt_barkod_ara.returnPressed.connect(self.urun_hizli_bul_ve_ekle)
        arama_layout.addWidget(self.txt_barkod_ara, stretch=5)

        arama_layout.addWidget(QLabel("Adet:"))
        self.spn_adet = QSpinBox()
        self.spn_adet.setRange(1, 1000)
        self.spn_adet.setValue(1)
        self.spn_adet.setFixedWidth(70)
        arama_layout.addWidget(self.spn_adet)

        self.btn_sepete_ekle = QPushButton("➕ Ekle")
        self.btn_sepete_ekle.setObjectName("btnSuccess")
        self.btn_sepete_ekle.clicked.connect(self.urun_hizli_bul_ve_ekle)
        arama_layout.addWidget(self.btn_sepete_ekle)

        sol_layout.addWidget(arama_kart)

        # Sepet Tablosu
        self.tablo_sepet = QTableWidget()
        self.tablo_sepet.setColumnCount(8)
        self.tablo_sepet.setHorizontalHeaderLabels([
            "Ürün ID", "Parça Kodu", "Ürün Adı", "Stok",
            "Adet", "Birim Fiyat", "KDV", "Toplam Tutar"
        ])
        self.tablo_sepet.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tablo_sepet.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tablo_sepet.setAlternatingRowColors(True)
        self.tablo_sepet.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo_sepet.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Ürün adı genişlesin
        sol_layout.addWidget(self.tablo_sepet)

        # Sepet İşlem Butonları
        sepet_btn_layout = QHBoxLayout()
        self.btn_satir_sil = QPushButton("🗑️ Seçili Satırı Kaldır")
        self.btn_satir_sil.setObjectName("btnDanger")
        self.btn_satir_sil.clicked.connect(self.secili_satiri_sil)
        sepet_btn_layout.addWidget(self.btn_satir_sil)

        self.btn_sepet_temizle = QPushButton("🧹 Sepeti Boşalt")
        self.btn_sepet_temizle.setObjectName("btnSecondary")
        self.btn_sepet_temizle.clicked.connect(self.sepeti_temizle)
        sepet_btn_layout.addWidget(self.btn_sepet_temizle)

        sepet_btn_layout.addStretch()
        sol_layout.addLayout(sepet_btn_layout)

        ana_layout.addLayout(sol_layout, stretch=7)

        # ==========================================
        # SAĞ TARAF: Müşteri, Ödeme ve Toplam Paneli
        # ==========================================
        sag_kart = QFrame()
        sag_kart.setObjectName("cardFrame")
        sag_kart.setFixedWidth(360)
        sag_layout = QVBoxLayout(sag_kart)
        sag_layout.setContentsMargins(15, 15, 15, 15)
        sag_layout.setSpacing(12)

        sag_baslik = QLabel("💳 ÖDEME & HESAP")
        sag_baslik.setStyleSheet("font-size: 14pt; font-weight: bold; color: #00a8ff;")
        sag_layout.addWidget(sag_baslik)

        # Müşteri Seçimi
        sag_layout.addWidget(QLabel("Müşteri Seçimi (Cari):"))
        self.cmb_musteri = QComboBox()
        self.cmb_musteri.currentIndexChanged.connect(self.musteri_secildi)
        sag_layout.addWidget(self.cmb_musteri)

        self.lbl_musteri_bakiye = QLabel("Cari Bakiye: 0,00 ₺")
        self.lbl_musteri_bakiye.setStyleSheet("color: #a4b0be; font-size: 9pt;")
        sag_layout.addWidget(self.lbl_musteri_bakiye)

        sag_layout.addSpacing(10)

        # Ödeme Tipi
        sag_layout.addWidget(QLabel("Ödeme Yöntemi:"))
        odeme_layout = QVBoxLayout()
        self.rb_nakit = QRadioButton("💵 Nakit")
        self.rb_nakit.setChecked(True)
        self.rb_kart = QRadioButton("💳 Kredi / Banka Kartı")
        self.rb_veresiye = QRadioButton("📝 Veresiye (Cari Hesaba)")

        self.odeme_grubu = QButtonGroup(self)
        self.odeme_grubu.addButton(self.rb_nakit, 1)
        self.odeme_grubu.addButton(self.rb_kart, 2)
        self.odeme_grubu.addButton(self.rb_veresiye, 3)

        odeme_layout.addWidget(self.rb_nakit)
        odeme_layout.addWidget(self.rb_kart)
        odeme_layout.addWidget(self.rb_veresiye)
        sag_layout.addLayout(odeme_layout)

        # Açıklama
        sag_layout.addWidget(QLabel("Sipariş Notu:"))
        self.txt_sip_not = QLineEdit()
        self.txt_sip_not.setPlaceholderText("Araç plakası veya açıklama...")
        sag_layout.addWidget(self.txt_sip_not)

        sag_layout.addStretch()

        # Fiyat Özeti Kutusu
        fiyat_kutu = QFrame()
        fiyat_kutu.setStyleSheet("background-color: #1e1f26; border-radius: 8px; padding: 12px;")
        fiyat_kutu_layout = QVBoxLayout(fiyat_kutu)
        fiyat_kutu_layout.setSpacing(6)

        ara_toplam_layout = QHBoxLayout()
        ara_toplam_layout.addWidget(QLabel("Ara Toplam:"))
        self.lbl_ara_toplam = QLabel("0,00 ₺")
        self.lbl_ara_toplam.setAlignment(QtCore.Qt.AlignRight)
        ara_toplam_layout.addWidget(self.lbl_ara_toplam)
        fiyat_kutu_layout.addLayout(ara_toplam_layout)

        kdv_layout = QHBoxLayout()
        kdv_layout.addWidget(QLabel("KDV Toplamı:"))
        self.lbl_kdv_toplam = QLabel("0,00 ₺")
        self.lbl_kdv_toplam.setAlignment(QtCore.Qt.AlignRight)
        kdv_layout.addWidget(self.lbl_kdv_toplam)
        fiyat_kutu_layout.addLayout(kdv_layout)

        cizgi = QFrame()
        cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet("color: #333945;")
        fiyat_kutu_layout.addWidget(cizgi)

        genel_layout = QHBoxLayout()
        lbl_g = QLabel("GENEL TOPLAM:")
        lbl_g.setStyleSheet("font-size: 11pt; font-weight: bold; color: #00a8ff;")
        genel_layout.addWidget(lbl_g)

        self.lbl_genel_toplam = QLabel("0,00 ₺")
        self.lbl_genel_toplam.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2ecc71;")
        self.lbl_genel_toplam.setAlignment(QtCore.Qt.AlignRight)
        genel_layout.addWidget(self.lbl_genel_toplam)
        fiyat_kutu_layout.addLayout(genel_layout)

        sag_layout.addWidget(fiyat_kutu)

        # Satışı Tamamla Butonu
        self.btn_tamamla = QPushButton("✅ SATIŞI ONAYLA (F12)")
        self.btn_tamamla.setObjectName("btnSuccess")
        self.btn_tamamla.setFixedHeight(48)
        self.btn_tamamla.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.btn_tamamla.clicked.connect(self.satisi_tamamla)
        sag_layout.addWidget(self.btn_tamamla)

        ana_layout.addWidget(sag_kart, stretch=3)

    def musterileri_doldur(self):
        self.cmb_musteri.blockSignals(True)
        self.cmb_musteri.clear()
        self.cmb_musteri.addItem("Perakende Satış (Müşterisiz)", None)
        for m in self.musteri_servisi.musterileri_getir():
            self.cmb_musteri.addItem(f"{m.ad_soyad} ({m.telefon or 'Telsiz'})", m.id)
        self.cmb_musteri.blockSignals(False)

    def musteri_secildi(self):
        m_id = self.cmb_musteri.currentData()
        if m_id:
            m = self.musteri_servisi.musteri_getir(m_id)
            if m:
                self.lbl_musteri_bakiye.setText(f"Cari Borç: {kurus_to_tl_str(m.bakiye_kurus)}")
                return
        self.lbl_musteri_bakiye.setText("Cari Bakiye: 0,00 ₺")

    def urun_hizli_bul_ve_ekle(self):
        metin = self.txt_barkod_ara.text().strip()
        if not metin:
            return

        adet = self.spn_adet.value()

        # 1. Önce tam barkod eşleşmesi dene
        urun = self.urun_servisi.urun_getir_barkod(metin)

        # 2. Tam parça kodu dene
        if not urun:
            urun = self.urun_servisi.urun_getir_parca_kodu(metin)

        # 3. Kısmi arama dene
        if not urun:
            sonuclar = self.urun_servisi.urun_ara(terim=metin, limit=10)
            if len(sonuclar) == 1:
                urun = sonuclar[0]
            elif len(sonuclar) > 1:
                # Kullanıcıya seçim listesi aç
                urun = self._urun_secim_diyalogu(sonuclar)
            else:
                QMessageBox.warning(self, "Bulunamadı", f"'{metin}' ile eşleşen parça bulunamadı!")
                self.txt_barkod_ara.selectAll()
                return

        if not urun:
            return

        # Stok kontrolü (mevcut sepeti de hesaba katarak)
        sepetteki_adet = sum(item["adet"] for item in self.sepet if item["urun"].id == urun.id)
        if urun.stok < sepetteki_adet + adet:
            QMessageBox.warning(
                self,
                "Yetersiz Stok",
                f"'{urun.ad}' için depoda {urun.stok} adet var!\n"
                f"Sepette zaten {sepetteki_adet} adet var, {adet} adet daha eklenemez."
            )
            return

        # Sepete ekle veya mevcut olanın adedini artır
        var_mi = False
        for item in self.sepet:
            if item["urun"].id == urun.id:
                item["adet"] += adet
                var_mi = True
                break

        if not var_mi:
            self.sepet.append({
                "urun": urun,
                "adet": adet,
                "birim_fiyat_kurus": urun.satis_fiyati_kurus,
                "kdv_orani": urun.kdv_orani
            })

        self.sepet_tablosunu_guncelle()
        self.txt_barkod_ara.clear()
        self.spn_adet.setValue(1)
        self.txt_barkod_ara.setFocus()

    def _urun_secim_diyalogu(self, urunler: list) -> Urun | None:
        diyalog = QtWidgets.QDialog(self)
        diyalog.setWindowTitle("Birden Fazla Eşleşme - Ürün Seçiniz")
        diyalog.resize(600, 350)
        d_layout = QVBoxLayout(diyalog)

        d_layout.addWidget(QLabel("Birden fazla ürün bulundu, lütfen seçim yapınız:"))
        liste = QtWidgets.QListWidget()
        for u in urunler:
            liste.addItem(f"{u.parca_kodu} - {u.ad} | Stok: {u.stok} | Fiyat: {kurus_to_tl_str(u.satis_fiyati_kurus)}")

        liste.setCurrentRow(0)
        d_layout.addWidget(liste)

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(diyalog.accept)
        btn_box.rejected.connect(diyalog.reject)
        d_layout.addWidget(btn_box)

        if diyalog.exec_() == QtWidgets.QDialog.Accepted:
            row = liste.currentRow()
            if row >= 0:
                return urunler[row]
        return None

    def sepet_tablosunu_guncelle(self):
        self.tablo_sepet.setRowCount(0)
        toplam_matrah = 0
        toplam_kdv = 0

        for idx, item in enumerate(self.sepet):
            u = item["urun"]
            adet = item["adet"]
            birim_fiyat = item["birim_fiyat_kurus"]
            kdv_orani = item["kdv_orani"]

            matrah = adet * birim_fiyat
            kdv_tutar, _ = kdv_hesapla(matrah, kdv_orani)

            toplam_matrah += matrah
            toplam_kdv += kdv_tutar

            self.tablo_sepet.insertRow(idx)
            self.tablo_sepet.setItem(idx, 0, QTableWidgetItem(str(u.id)))
            self.tablo_sepet.setItem(idx, 1, QTableWidgetItem(u.parca_kodu))
            self.tablo_sepet.setItem(idx, 2, QTableWidgetItem(u.ad))
            self.tablo_sepet.setItem(idx, 3, QTableWidgetItem(str(u.stok)))
            self.tablo_sepet.setItem(idx, 4, QTableWidgetItem(str(adet)))
            self.tablo_sepet.setItem(idx, 5, QTableWidgetItem(kurus_to_tl_str(birim_fiyat)))
            self.tablo_sepet.setItem(idx, 6, QTableWidgetItem(f"%{kdv_orani}"))
            self.tablo_sepet.setItem(idx, 7, QTableWidgetItem(kurus_to_tl_str(matrah + kdv_tutar)))

        genel_toplam = toplam_matrah + toplam_kdv
        self.lbl_ara_toplam.setText(kurus_to_tl_str(toplam_matrah))
        self.lbl_kdv_toplam.setText(kurus_to_tl_str(toplam_kdv))
        self.lbl_genel_toplam.setText(kurus_to_tl_str(genel_toplam))

    def secili_satiri_sil(self):
        secili = self.tablo_sepet.selectedItems()
        if not secili:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen sepetten kaldırmak istediğiniz satırı seçin.")
            return

        satir = secili[0].row()
        del self.sepet[satir]
        self.sepet_tablosunu_guncelle()

    def sepeti_temizle(self):
        if not self.sepet:
            return
        if QMessageBox.question(self, "Sepeti Temizle", "Sepetteki tüm ürünleri kaldırmak istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.sepet.clear()
            self.sepet_tablosunu_guncelle()

    def satisi_tamamla(self):
        if not self.sepet:
            QMessageBox.warning(self, "Sepet Boş", "Satışı onaylamak için sepete en az bir ürün ekleyiniz.")
            return

        # Ödeme tipi
        odeme_tipi = "nakit"
        if self.rb_kart.isChecked():
            odeme_tipi = "kart"
        elif self.rb_veresiye.isChecked():
            odeme_tipi = "veresiye"

        musteri_id = self.cmb_musteri.currentData()
        if odeme_tipi == "veresiye" and not musteri_id:
            QMessageBox.warning(
                self,
                "Müşteri Gerekli",
                "Veresiye satış yapabilmek için lütfen listeden bir müşteri (cari hesap) seçiniz!"
            )
            self.cmb_musteri.setFocus()
            return

        # Kalem verisini hazırla
        kalemler = [
            {
                "urun_id": item["urun"].id,
                "adet": item["adet"],
                "birim_fiyat_kurus": item["birim_fiyat_kurus"],
                "kdv_orani": item["kdv_orani"]
            }
            for item in self.sepet
        ]

        kullanici_id = self.aktif_kullanici.id if self.aktif_kullanici else None
        aciklama = self.txt_sip_not.text().strip()

        try:
            siparis = self.satis_servisi.siparis_olustur(
                kalemler=kalemler,
                musteri_id=musteri_id,
                odeme_tipi=odeme_tipi,
                aciklama=aciklama,
                kullanici_id=kullanici_id
            )

            QMessageBox.information(
                self,
                "Satış Başarılı",
                f"Sipariş #{siparis.siparis_no} başarıyla oluşturuldu!\n"
                f"Toplam: {kurus_to_tl_str(siparis.genel_toplam_kurus)}\n"
                "Stoklar depodan düşüldü."
            )

            # Sepeti ve alanları sıfırla
            self.sepet.clear()
            self.sepet_tablosunu_guncelle()
            self.txt_sip_not.clear()
            self.txt_barkod_ara.clear()
            self.txt_barkod_ara.setFocus()
            self.musteri_secildi()  # Cari bakiyeyi tazele

        except Exception as e:
            QMessageBox.critical(self, "Satış Hatası", str(e))
