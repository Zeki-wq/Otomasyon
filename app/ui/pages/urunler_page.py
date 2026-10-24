"""
Ürün Yönetimi ve Hızlı Arama Sayfası
50.000 kaleme kadar anlık filtreleme, sayfalama, ekleme, düzenleme ve pasife alma.
"""

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import Urun
from app.domain.money import kurus_to_tl_str
from app.domain.validators import ValidationError, sayisal_fiyat_dogrula
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi


class UrunDiyalog(QDialog):
    """Yeni ürün ekleme ve mevcut ürünü düzenleme diyaloğu."""

    def __init__(self, parent=None, urun_servisi: UrunServisi = None, urun: Urun = None, aktif_kullanici=None):
        super().__init__(parent)
        self.urun_servisi = urun_servisi
        self.urun = urun
        self.aktif_kullanici = aktif_kullanici
        self.setWindowTitle("Ürün Düzenle" if urun else "Yeni Ürün Ekle")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(740, 680)
        self.resize(750, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Başlık
        baslik = QLabel("✏️ ÜRÜN BİLGİLERİ" if self.urun else "📦 YENİ PARÇA KAYDI")
        baslik.setObjectName("headerTitle")
        layout.addWidget(baslik)

        form_frame = QFrame()
        form_frame.setObjectName("cardFrame")
        form_grid = QGridLayout(form_frame)
        form_grid.setSpacing(12)
        form_grid.setContentsMargins(15, 15, 15, 15)

        # 1. Parça Kodu ve Alış Fiyatı
        kod_kutu = QVBoxLayout()
        self.txt_kod = QLineEdit()
        self.txt_kod.setPlaceholderText("Örn: BRM-001")
        self.txt_kod.textChanged.connect(lambda: self._hata_temizle(self.txt_kod, self.lbl_kod_hata))
        kod_kutu.addWidget(self.txt_kod)
        self.lbl_kod_hata = QLabel("")
        self.lbl_kod_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_kod_hata.setWordWrap(True)
        self.lbl_kod_hata.hide()
        kod_kutu.addWidget(self.lbl_kod_hata)
        form_grid.addWidget(QLabel("Parça Kodu (*):"), 0, 0)
        form_grid.addLayout(kod_kutu, 0, 1)

        alis_kutu = QVBoxLayout()
        self.txt_alis = QLineEdit()
        self.txt_alis.setPlaceholderText("0,00 ₺")
        self.txt_alis.textChanged.connect(lambda: self._hata_temizle(self.txt_alis, self.lbl_alis_hata))
        alis_kutu.addWidget(self.txt_alis)
        self.lbl_alis_hata = QLabel("")
        self.lbl_alis_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_alis_hata.setWordWrap(True)
        self.lbl_alis_hata.hide()
        alis_kutu.addWidget(self.lbl_alis_hata)
        form_grid.addWidget(QLabel("Alış Fiyatı:"), 0, 2)
        form_grid.addLayout(alis_kutu, 0, 3)

        # 2. Parça Adı ve Satış Fiyatı
        ad_kutu = QVBoxLayout()
        self.txt_ad = QLineEdit()
        self.txt_ad.setPlaceholderText("Örn: Ön Fren Diski")
        self.txt_ad.textChanged.connect(lambda: self._hata_temizle(self.txt_ad, self.lbl_ad_hata))
        ad_kutu.addWidget(self.txt_ad)
        self.lbl_ad_hata = QLabel("")
        self.lbl_ad_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_ad_hata.setWordWrap(True)
        self.lbl_ad_hata.hide()
        ad_kutu.addWidget(self.lbl_ad_hata)
        form_grid.addWidget(QLabel("Parça Adı (*):"), 1, 0)
        form_grid.addLayout(ad_kutu, 1, 1)

        satis_kutu = QVBoxLayout()
        self.txt_satis = QLineEdit()
        self.txt_satis.setPlaceholderText("0,00 ₺")
        self.txt_satis.textChanged.connect(lambda: self._hata_temizle(self.txt_satis, self.lbl_satis_hata))
        satis_kutu.addWidget(self.txt_satis)
        self.lbl_satis_hata = QLabel("")
        self.lbl_satis_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_satis_hata.setWordWrap(True)
        self.lbl_satis_hata.hide()
        satis_kutu.addWidget(self.lbl_satis_hata)
        form_grid.addWidget(QLabel("Satış Fiyatı (*):"), 1, 2)
        form_grid.addLayout(satis_kutu, 1, 3)

        # 3. Marka ve KDV Oranı
        marka_layout = QHBoxLayout()
        self.cmb_marka = QComboBox()
        self.btn_yeni_marka = QPushButton("+")
        self.btn_yeni_marka.setFixedWidth(35)
        self.btn_yeni_marka.clicked.connect(self.yeni_marka_ekle)
        marka_layout.addWidget(self.cmb_marka)
        marka_layout.addWidget(self.btn_yeni_marka)
        form_grid.addWidget(QLabel("Marka:"), 2, 0)
        form_grid.addLayout(marka_layout, 2, 1)

        self.spn_kdv = QSpinBox()
        self.spn_kdv.setRange(0, 100)
        self.spn_kdv.setValue(20)
        self.spn_kdv.setSuffix(" %")
        form_grid.addWidget(QLabel("KDV Oranı:"), 2, 2)
        form_grid.addWidget(self.spn_kdv, 2, 3)

        # 4. Kategori ve Stok
        kat_layout = QHBoxLayout()
        self.cmb_kat = QComboBox()
        self.btn_yeni_kat = QPushButton("+")
        self.btn_yeni_kat.setFixedWidth(35)
        self.btn_yeni_kat.clicked.connect(self.yeni_kategori_ekle)
        kat_layout.addWidget(self.cmb_kat)
        kat_layout.addWidget(self.btn_yeni_kat)
        form_grid.addWidget(QLabel("Kategori:"), 3, 0)
        form_grid.addLayout(kat_layout, 3, 1)

        self.spn_stok = QSpinBox()
        self.spn_stok.setRange(0, 100000)
        self.spn_stok.setValue(0)
        if self.urun:
            self.spn_stok.setEnabled(False)
        form_grid.addWidget(QLabel("Açılış Stoğu:"), 3, 2)
        form_grid.addWidget(self.spn_stok, 3, 3)

        # 5. Barkod ve Kritik Stok
        self.txt_barkod = QLineEdit()
        self.txt_barkod.setPlaceholderText("Barkod okutun veya yazın")
        form_grid.addWidget(QLabel("Barkod:"), 4, 0)
        form_grid.addWidget(self.txt_barkod, 4, 1)

        self.spn_kritik = QSpinBox()
        self.spn_kritik.setRange(0, 1000)
        self.spn_kritik.setValue(5)
        form_grid.addWidget(QLabel("Kritik Stok:"), 4, 2)
        form_grid.addWidget(self.spn_kritik, 4, 3)

        # 6. OEM No ve Raf / Konum
        self.txt_oem = QLineEdit()
        self.txt_oem.setPlaceholderText("Örn: 1K0615301T")
        form_grid.addWidget(QLabel("OEM Numarası:"), 5, 0)
        form_grid.addWidget(self.txt_oem, 5, 1)

        self.txt_raf = QLineEdit()
        self.txt_raf.setPlaceholderText("Örn: A-12 / Raf 3")
        form_grid.addWidget(QLabel("Raf / Konum:"), 5, 2)
        form_grid.addWidget(self.txt_raf, 5, 3)

        # 7. Durum (Aktif / Pasif)
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItem("✅ Aktif", 1)
        self.cmb_durum.addItem("⛔ Pasif", 0)
        form_grid.addWidget(QLabel("Durum:"), 6, 0)
        form_grid.addWidget(self.cmb_durum, 6, 1)

        lbl_durum_ipucu = QLabel("ℹ️ Pasif ürünler satış ekranında listelenmez.")
        lbl_durum_ipucu.setStyleSheet("color: #718093; font-size: 8.5pt;")
        form_grid.addWidget(lbl_durum_ipucu, 6, 2, 1, 2)

        # 8. Açıklama (Tüm satır)
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMinimumHeight(60)
        self.txt_aciklama.setPlaceholderText("Uyumlu araçlar veya ek notlar...")
        form_grid.addWidget(QLabel("Açıklama:"), 7, 0)
        form_grid.addWidget(self.txt_aciklama, 7, 1, 1, 3)

        layout.addWidget(form_frame)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.btn_kaydet = QPushButton("💾 Kaydet")
        self.btn_kaydet.setObjectName("btnSuccess")
        self.btn_kaydet.clicked.connect(self.kaydet)

        self.btn_iptal = QPushButton("İptal")
        self.btn_iptal.setObjectName("btnSecondary")
        self.btn_iptal.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_iptal)
        btn_layout.addWidget(self.btn_kaydet)
        layout.addLayout(btn_layout)

        self.markalari_doldur()
        self.kategorileri_doldur()

        # Düzenleme modundaysa mevcut verileri doldur
        if self.urun:
            self.verileri_yukle()

    def markalari_doldur(self):
        self.cmb_marka.clear()
        self.cmb_marka.addItem("Seçiniz...", None)
        if self.urun_servisi:
            for m in self.urun_servisi.markalari_getir():
                self.cmb_marka.addItem(m.ad, m.id)

    def kategorileri_doldur(self):
        self.cmb_kat.clear()
        self.cmb_kat.addItem("Seçiniz...", None)
        if self.urun_servisi:
            for k in self.urun_servisi.kategorileri_getir():
                self.cmb_kat.addItem(k.ad, k.id)

    def yeni_marka_ekle(self):
        ad, ok = QtWidgets.QInputDialog.getText(self, "Yeni Marka", "Marka Adı:")
        if ok and ad.strip():
            try:
                yeni_id = self.urun_servisi.marka_ekle(ad.strip())
                self.markalari_doldur()
                index = self.cmb_marka.findData(yeni_id)
                if index >= 0:
                    self.cmb_marka.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.warning(self, "Hata", str(e))

    def yeni_kategori_ekle(self):
        ad, ok = QtWidgets.QInputDialog.getText(self, "Yeni Kategori", "Kategori Adı:")
        if ok and ad.strip():
            try:
                yeni_id = self.urun_servisi.kategori_ekle(ad.strip())
                self.kategorileri_doldur()
                index = self.cmb_kat.findData(yeni_id)
                if index >= 0:
                    self.cmb_kat.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.warning(self, "Hata", str(e))

    def verileri_yukle(self):
        self.txt_kod.setText(self.urun.parca_kodu)
        self.txt_ad.setText(self.urun.ad)
        self.txt_barkod.setText(self.urun.barkod)
        self.txt_oem.setText(self.urun.oem_no)

        m_idx = self.cmb_marka.findData(self.urun.marka_id)
        if m_idx >= 0:
            self.cmb_marka.setCurrentIndex(m_idx)

        k_idx = self.cmb_kat.findData(self.urun.kategori_id)
        if k_idx >= 0:
            self.cmb_kat.setCurrentIndex(k_idx)

        self.txt_alis.setText(kurus_to_tl_str(self.urun.alis_fiyati_kurus, sembol=False))
        self.txt_satis.setText(kurus_to_tl_str(self.urun.satis_fiyati_kurus, sembol=False))
        self.spn_kdv.setValue(self.urun.kdv_orani)
        self.spn_stok.setValue(self.urun.stok)
        self.spn_kritik.setValue(self.urun.kritik_stok)
        self.txt_raf.setText(self.urun.raf_yeri)
        self.txt_aciklama.setPlainText(self.urun.aciklama)

        durum_idx = self.cmb_durum.findData(self.urun.aktif if self.urun.aktif is not None else 1)
        if durum_idx >= 0:
            self.cmb_durum.setCurrentIndex(durum_idx)

        # Pasif ürünü tekrar aktife alma yetkisi yalnızca yöneticidedir
        is_yonetici = bool(self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici")
        if self.urun.aktif == 0 and not is_yonetici:
            self.cmb_durum.setEnabled(False)
            self.cmb_durum.setToolTip("Yalnızca yönetici pasif ürünü aktife alabilir.")

    def _hata_ayarla(self, widget: QWidget, label: QLabel, mesaj: str):
        widget.setStyleSheet("border: 1.5px solid #ff4757; background-color: #2d1f24;")
        label.setText(f"⚠️ {mesaj}")
        label.setStyleSheet("font-size: 8pt; color: #ff4757;")
        label.show()

    def _hata_temizle(self, widget: QWidget, label: QLabel):
        widget.setStyleSheet("")
        label.setText("")
        label.hide()

    def kaydet(self):
        ilk_hatali = None

        # 1. Parça Kodu Kontrolü
        kod = self.txt_kod.text().strip().upper()
        if not kod:
            self._hata_ayarla(self.txt_kod, self.lbl_kod_hata, "Lütfen bir parça kodu giriniz.")
            if not ilk_hatali:
                ilk_hatali = self.txt_kod
        else:
            self._hata_temizle(self.txt_kod, self.lbl_kod_hata)

        # 2. Parça Adı Kontrolü
        ad = self.txt_ad.text().strip()
        if not ad or len(ad) < 2:
            self._hata_ayarla(self.txt_ad, self.lbl_ad_hata, "Parça adı en az 2 karakter olmalıdır.")
            if not ilk_hatali:
                ilk_hatali = self.txt_ad
        else:
            self._hata_temizle(self.txt_ad, self.lbl_ad_hata)

        # 3. Alış Fiyatı Kontrolü
        alis_kurus = 0
        try:
            alis_kurus = sayisal_fiyat_dogrula(self.txt_alis.text(), "Alış Fiyatı")
            self._hata_temizle(self.txt_alis, self.lbl_alis_hata)
        except (ValueError, ValidationError) as e:
            self._hata_ayarla(self.txt_alis, self.lbl_alis_hata, str(e))
            if not ilk_hatali:
                ilk_hatali = self.txt_alis

        # 4. Satış Fiyatı Kontrolü
        satis_kurus = 0
        try:
            satis_kurus = sayisal_fiyat_dogrula(self.txt_satis.text(), "Satış Fiyatı")
            if satis_kurus <= 0:
                self._hata_ayarla(self.txt_satis, self.lbl_satis_hata, "Satış fiyatı 0'dan büyük olmalıdır.")
                if not ilk_hatali:
                    ilk_hatali = self.txt_satis
            else:
                self._hata_temizle(self.txt_satis, self.lbl_satis_hata)
        except (ValueError, ValidationError) as e:
            self._hata_ayarla(self.txt_satis, self.lbl_satis_hata, str(e))
            if not ilk_hatali:
                ilk_hatali = self.txt_satis

        # Hatalı alan varsa diyalog açık kalır ve ilk alana odaklanır
        if ilk_hatali:
            ilk_hatali.setFocus()
            return

        kategori_id = self.cmb_kat.currentData()
        marka_id = self.cmb_marka.currentData()
        yeni_aktif = self.cmb_durum.currentData()
        if yeni_aktif is None:
            yeni_aktif = 1
        kullanici_id = self.aktif_kullanici.id if self.aktif_kullanici else None

        try:
            if self.urun:
                eski_aktif = self.urun.aktif
                if eski_aktif == 0 and yeni_aktif == 1:
                    is_yonetici = bool(self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici")
                    if not is_yonetici:
                        QMessageBox.warning(self, "Yetkisiz İşlem", "Yalnızca yönetici pasif ürünü aktife alabilir.")
                        return

                # Güncelleme
                self.urun.parca_kodu = kod
                self.urun.ad = ad
                self.urun.barkod = self.txt_barkod.text().strip()
                self.urun.oem_no = self.txt_oem.text().strip().upper()
                self.urun.kategori_id = kategori_id
                self.urun.marka_id = marka_id
                self.urun.alis_fiyati_kurus = alis_kurus
                self.urun.satis_fiyati_kurus = satis_kurus
                self.urun.kdv_orani = self.spn_kdv.value()
                self.urun.kritik_stok = self.spn_kritik.value()
                self.urun.raf_yeri = self.txt_raf.text().strip()
                self.urun.aciklama = self.txt_aciklama.toPlainText().strip()
                self.urun.aktif = yeni_aktif

                self.urun_servisi.urun_guncelle(self.urun)

                # Durum değiştiyse denetim ve hareket kaydını da oluştur
                if eski_aktif != yeni_aktif:
                    if yeni_aktif == 1:
                        self.urun_servisi.urun_aktife_al(self.urun.id, kullanici_id=kullanici_id)
                    else:
                        self.urun_servisi.urun_pasife_al(self.urun.id, kullanici_id=kullanici_id)

                QMessageBox.information(self, "Başarılı", "Ürün bilgileri başarıyla güncellendi.")
            else:
                # Yeni Ekleme
                yeni = Urun(
                    id=None,
                    parca_kodu=kod,
                    ad=ad,
                    barkod=self.txt_barkod.text().strip(),
                    oem_no=self.txt_oem.text().strip().upper(),
                    kategori_id=kategori_id,
                    marka_id=marka_id,
                    alis_fiyati_kurus=alis_kurus,
                    satis_fiyati_kurus=satis_kurus,
                    kdv_orani=self.spn_kdv.value(),
                    stok=self.spn_stok.value(),
                    kritik_stok=self.spn_kritik.value(),
                    raf_yeri=self.txt_raf.text().strip(),
                    aciklama=self.txt_aciklama.toPlainText().strip(),
                    aktif=yeni_aktif
                )
                self.urun_servisi.urun_ekle(yeni)
                QMessageBox.information(self, "Başarılı", f"'{ad}' başarıyla depoya eklendi.")

            self.accept()
        except ValidationError as ve:
            self._hata_ayarla(self.txt_kod, self.lbl_kod_hata, str(ve))
            self.txt_kod.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class UrunlerPage(QWidget):
    """Parça ve Ürün Yönetimi Ana Ekranı."""

    def __init__(self, urun_servisi: UrunServisi, stok_servisi: StokServisi, aktif_kullanici=None, parent=None):
        super().__init__(parent)
        self.urun_servisi = urun_servisi
        self.stok_servisi = stok_servisi
        self.aktif_kullanici = aktif_kullanici

        self.sayfa_no = 1
        self.sayfa_boyutu = 50
        self.toplam_urun = 0

        # Hızlı arama için geciktirme sayacı (debouncing)
        self.arama_timer = QtCore.QTimer()
        self.arama_timer.setSingleShot(True)
        self.arama_timer.setInterval(250)
        self.arama_timer.timeout.connect(self.listeyi_guncelle)

        self.init_ui()
        self.filtreleri_doldur()
        self.listeyi_guncelle()

    def init_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(12)

        # 1. Üst Başlık ve İstatistik Çubuğu
        ust_bar = QHBoxLayout()
        baslik = QLabel("📦 PARÇA VE DEPO YÖNETİMİ")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        self.lbl_ozet = QLabel("Yükleniyor...")
        self.lbl_ozet.setStyleSheet("color: #00a8ff; font-weight: bold;")
        ust_bar.addWidget(self.lbl_ozet)

        self.btn_yeni_urun = QPushButton("➕ Yeni Ürün Ekle")
        self.btn_yeni_urun.setObjectName("btnSuccess")
        self.btn_yeni_urun.clicked.connect(self.yeni_urun_ac)
        ust_bar.addWidget(self.btn_yeni_urun)

        ana_layout.addLayout(ust_bar)

        # 2. Arama ve Filtreleme Kartı
        filtre_kart = QFrame()
        filtre_kart.setObjectName("filterFrame")
        filtre_layout = QHBoxLayout(filtre_kart)
        filtre_layout.setContentsMargins(10, 8, 10, 8)
        filtre_layout.setSpacing(10)

        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("🔍 Parça kodu, ad, OEM, barkod veya marka ile hızlı ara... (Enter)")
        self.txt_ara.textChanged.connect(self.arama_tetikle)
        self.txt_ara.returnPressed.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.txt_ara, stretch=4)

        self.cmb_filtre_kat = QComboBox()
        self.cmb_filtre_kat.currentIndexChanged.connect(self.filtre_degisti)
        filtre_layout.addWidget(self.cmb_filtre_kat, stretch=2)

        self.cmb_filtre_marka = QComboBox()
        self.cmb_filtre_marka.currentIndexChanged.connect(self.filtre_degisti)
        filtre_layout.addWidget(self.cmb_filtre_marka, stretch=2)

        self.cmb_aktiflik = QComboBox()
        self.cmb_aktiflik.addItem("Yalnızca Aktifler", "aktif")
        self.cmb_aktiflik.addItem("Yalnızca Pasifler", "pasif")
        self.cmb_aktiflik.addItem("Tüm Ürünler (Aktif + Pasif)", "tumu")
        self.cmb_aktiflik.currentIndexChanged.connect(self.filtre_degisti)
        filtre_layout.addWidget(self.cmb_aktiflik, stretch=2)

        self.btn_temizle = QPushButton("Temizle")
        self.btn_temizle.setObjectName("btnSecondary")
        self.btn_temizle.clicked.connect(self.filtreleri_temizle)
        filtre_layout.addWidget(self.btn_temizle)

        ana_layout.addWidget(filtre_kart)

        # 3. Ürün Tablosu
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(13)
        self.tablo.setHorizontalHeaderLabels([
            "ID", "Parça Kodu", "Barkod", "OEM No", "Ürün Adı",
            "Marka", "Kategori", "Raf", "Alış (₺)", "Satış (₺)",
            "KDV", "Stok", "Durum"
        ])
        self.tablo.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tablo.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tablo.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tablo.horizontalHeader().setMinimumSectionSize(60)
        widths = [50, 110, 95, 105, 240, 95, 110, 70, 90, 90, 65, 65, 75]
        for col, w in enumerate(widths):
            self.tablo.setColumnWidth(col, w)
        self.tablo.doubleClicked.connect(self.urun_duzenle_ac)
        self.tablo.itemSelectionChanged.connect(self.satir_secildi)
        ana_layout.addWidget(self.tablo, stretch=1)

        # 4. Alt İşlem Çubuğu ve Sayfalama
        alt_bar = QHBoxLayout()

        self.btn_duzenle = QPushButton("✏️ Düzenle")
        self.btn_duzenle.clicked.connect(self.urun_duzenle_ac)
        alt_bar.addWidget(self.btn_duzenle)

        self.btn_stok_duzelt = QPushButton("📦 Stok Düzelt")
        self.btn_stok_duzelt.setObjectName("btnSecondary")
        self.btn_stok_duzelt.clicked.connect(self.stok_duzelt_ac)
        alt_bar.addWidget(self.btn_stok_duzelt)

        self.btn_sil = QPushButton("🗑️ Pasife Al")
        self.btn_sil.setObjectName("btnDanger")
        self.btn_sil.clicked.connect(self.urun_pasife_al)
        alt_bar.addWidget(self.btn_sil)

        self.btn_aktife_al = QPushButton("♻️ Aktife Al")
        self.btn_aktife_al.setObjectName("btnSuccess")
        self.btn_aktife_al.clicked.connect(self.urun_aktife_al)
        self.btn_aktife_al.hide()
        alt_bar.addWidget(self.btn_aktife_al)

        alt_bar.addStretch()

        # Sayfalama
        self.btn_onceki = QPushButton("◀ Önceki")
        self.btn_onceki.clicked.connect(self.onceki_sayfa)
        alt_bar.addWidget(self.btn_onceki)

        self.lbl_sayfa = QLabel("Sayfa 1 / 1")
        self.lbl_sayfa.setStyleSheet("font-weight: bold; padding: 0 10px;")
        alt_bar.addWidget(self.lbl_sayfa)

        self.btn_sonraki = QPushButton("Sonraki ▶")
        self.btn_sonraki.clicked.connect(self.sonraki_sayfa)
        alt_bar.addWidget(self.btn_sonraki)

        ana_layout.addLayout(alt_bar)

    def filtreleri_doldur(self):
        self.cmb_filtre_kat.blockSignals(True)
        self.cmb_filtre_marka.blockSignals(True)

        self.cmb_filtre_kat.clear()
        self.cmb_filtre_kat.addItem("Tüm Kategoriler", None)
        for k in self.urun_servisi.kategorileri_getir():
            self.cmb_filtre_kat.addItem(k.ad, k.id)

        self.cmb_filtre_marka.clear()
        self.cmb_filtre_marka.addItem("Tüm Markalar", None)
        for m in self.urun_servisi.markalari_getir():
            self.cmb_filtre_marka.addItem(m.ad, m.id)

        self.cmb_filtre_kat.blockSignals(False)
        self.cmb_filtre_marka.blockSignals(False)

    def arama_tetikle(self):
        self.arama_timer.start()

    def filtre_degisti(self):
        self.sayfa_no = 1
        self.listeyi_guncelle()

    def filtreleri_temizle(self):
        self.txt_ara.clear()
        self.cmb_filtre_kat.setCurrentIndex(0)
        self.cmb_filtre_marka.setCurrentIndex(0)
        self.cmb_aktiflik.setCurrentIndex(0)
        self.sayfa_no = 1
        self.listeyi_guncelle()

    def listeyi_guncelle(self):
        terim = self.txt_ara.text().strip()
        kat_id = self.cmb_filtre_kat.currentData()
        marka_id = self.cmb_filtre_marka.currentData()
        aktiflik = self.cmb_aktiflik.currentData()

        self.toplam_urun = self.urun_servisi.toplam_urun_sayisi(
            terim=terim,
            kategori_id=kat_id,
            marka_id=marka_id,
            aktiflik_filtresi=aktiflik
        )

        toplam_sayfa = max(1, (self.toplam_urun + self.sayfa_boyutu - 1) // self.sayfa_boyutu)
        self.sayfa_no = min(self.sayfa_no, toplam_sayfa)

        offset = (self.sayfa_no - 1) * self.sayfa_boyutu

        urunler = self.urun_servisi.urun_ara(
            terim=terim,
            kategori_id=kat_id,
            marka_id=marka_id,
            aktiflik_filtresi=aktiflik,
            limit=self.sayfa_boyutu,
            offset=offset
        )

        # Tabloyu doldur
        self.tablo.setRowCount(0)
        for satir_idx, u in enumerate(urunler):
            self.tablo.insertRow(satir_idx)

            items = [
                QTableWidgetItem(str(u.id)),
                QTableWidgetItem(u.parca_kodu),
                QTableWidgetItem(u.barkod),
                QTableWidgetItem(u.oem_no),
                QTableWidgetItem(u.ad),
                QTableWidgetItem(u.marka_adi),
                QTableWidgetItem(u.kategori_adi),
                QTableWidgetItem(u.raf_yeri),
                QTableWidgetItem(kurus_to_tl_str(u.alis_fiyati_kurus)),
                QTableWidgetItem(kurus_to_tl_str(u.satis_fiyati_kurus)),
                QTableWidgetItem(f"%{u.kdv_orani}"),
            ]

            # Pasif ürünlerde satırı soluklaştır
            if u.aktif == 0:
                for it in items:
                    it.setForeground(QtGui.QColor("#718093"))

            for col_idx, it in enumerate(items):
                self.tablo.setItem(satir_idx, col_idx, it)

            # Stok hücresi (Kritikse uyar)
            stok_item = QTableWidgetItem(str(u.stok))
            if u.aktif == 0:
                stok_item.setForeground(QtGui.QColor("#718093"))
            elif u.stok <= u.kritik_stok:
                stok_item.setForeground(QtGui.QColor("#ff4757"))
                stok_item.setToolTip(f"Kritik stok seviyesinde! (Kritik: {u.kritik_stok})")
            self.tablo.setItem(satir_idx, 11, stok_item)

            if u.aktif == 1:
                durum_item = QTableWidgetItem("✅ Aktif")
                durum_item.setForeground(QtGui.QColor("#2ecc71"))
            else:
                durum_item = QTableWidgetItem("⛔ Pasif")
                durum_item.setForeground(QtGui.QColor("#e74c3c"))
                durum_item.setToolTip("Bu ürün pasif durumdadır. Satış ekranında çıkmaz.")
            self.tablo.setItem(satir_idx, 12, durum_item)

        # Sayfalama butonları
        self.lbl_sayfa.setText(f"Sayfa {self.sayfa_no} / {toplam_sayfa}")
        self.btn_onceki.setEnabled(self.sayfa_no > 1)
        self.btn_sonraki.setEnabled(self.sayfa_no < toplam_sayfa)

        # Özet bilgi
        if self.toplam_urun == 0:
            self.lbl_ozet.setText("🔍 Arama kriterlerine uygun ürün bulunamadı.")
            self.lbl_ozet.setStyleSheet("color: #ff9f43; font-weight: bold;")
        else:
            kritik_sayisi = self.stok_servisi.kritik_stok_sayisi()
            self.lbl_ozet.setText(f"Toplam: {self.toplam_urun} Ürün  |  ⚠️ Kritik Stok: {kritik_sayisi}")
            self.lbl_ozet.setStyleSheet("color: #00a8ff; font-weight: bold;")
        self.satir_secildi()

    def satir_secildi(self):
        u_id = self.secili_urun_id()
        if not u_id:
            self.btn_aktife_al.hide()
            self.btn_sil.show()
            return

        urun = self.urun_servisi.urun_getir(u_id)
        if not urun:
            return

        if urun.aktif == 0:
            self.btn_sil.hide()
            is_admin = bool(self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici")
            self.btn_aktife_al.setVisible(is_admin)
        else:
            self.btn_aktife_al.hide()
            self.btn_sil.show()

    def onceki_sayfa(self):
        if self.sayfa_no > 1:
            self.sayfa_no -= 1
            self.listeyi_guncelle()

    def sonraki_sayfa(self):
        self.sayfa_no += 1
        self.listeyi_guncelle()

    def secili_urun_id(self):
        secili = self.tablo.selectedItems()
        if not secili:
            return None
        satir = secili[0].row()
        return int(self.tablo.item(satir, 0).text())

    def yeni_urun_ac(self):
        diyalog = UrunDiyalog(self, self.urun_servisi, aktif_kullanici=self.aktif_kullanici)
        if diyalog.exec() == QDialog.Accepted:
            self.listeyi_guncelle()

    def urun_duzenle_ac(self):
        u_id = self.secili_urun_id()
        if not u_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz ürünü seçiniz.")
            return

        urun = self.urun_servisi.urun_getir(u_id)
        if not urun:
            QMessageBox.critical(self, "Hata", "Ürün bulunamadı.")
            return

        diyalog = UrunDiyalog(self, self.urun_servisi, urun, aktif_kullanici=self.aktif_kullanici)
        if diyalog.exec() == QDialog.Accepted:
            self.listeyi_guncelle()

    def urun_pasife_al(self):
        u_id = self.secili_urun_id()
        if not u_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen pasife almak istediğiniz ürünü seçiniz.")
            return

        urun = self.urun_servisi.urun_getir(u_id)
        if not urun:
            return

        onay = QMessageBox.question(
            self,
            "Pasife Alma Onayı",
            f"'{urun.ad}' ({urun.parca_kodu}) ürününü pasife almak istediğinizden emin misiniz?\n\n"
            "Not: Geçmiş siparişler ve stok kayıtları korunacaktır.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if onay == QMessageBox.Yes:
            k_id = getattr(self.aktif_kullanici, "id", None)
            self.urun_servisi.urun_pasife_al(u_id, kullanici_id=k_id)
            QMessageBox.information(self, "Başarılı", "Ürün pasife alındı.")
            self.listeyi_guncelle()

    def urun_aktife_al(self):
        if not (self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici"):
            QMessageBox.warning(self, "Yetkisiz İşlem", "Yalnızca yönetici pasif ürünü aktife alabilir.")
            return

        u_id = self.secili_urun_id()
        if not u_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen aktife almak istediğiniz ürünü seçiniz.")
            return

        urun = self.urun_servisi.urun_getir(u_id)
        if not urun:
            return

        onay = QMessageBox.question(
            self,
            "Aktife Alma Onayı",
            f"'{urun.ad}' ({urun.parca_kodu}) ürününü tekrar aktif hale getirmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if onay == QMessageBox.Yes:
            k_id = getattr(self.aktif_kullanici, "id", None)
            self.urun_servisi.urun_aktife_al(u_id, kullanici_id=k_id)
            QMessageBox.information(self, "Başarılı", "Ürün başarıyla aktife alındı.")
            self.listeyi_guncelle()

    def stok_duzelt_ac(self):
        u_id = self.secili_urun_id()
        if not u_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen stok miktarını düzeltmek istediğiniz ürünü seçiniz.")
            return

        urun = self.urun_servisi.urun_getir(u_id)
        if not urun:
            return

        yeni_stok, ok = QtWidgets.QInputDialog.getInt(
            self,
            "Stok Düzeltme",
            f"'{urun.ad}' güncel sayım stoğunu giriniz (Mevcut: {urun.stok}):",
            value=urun.stok,
            min=0,
            max=100000
        )
        if ok:
            neden, ok_neden = QtWidgets.QInputDialog.getText(
                self,
                "Düzeltme Gerekçesi",
                "Stok değişim nedenini yazınız (Örn: Sayım fazlası / hasarlı ürün):"
            )
            if ok_neden and neden.strip():
                try:
                    self.stok_servisi.stok_duzeltme_yap(
                        urun_id=u_id,
                        yeni_stok=yeni_stok,
                        aciklama=neden.strip()
                    )
                    QMessageBox.information(self, "Başarılı", f"Stok {yeni_stok} adet olarak güncellendi.")
                    self.listeyi_guncelle()
                except Exception as e:
                    QMessageBox.critical(self, "Hata", str(e))
