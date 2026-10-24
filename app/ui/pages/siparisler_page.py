"""
Sipariş Geçmişi, Detay Görüntüleme ve İptal/İade Ekranı
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.domain.money import kurus_to_tl_str
from app.services.musteri_servisi import MusteriServisi
from app.services.satis_servisi import SatisServisi


class SiparisDetayDiyalog(QDialog):
    """Siparişin kalemlerini ve detaylarını gösteren pencere."""

    def __init__(self, siparis, parent=None):
        super().__init__(parent)
        self.siparis = siparis
        self.setWindowTitle(f"Sipariş Detayı - {siparis.siparis_no}")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(750, 480)
        self.resize(780, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Bilgi Kartı
        kart = QFrame()
        kart.setObjectName("cardFrame")
        k_layout = QVBoxLayout(kart)

        ust = QHBoxLayout()
        ust.addWidget(QLabel(f"<b>Sipariş No:</b> {self.siparis.siparis_no}"))
        ust.addWidget(QLabel(f"<b>Tarih:</b> {self.siparis.tarih}"))
        ust.addWidget(QLabel(f"<b>Müşteri:</b> {self.siparis.musteri_adi}"))
        k_layout.addLayout(ust)

        alt = QHBoxLayout()
        alt.addWidget(QLabel(f"<b>Ödeme:</b> {self.siparis.odeme_tipi.upper()}"))
        durum_renk = "#2ecc71" if self.siparis.durum == "tamamlandi" else "#e74c3c"
        alt.addWidget(QLabel(f"<b>Durum:</b> <span style='color:{durum_renk}; font-weight:bold;'>{self.siparis.durum.upper()}</span>"))
        if self.siparis.aciklama:
            alt.addWidget(QLabel(f"<b>Not:</b> {self.siparis.aciklama}"))
        k_layout.addLayout(alt)

        layout.addWidget(kart)

        # Kalemler Tablosu
        tablo = QTableWidget()
        tablo.setColumnCount(6)
        tablo.setHorizontalHeaderLabels([
            "Parça Kodu", "Ürün Adı", "Adet", "Birim Fiyat", "KDV", "Toplam Tutar"
        ])
        tablo.setAlternatingRowColors(True)
        tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        for idx, k in enumerate(self.siparis.kalemler):
            tablo.insertRow(idx)
            tablo.setItem(idx, 0, QTableWidgetItem(k.parca_kodu_anlik))
            tablo.setItem(idx, 1, QTableWidgetItem(k.urun_adi_anlik))
            tablo.setItem(idx, 2, QTableWidgetItem(str(k.adet)))
            tablo.setItem(idx, 3, QTableWidgetItem(kurus_to_tl_str(k.birim_fiyat_kurus)))
            tablo.setItem(idx, 4, QTableWidgetItem(f"%{k.kdv_orani}"))
            tablo.setItem(idx, 5, QTableWidgetItem(kurus_to_tl_str(k.toplam_kurus)))

        layout.addWidget(tablo)

        # Toplamlar
        toplam_kutu = QHBoxLayout()
        toplam_kutu.addStretch()
        toplam_kutu.addWidget(QLabel(f"Ara Toplam: <b>{kurus_to_tl_str(self.siparis.ara_toplam_kurus)}</b>"))
        toplam_kutu.addWidget(QLabel(f"KDV: <b>{kurus_to_tl_str(self.siparis.kdv_toplam_kurus)}</b>"))
        toplam_kutu.addWidget(QLabel(f"GENEL TOPLAM: <b style='color:#2ecc71; font-size:12pt;'>{kurus_to_tl_str(self.siparis.genel_toplam_kurus)}</b>"))
        layout.addLayout(toplam_kutu)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setObjectName("btnSecondary")
        btn_kapat.clicked.connect(self.accept)
        layout.addWidget(btn_kapat, alignment=QtCore.Qt.AlignRight)


class SiparislerPage(QWidget):
    """Geçmiş Siparişlerin Listelendiği ve İptal/İade Edildiği Ekran."""

    def __init__(
        self,
        satis_servisi: SatisServisi,
        musteri_servisi: MusteriServisi,
        aktif_kullanici=None,
        parent=None
    ):
        super().__init__(parent)
        self.satis_servisi = satis_servisi
        self.musteri_servisi = musteri_servisi
        self.aktif_kullanici = aktif_kullanici

        self.init_ui()
        self.musterileri_doldur()
        self.listeyi_guncelle()

    def init_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(12)

        # Üst Başlık
        ust_bar = QHBoxLayout()
        baslik = QLabel("📋 SİPARİŞ GEÇMİŞİ & İPTAL / İADE")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        self.btn_yenile = QPushButton("🔄 Yenile")
        self.btn_yenile.setObjectName("btnSecondary")
        self.btn_yenile.clicked.connect(self.listeyi_guncelle)
        ust_bar.addWidget(self.btn_yenile)

        ana_layout.addLayout(ust_bar)

        # Filtre Paneli
        filtre_kart = QFrame()
        filtre_kart.setObjectName("filterFrame")
        filtre_layout = QHBoxLayout(filtre_kart)
        filtre_layout.setContentsMargins(10, 8, 10, 8)
        filtre_layout.setSpacing(10)

        # Tarih filtreleri
        filtre_layout.addWidget(QLabel("Tarih Aralığı:"))
        self.dt_baslangic = QDateEdit()
        self.dt_baslangic.setCalendarPopup(True)
        self.dt_baslangic.setDate(QtCore.QDate.currentDate().addDays(-30))
        filtre_layout.addWidget(self.dt_baslangic)

        self.dt_bitis = QDateEdit()
        self.dt_bitis.setCalendarPopup(True)
        self.dt_bitis.setDate(QtCore.QDate.currentDate())
        filtre_layout.addWidget(self.dt_bitis)

        # Hızlı Tarih Butonları
        self.btn_bugun = QPushButton("Bugün")
        self.btn_bugun.setMinimumWidth(75)
        self.btn_bugun.clicked.connect(self.tarih_bugun)
        filtre_layout.addWidget(self.btn_bugun)

        # Müşteri
        self.cmb_musteri = QComboBox()
        self.cmb_musteri.currentIndexChanged.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.cmb_musteri, stretch=2)

        # Durum
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItem("Tüm Durumlar", None)
        self.cmb_durum.addItem("Tamamlananlar", "tamamlandi")
        self.cmb_durum.addItem("İptal Edilenler", "iptal")
        self.cmb_durum.currentIndexChanged.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.cmb_durum, stretch=1)

        self.btn_filtrele = QPushButton("Filtrele")
        self.btn_filtrele.clicked.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.btn_filtrele)

        ana_layout.addWidget(filtre_kart)

        # Siparişler Tablosu
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(9)
        self.tablo.setHorizontalHeaderLabels([
            "ID", "Sipariş No", "Tarih", "Müşteri", "Ara Toplam",
            "KDV", "Genel Toplam", "Ödeme Tipi", "Durum"
        ])
        self.tablo.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tablo.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tablo.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tablo.horizontalHeader().setMinimumSectionSize(65)
        sip_widths = [50, 140, 130, 200, 95, 80, 105, 95, 85]
        for col, w in enumerate(sip_widths):
            self.tablo.setColumnWidth(col, w)
        self.tablo.doubleClicked.connect(self.detay_goster)
        ana_layout.addWidget(self.tablo, stretch=1)

        # Alt Butonlar
        alt_bar = QHBoxLayout()

        self.btn_detay = QPushButton("👁️ Sipariş Detayı / Kalemler")
        self.btn_detay.clicked.connect(self.detay_goster)
        alt_bar.addWidget(self.btn_detay)

        self.btn_iptal = QPushButton("❌ Siparişi İptal Et (Stoğu İade Al)")
        self.btn_iptal.setObjectName("btnDanger")
        self.btn_iptal.clicked.connect(self.siparis_iptal_et)
        alt_bar.addWidget(self.btn_iptal)

        alt_bar.addStretch()
        self.lbl_bilgi = QLabel("Toplam 0 sipariş listelendi.")
        alt_bar.addWidget(self.lbl_bilgi)

        ana_layout.addLayout(alt_bar)

    def musterileri_doldur(self):
        self.cmb_musteri.blockSignals(True)
        self.cmb_musteri.clear()
        self.cmb_musteri.addItem("Tüm Müşteriler", None)
        for m in self.musteri_servisi.musterileri_getir():
            self.cmb_musteri.addItem(m.ad_soyad, m.id)
        self.cmb_musteri.blockSignals(False)

    def tarih_bugun(self):
        bugun = QtCore.QDate.currentDate()
        self.dt_baslangic.setDate(bugun)
        self.dt_bitis.setDate(bugun)
        self.listeyi_guncelle()

    def listeyi_guncelle(self):
        baslangic = self.dt_baslangic.date().toString("yyyy-MM-dd")
        bitis = self.dt_bitis.date().toString("yyyy-MM-dd")
        musteri_id = self.cmb_musteri.currentData()
        durum = self.cmb_durum.currentData()

        siparisler = self.satis_servisi.siparisleri_getir(
            musteri_id=musteri_id,
            durum=durum,
            baslangic_tarih=baslangic,
            bitis_tarih=bitis,
            limit=200
        )

        self.tablo.setRowCount(0)
        for satir_idx, s in enumerate(siparisler):
            self.tablo.insertRow(satir_idx)
            self.tablo.setItem(satir_idx, 0, QTableWidgetItem(str(s.id)))
            self.tablo.setItem(satir_idx, 1, QTableWidgetItem(s.siparis_no))
            self.tablo.setItem(satir_idx, 2, QTableWidgetItem(str(s.tarih)))
            self.tablo.setItem(satir_idx, 3, QTableWidgetItem(s.musteri_adi))
            self.tablo.setItem(satir_idx, 4, QTableWidgetItem(kurus_to_tl_str(s.ara_toplam_kurus)))
            self.tablo.setItem(satir_idx, 5, QTableWidgetItem(kurus_to_tl_str(s.kdv_toplam_kurus)))
            self.tablo.setItem(satir_idx, 6, QTableWidgetItem(kurus_to_tl_str(s.genel_toplam_kurus)))
            self.tablo.setItem(satir_idx, 7, QTableWidgetItem(s.odeme_tipi.upper()))

            durum_item = QTableWidgetItem(s.durum.upper())
            if s.durum == "iptal":
                durum_item.setForeground(QtGui.QColor("#ff4757"))
            else:
                durum_item.setForeground(QtGui.QColor("#2ed573"))
            self.tablo.setItem(satir_idx, 8, durum_item)

        self.lbl_bilgi.setText(f"Toplam {len(siparisler)} sipariş listelendi.")

    def secili_siparis_id(self):
        secili = self.tablo.selectedItems()
        if not secili:
            return None
        satir = secili[0].row()
        return int(self.tablo.item(satir, 0).text())

    def detay_goster(self):
        s_id = self.secili_siparis_id()
        if not s_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen detayını görmek istediğiniz siparişi seçiniz.")
            return

        siparis = self.satis_servisi.siparis_detay_getir(s_id)
        if not siparis:
            QMessageBox.critical(self, "Hata", "Sipariş bulunamadı.")
            return

        diyalog = SiparisDetayDiyalog(siparis, self)
        diyalog.exec_()

    def siparis_iptal_et(self):
        s_id = self.secili_siparis_id()
        if not s_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen iptal etmek istediğiniz siparişi seçiniz.")
            return

        siparis = self.satis_servisi.siparis_detay_getir(s_id)
        if not siparis:
            return

        if siparis.durum == "iptal":
            QMessageBox.warning(self, "İptal Edilmiş", "Bu sipariş zaten iptal edilmiştir.")
            return

        onay = QMessageBox.question(
            self,
            "Sipariş İptal Onayı",
            f"#{siparis.siparis_no} numaralı siparişi iptal etmek istediğinizden emin misiniz?\n\n"
            f"Bu işlem ile:\n"
            f"- Siparişteki tüm ürünler ({len(siparis.kalemler)} kalem) otomatik olarak depoya geri eklenecektir.\n"
            f"- Veresiyeli satış ise müşteri cari borcu {kurus_to_tl_str(siparis.genel_toplam_kurus)} düşülecektir.\n"
            f"- Stok hareket defterine iptal kaydı düşülecektir.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if onay == QMessageBox.Yes:
            neden, ok = QtWidgets.QInputDialog.getText(
                self, "İptal Gerekçesi", "Lütfen iptal / iade gerekçesini giriniz:"
            )
            aciklama = neden.strip() if ok else "Müşteri isteği ile iptal"
            try:
                kullanici_id = self.aktif_kullanici.id if self.aktif_kullanici else None
                self.satis_servisi.siparis_iptal_et(
                    siparis_id=s_id,
                    aciklama=aciklama,
                    kullanici_id=kullanici_id
                )
                QMessageBox.information(
                    self,
                    "İptal Başarılı",
                    f"#{siparis.siparis_no} siparişi iptal edildi ve stoklar depoya iade alındı."
                )
                self.listeyi_guncelle()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
