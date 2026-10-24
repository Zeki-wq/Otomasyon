"""
Müşteri (Cari Hesap), Tahsilat ve Hesap Ekstresi Ekranı
"""

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import Musteri
from app.domain.money import kurus_to_tl_str, tl_str_to_kurus
from app.domain.validators import (
    ValidationError,
    eposta_dogrula,
    musteri_gecerli_mi,
    tc_maskele,
    telefon_dogrula_ve_normalize,
    telefon_formatla,
    vergi_veya_tc_dogrula,
)
from app.services.musteri_servisi import MusteriServisi
from app.ui.theme import apply_theme


class MusteriDiyalog(QDialog):
    """Yeni müşteri ekleme ve düzenleme penceresi."""

    def __init__(self, parent=None, musteri_servisi: MusteriServisi = None, musteri: Musteri = None, aktif_kullanici=None):
        super().__init__(parent)
        self.musteri_servisi = musteri_servisi
        self.musteri = musteri
        self.aktif_kullanici = aktif_kullanici
        self.setWindowTitle("Müşteri Düzenle" if musteri else "Yeni Müşteri Ekle")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(560, 600)
        self.resize(580, 620)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        baslik = QLabel("👤 CARİ MÜŞTERİ BİLGİLERİ")
        baslik.setObjectName("headerTitle")
        layout.addWidget(baslik)

        kart = QFrame()
        kart.setObjectName("cardFrame")
        form = QFormLayout(kart)
        form.setSpacing(10)
        form.setLabelAlignment(QtCore.Qt.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Ad Soyad / Ünvan ve Hata Etiketi
        lbl_ad = QLabel("Ad Soyad / Ünvan (*):")
        lbl_ad.setMinimumWidth(140)
        ad_kutu = QVBoxLayout()
        self.txt_ad = QLineEdit()
        self.txt_ad.setPlaceholderText("Örn: Mehmet Usta / Örnek Oto Servis")
        self.txt_ad.textChanged.connect(lambda: self._hata_temizle(self.txt_ad, self.lbl_ad_hata))
        ad_kutu.addWidget(self.txt_ad)

        self.lbl_ad_hata = QLabel("")
        self.lbl_ad_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_ad_hata.setWordWrap(True)
        self.lbl_ad_hata.hide()
        ad_kutu.addWidget(self.lbl_ad_hata)
        form.addRow(lbl_ad, ad_kutu)

        # Telefon ve Hata Etiketi
        lbl_tel = QLabel("Telefon Numarası:")
        lbl_tel.setMinimumWidth(140)
        tel_kutu = QVBoxLayout()
        self.txt_tel = QLineEdit()
        self.txt_tel.setPlaceholderText("Örn: 0532 123 45 67")
        regex_tel = QtCore.QRegularExpression(r"^[\d\s\+\-\(\)]{0,17}$")
        self.txt_tel.setValidator(QtGui.QRegularExpressionValidator(regex_tel, self.txt_tel))
        self.txt_tel.setMaxLength(17)
        self.txt_tel.textChanged.connect(lambda: self._hata_temizle(self.txt_tel, self.lbl_tel_hata))
        tel_kutu.addWidget(self.txt_tel)

        self.lbl_tel_hata = QLabel("")
        self.lbl_tel_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_tel_hata.setWordWrap(True)
        self.lbl_tel_hata.hide()
        tel_kutu.addWidget(self.lbl_tel_hata)
        form.addRow(lbl_tel, tel_kutu)

        # E-Posta ve Hata Etiketi
        lbl_eposta = QLabel("E-Posta Adresi:")
        lbl_eposta.setMinimumWidth(140)
        eposta_kutu = QVBoxLayout()
        self.txt_eposta = QLineEdit()
        self.txt_eposta.setPlaceholderText("Örn: info@ornekservis.com")
        self.txt_eposta.textChanged.connect(lambda: self._hata_temizle(self.txt_eposta, self.lbl_eposta_hata))
        eposta_kutu.addWidget(self.txt_eposta)

        self.lbl_eposta_hata = QLabel("")
        self.lbl_eposta_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_eposta_hata.setWordWrap(True)
        self.lbl_eposta_hata.hide()
        eposta_kutu.addWidget(self.lbl_eposta_hata)
        form.addRow(lbl_eposta, eposta_kutu)

        # TC / Vergi No ve Hata Etiketi
        lbl_vergi = QLabel("Vergi No / TCKN:")
        lbl_vergi.setMinimumWidth(140)
        vergi_kutu = QVBoxLayout()
        self.txt_vergi = QLineEdit()
        self.txt_vergi.setPlaceholderText("TC Kimlik (11 hane) veya Vergi No (10 hane)")
        regex_tc = QtCore.QRegularExpression(r"^\d{0,11}$")
        self.txt_vergi.setValidator(QtGui.QRegularExpressionValidator(regex_tc, self.txt_vergi))
        self.txt_vergi.setMaxLength(11)
        self.txt_vergi.textChanged.connect(self._vergi_degisti)
        vergi_kutu.addWidget(self.txt_vergi)

        self.lbl_vergi_hata = QLabel("")
        self.lbl_vergi_hata.setStyleSheet("font-size: 8pt; color: #ff4757;")
        self.lbl_vergi_hata.setWordWrap(True)
        self.lbl_vergi_hata.hide()
        vergi_kutu.addWidget(self.lbl_vergi_hata)
        form.addRow(lbl_vergi, vergi_kutu)

        lbl_adres = QLabel("Adres:")
        lbl_adres.setMinimumWidth(140)
        self.txt_adres = QTextEdit()
        self.txt_adres.setMinimumHeight(65)
        self.txt_adres.setPlaceholderText("Açık adres...")
        form.addRow(lbl_adres, self.txt_adres)

        # Hesap Durumu (Aktif / Pasif)
        lbl_durum = QLabel("Hesap Durumu:")
        lbl_durum.setMinimumWidth(140)
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItem("✅ Aktif", 1)
        self.cmb_durum.addItem("⛔ Pasif", 0)
        form.addRow(lbl_durum, self.cmb_durum)

        layout.addWidget(kart)

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

        if self.musteri:
            self.txt_ad.setText(self.musteri.ad_soyad)
            self.txt_tel.setText(self.musteri.telefon)
            self.txt_eposta.setText(self.musteri.eposta)

            # KVKK: Tam TC yalnızca yöneticiye gösterilir
            is_admin = bool(self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici")
            if is_admin or not self.musteri.vergi_no_tc:
                self.txt_vergi.setText(self.musteri.vergi_no_tc)
            else:
                self.txt_vergi.setText(tc_maskele(self.musteri.vergi_no_tc))
                self.txt_vergi.setReadOnly(True)
                self.txt_vergi.setToolTip("KVKK gereği TC kimlik numarasını yalnızca yönetici düzenleyebilir.")

            self.txt_adres.setPlainText(self.musteri.adres)

            durum_idx = self.cmb_durum.findData(self.musteri.aktif if self.musteri.aktif is not None else 1)
            if durum_idx >= 0:
                self.cmb_durum.setCurrentIndex(durum_idx)

            # Mevcut geçersiz veriler varsa formu açınca her hatalı alanı kırmızı vurgula ve mesajını göster
            ad_val = str(self.musteri.ad_soyad or "").strip()
            if len(ad_val) < 2:
                self._hata_ayarla(self.txt_ad, self.lbl_ad_hata, "Müşteri adı veya firma ünvanı en az 2 karakter olmalıdır!")

            tel_val = str(self.musteri.telefon or "").strip()
            if tel_val:
                try:
                    telefon_dogrula_ve_normalize(tel_val)
                except ValidationError as e:
                    self._hata_ayarla(self.txt_tel, self.lbl_tel_hata, str(e))

            eposta_val = str(self.musteri.eposta or "").strip()
            if eposta_val and not eposta_dogrula(eposta_val):
                self._hata_ayarla(self.txt_eposta, self.lbl_eposta_hata, "Geçersiz e-posta formatı (örn: info@firma.com)!")

            v_val = str(self.musteri.vergi_no_tc or "").strip()
            if v_val:
                gecerli_v, aciklama_v = vergi_veya_tc_dogrula(v_val)
                if not gecerli_v:
                    self._hata_ayarla(self.txt_vergi, self.lbl_vergi_hata, aciklama_v)

    def _hata_ayarla(self, widget: QWidget, label: QLabel, mesaj: str):
        widget.setStyleSheet("border: 1.5px solid #ff4757; background-color: #2d1f24;")
        label.setText(f"⚠️ {mesaj}")
        label.setStyleSheet("font-size: 8pt; color: #ff4757;")
        label.show()

    def _hata_temizle(self, widget: QWidget, label: QLabel):
        widget.setStyleSheet("")
        label.setText("")
        label.hide()

    def _vergi_degisti(self, metin: str):
        v = metin.strip()
        if not v:
            self._hata_temizle(self.txt_vergi, self.lbl_vergi_hata)
            return

        gecerli, aciklama = vergi_veya_tc_dogrula(v)
        if not gecerli:
            self._hata_ayarla(self.txt_vergi, self.lbl_vergi_hata, aciklama)
        else:
            self.txt_vergi.setStyleSheet("")
            if aciklama == "tc":
                self.lbl_vergi_hata.setText("✅ Geçerli TC Kimlik Numarası")
                self.lbl_vergi_hata.setStyleSheet("font-size: 8pt; color: #2ecc71;")
                self.lbl_vergi_hata.show()
            elif aciklama == "vergi":
                self.lbl_vergi_hata.setText("ℹ️ Geçerli 10 Haneli Vergi Numarası")
                self.lbl_vergi_hata.setStyleSheet("font-size: 8pt; color: #3498db;")
                self.lbl_vergi_hata.show()

    def kaydet(self):
        ilk_hatali = None

        # 1. Ad Soyad Kontrolü
        ad = self.txt_ad.text().strip()
        if not ad or len(ad) < 2:
            self._hata_ayarla(self.txt_ad, self.lbl_ad_hata, "Müşteri adı veya firma ünvanı en az 2 karakter olmalıdır!")
            if not ilk_hatali:
                ilk_hatali = self.txt_ad
        else:
            self._hata_temizle(self.txt_ad, self.lbl_ad_hata)

        # 2. Telefon Kontrolü
        tel = self.txt_tel.text().strip()
        if tel:
            try:
                telefon_dogrula_ve_normalize(tel)
                self._hata_temizle(self.txt_tel, self.lbl_tel_hata)
            except ValidationError as e:
                self._hata_ayarla(self.txt_tel, self.lbl_tel_hata, str(e))
                if not ilk_hatali:
                    ilk_hatali = self.txt_tel
        else:
            self._hata_temizle(self.txt_tel, self.lbl_tel_hata)

        # 3. E-Posta Kontrolü
        eposta = self.txt_eposta.text().strip()
        if eposta:
            if not eposta_dogrula(eposta):
                self._hata_ayarla(self.txt_eposta, self.lbl_eposta_hata, "Geçersiz e-posta formatı (örn: info@firma.com)!")
                if not ilk_hatali:
                    ilk_hatali = self.txt_eposta
            else:
                self._hata_temizle(self.txt_eposta, self.lbl_eposta_hata)
        else:
            self._hata_temizle(self.txt_eposta, self.lbl_eposta_hata)

        # 4. Vergi / TC No Kontrolü
        vergi_tc = self.txt_vergi.text().strip()
        if self.musteri and vergi_tc == tc_maskele(self.musteri.vergi_no_tc):
            vergi_tc = self.musteri.vergi_no_tc

        if vergi_tc:
            gecerli, aciklama = vergi_veya_tc_dogrula(vergi_tc)
            if not gecerli:
                self._hata_ayarla(self.txt_vergi, self.lbl_vergi_hata, aciklama)
                if not ilk_hatali:
                    ilk_hatali = self.txt_vergi
            else:
                self._hata_temizle(self.txt_vergi, self.lbl_vergi_hata)
        else:
            self._hata_temizle(self.txt_vergi, self.lbl_vergi_hata)

        # Hata varsa kaydı durdur ve ilk hatalı alana odaklan
        if ilk_hatali:
            ilk_hatali.setFocus()
            return

        yeni_durum = self.cmb_durum.currentData()
        if yeni_durum is None:
            yeni_durum = 1

        try:
            if self.musteri:
                self.musteri.ad_soyad = ad
                self.musteri.telefon = tel
                self.musteri.eposta = eposta
                self.musteri.vergi_no_tc = vergi_tc
                self.musteri.adres = self.txt_adres.toPlainText().strip()
                self.musteri.aktif = yeni_durum
                self.musteri_servisi.musteri_guncelle(self.musteri)
                QMessageBox.information(self, "Başarılı", "Müşteri bilgileri güncellendi.")
            else:
                yeni = Musteri(
                    id=None,
                    ad_soyad=ad,
                    telefon=tel,
                    eposta=eposta,
                    vergi_no_tc=vergi_tc,
                    adres=self.txt_adres.toPlainText().strip(),
                    aktif=yeni_durum
                )
                self.musteri_servisi.musteri_ekle(yeni)
                QMessageBox.information(self, "Başarılı", f"'{ad}' cari hesabı açıldı.")

            self.accept()
        except ValidationError as ve:
            QMessageBox.warning(self, "Doğrulama Hatası", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class TahsilatDiyalog(QDialog):
    """Müşteriden cari tahsilat alma penceresi."""

    def __init__(self, musteri: Musteri, musteri_servisi: MusteriServisi, aktif_kullanici=None, parent=None):
        super().__init__(parent)
        self.musteri = musteri
        self.musteri_servisi = musteri_servisi
        self.aktif_kullanici = aktif_kullanici
        self.setWindowTitle(f"Tahsilat Girişi - {musteri.ad_soyad}")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(420, 380)
        self.resize(440, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        baslik = QLabel("💵 TAHSİLAT GİRİŞİ")
        baslik.setObjectName("headerTitle")
        layout.addWidget(baslik)

        kart = QFrame()
        kart.setObjectName("cardFrame")
        form = QFormLayout(kart)
        form.setSpacing(10)

        form.addRow("Müşteri:", QLabel(f"<b>{self.musteri.ad_soyad}</b>"))
        form.addRow("Güncel Borç:", QLabel(f"<b style='color:#ff4757;'>{kurus_to_tl_str(self.musteri.bakiye_kurus)}</b>"))

        self.txt_tutar = QLineEdit()
        self.txt_tutar.setPlaceholderText("0,00 ₺")
        form.addRow("Tahsil Edilen Tutar (*):", self.txt_tutar)

        # Ödeme tipi
        odeme_layout = QHBoxLayout()
        self.rb_nakit = QRadioButton("Nakit")
        self.rb_nakit.setChecked(True)
        self.rb_kart = QRadioButton("Kredi Kartı")
        self.grp_odeme = QButtonGroup(self)
        self.grp_odeme.addButton(self.rb_nakit, 1)
        self.grp_odeme.addButton(self.rb_kart, 2)
        odeme_layout.addWidget(self.rb_nakit)
        odeme_layout.addWidget(self.rb_kart)
        form.addRow("Ödeme Yolu:", odeme_layout)

        self.txt_aciklama = QLineEdit()
        self.txt_aciklama.setPlaceholderText("Örn: Makbuz No 1234 / Havale")
        form.addRow("Açıklama / Makbuz:", self.txt_aciklama)

        layout.addWidget(kart)

        btn_layout = QHBoxLayout()
        self.btn_onayla = QPushButton("✅ Tahsilatı Kaydet")
        self.btn_onayla.setObjectName("btnSuccess")
        self.btn_onayla.clicked.connect(self.kaydet)

        self.btn_iptal = QPushButton("İptal")
        self.btn_iptal.setObjectName("btnSecondary")
        self.btn_iptal.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_iptal)
        btn_layout.addWidget(self.btn_onayla)
        layout.addLayout(btn_layout)

    def kaydet(self):
        tutar_kurus = tl_str_to_kurus(self.txt_tutar.text())
        if tutar_kurus <= 0:
            QMessageBox.warning(self, "Geçersiz Tutar", "Lütfen 0'dan büyük geçerli bir tahsilat tutarı giriniz.")
            self.txt_tutar.setFocus()
            return

        odeme_tipi = "nakit" if self.rb_nakit.isChecked() else "kart"
        aciklama = self.txt_aciklama.text().strip()
        kullanici_id = self.aktif_kullanici.id if self.aktif_kullanici else None

        try:
            self.musteri_servisi.tahsilat_yap(
                musteri_id=self.musteri.id,
                tutar_kurus=tutar_kurus,
                odeme_tipi=odeme_tipi,
                aciklama=aciklama,
                kullanici_id=kullanici_id
            )
            QMessageBox.information(
                self,
                "Tahsilat Kaydedildi",
                f"{kurus_to_tl_str(tutar_kurus)} tahsilat başarıyla kaydedildi ve cari borçtan düşüldü."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class EkstreDiyalog(QDialog):
    """Müşteri hesap ekstresi penceresi."""

    def __init__(self, musteri: Musteri, musteri_servisi: MusteriServisi, parent=None):
        super().__init__(parent)
        self.musteri = musteri
        self.musteri_servisi = musteri_servisi
        self.setWindowTitle(f"Hesap Ekstresi - {musteri.ad_soyad}")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(780, 480)
        self.resize(820, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Başlık ve Müşteri Özeti
        kart = QFrame()
        kart.setObjectName("cardFrame")
        k_layout = QHBoxLayout(kart)
        k_layout.addWidget(QLabel(f"<b>Müşteri:</b> {self.musteri.ad_soyad}"))
        k_layout.addWidget(QLabel(f"<b>Telefon:</b> {self.musteri.telefon or 'Yok'}"))
        k_layout.addStretch()
        k_layout.addWidget(QLabel(f"Güncel Bakiye: <b style='color:#ff4757; font-size:12pt;'>{kurus_to_tl_str(self.musteri.bakiye_kurus)}</b>"))
        layout.addWidget(kart)

        # Tablo
        tablo = QTableWidget()
        tablo.setColumnCount(6)
        tablo.setHorizontalHeaderLabels([
            "Tarih", "Belge No", "İşlem Türü", "Borç (+)", "Alacak (-)", "Bakiye"
        ])
        tablo.setAlternatingRowColors(True)
        tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tablo.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        islemler = self.musteri_servisi.musteri_ekstresi_getir(self.musteri.id)
        for idx, row in enumerate(islemler):
            tablo.insertRow(idx)
            tablo.setItem(idx, 0, QTableWidgetItem(str(row["tarih"])))
            tablo.setItem(idx, 1, QTableWidgetItem(str(row["belge_no"])))
            tablo.setItem(idx, 2, QTableWidgetItem(str(row["islem"])))

            borc_str = kurus_to_tl_str(row["borc_kurus"]) if row["borc_kurus"] > 0 else "-"
            alacak_str = kurus_to_tl_str(row["alacak_kurus"]) if row["alacak_kurus"] > 0 else "-"

            borc_item = QTableWidgetItem(borc_str)
            if row["borc_kurus"] > 0:
                borc_item.setForeground(QtGui.QColor("#ff4757"))
            tablo.setItem(idx, 3, borc_item)

            alacak_item = QTableWidgetItem(alacak_str)
            if row["alacak_kurus"] > 0:
                alacak_item.setForeground(QtGui.QColor("#2ecc71"))
            tablo.setItem(idx, 4, alacak_item)

            bakiye_item = QTableWidgetItem(kurus_to_tl_str(row["yuruyen_bakiye_kurus"]))
            tablo.setItem(idx, 5, bakiye_item)

        layout.addWidget(tablo)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setObjectName("btnSecondary")
        btn_kapat.clicked.connect(self.accept)
        layout.addWidget(btn_kapat, alignment=QtCore.Qt.AlignRight)


class MusterilerPage(QWidget):
    """Müşteri ve Cari Hesap Yönetimi Ana Ekranı."""

    def __init__(self, musteri_servisi: MusteriServisi, aktif_kullanici=None, parent=None):
        super().__init__(parent)
        self.musteri_servisi = musteri_servisi
        self.aktif_kullanici = aktif_kullanici

        self.init_ui()
        self.listeyi_guncelle()

    def init_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(12)

        # Üst Bar
        ust_bar = QHBoxLayout()
        baslik = QLabel("👥 CARİ HESAPLAR & MÜŞTERİLER")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        self.btn_yeni = QPushButton("➕ Yeni Müşteri Ekle")
        self.btn_yeni.setObjectName("btnSuccess")
        self.btn_yeni.clicked.connect(self.yeni_musteri_ac)
        ust_bar.addWidget(self.btn_yeni)

        ana_layout.addLayout(ust_bar)

        # Arama ve Filtre Barı
        filtre_kart = QFrame()
        filtre_kart.setObjectName("filterFrame")
        filtre_layout = QHBoxLayout(filtre_kart)
        filtre_layout.setContentsMargins(10, 8, 10, 8)
        filtre_layout.setSpacing(10)

        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("🔍 Müşteri adı, telefon veya vergi/TC no ile ara...")
        self.txt_ara.textChanged.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.txt_ara, stretch=3)

        self.cmb_filtre_durum = QComboBox()
        self.cmb_filtre_durum.addItem("Tüm Müşteriler (Aktif + Pasif)", "tumu")
        self.cmb_filtre_durum.addItem("✅ Yalnızca Aktifler", "aktif")
        self.cmb_filtre_durum.addItem("⛔ Yalnızca Pasifler", "pasif")
        self.cmb_filtre_durum.addItem("Yalnızca Geçerli Kayıtlar", "gecerli")
        self.cmb_filtre_durum.addItem("⚠️ Yalnızca Hatalı Kayıtlar", "hatali")
        self.cmb_filtre_durum.currentIndexChanged.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.cmb_filtre_durum, stretch=1)

        ana_layout.addWidget(filtre_kart)

        # Tablo
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(8)
        self.tablo.setHorizontalHeaderLabels([
            "ID", "Ad Soyad / Firma Ünvanı", "Telefon", "E-Posta",
            "Vergi / TC No", "Cari Borç (₺)", "Adres", "Durum"
        ])
        self.tablo.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tablo.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tablo.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tablo.horizontalHeader().setMinimumSectionSize(65)
        m_widths = [50, 210, 120, 130, 150, 105, 170, 85]
        for col, w in enumerate(m_widths):
            self.tablo.setColumnWidth(col, w)
        self.tablo.doubleClicked.connect(self.musteri_duzenle_ac)
        self.tablo.itemSelectionChanged.connect(self.satir_secildi)
        ana_layout.addWidget(self.tablo, stretch=1)

        # Alt Butonlar
        alt_bar = QHBoxLayout()

        self.btn_duzenle = QPushButton("✏️ Düzenle")
        self.btn_duzenle.clicked.connect(self.musteri_duzenle_ac)
        alt_bar.addWidget(self.btn_duzenle)

        self.btn_tahsilat = QPushButton("💵 Tahsilat Girişi")
        self.btn_tahsilat.setObjectName("btnSuccess")
        self.btn_tahsilat.clicked.connect(self.tahsilat_ac)
        alt_bar.addWidget(self.btn_tahsilat)

        self.btn_ekstre = QPushButton("📜 Hesap Ekstresi")
        self.btn_ekstre.setObjectName("btnSecondary")
        self.btn_ekstre.clicked.connect(self.ekstre_ac)
        alt_bar.addWidget(self.btn_ekstre)

        self.btn_sil = QPushButton("🗑️ Pasife Al")
        self.btn_sil.setObjectName("btnDanger")
        self.btn_sil.clicked.connect(self.musteri_pasife_al)
        alt_bar.addWidget(self.btn_sil)

        self.btn_aktife_al = QPushButton("♻️ Aktife Al")
        self.btn_aktife_al.setObjectName("btnSuccess")
        self.btn_aktife_al.clicked.connect(self.musteri_aktife_al)
        self.btn_aktife_al.hide()
        alt_bar.addWidget(self.btn_aktife_al)

        alt_bar.addStretch()
        self.lbl_sayi = QLabel("Toplam 0 müşteri")
        alt_bar.addWidget(self.lbl_sayi)

        ana_layout.addLayout(alt_bar)

    def satir_secildi(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            self.btn_aktife_al.hide()
            self.btn_sil.show()
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        if musteri.aktif == 0:
            self.btn_sil.hide()
            self.btn_aktife_al.show()
        else:
            self.btn_aktife_al.hide()
            self.btn_sil.show()

    def listeyi_guncelle(self):
        terim = self.txt_ara.text().strip()
        musteriler = self.musteri_servisi.musterileri_getir(arama_metni=terim, sadece_aktif=False)
        filtre_durum = self.cmb_filtre_durum.currentData() if hasattr(self, "cmb_filtre_durum") else "tumu"

        self.tablo.setRowCount(0)
        for m in musteriler:
            gecerli, hatalar = musteri_gecerli_mi(m)

            # Filtreye göre ele
            if filtre_durum == "aktif" and m.aktif != 1:
                continue
            if filtre_durum == "pasif" and m.aktif != 0:
                continue
            if filtre_durum == "hatali" and gecerli:
                continue
            if filtre_durum == "gecerli" and not gecerli:
                continue

            r_idx = self.tablo.rowCount()
            self.tablo.insertRow(r_idx)
            item_id = QTableWidgetItem(str(m.id))
            item_ad = QTableWidgetItem(m.ad_soyad)
            item_tel = QTableWidgetItem(telefon_formatla(m.telefon))
            item_eposta = QTableWidgetItem(m.eposta)

            # KVKK Maskeleme ve Geçersiz TC Rozeti
            tc_str = m.vergi_no_tc or ""
            if tc_str:
                gecerli_tc, _ = vergi_veya_tc_dogrula(tc_str)
                if not gecerli_tc:
                    item_tc = QTableWidgetItem(f"{tc_maskele(tc_str)} ⚠️ Geçersiz TC")
                    item_tc.setForeground(QtGui.QColor("#ff4757"))
                    item_tc.setToolTip("TCKN veya Vergi No resmi kontrolden geçemedi!")
                else:
                    item_tc = QTableWidgetItem(tc_maskele(tc_str))
            else:
                item_tc = QTableWidgetItem("-")

            # Bakiye
            item_bakiye = QTableWidgetItem(kurus_to_tl_str(m.bakiye_kurus))
            if m.bakiye_kurus > 0:
                item_bakiye.setForeground(QtGui.QColor("#ff4757"))
                item_bakiye.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))

            item_adres = QTableWidgetItem(m.adres)

            # Durum / Hatalı Bilgi Rozeti
            if not gecerli:
                durum_item = QTableWidgetItem("⚠️ Hatalı Bilgi")
                durum_item.setForeground(QtGui.QColor("#ff4757"))
                durum_item.setToolTip("Kayıtta hatalı alanlar var:\n" + "\n".join(hatalar) + "\nLütfen düzenleyerek düzeltiniz.")
            else:
                durum_item = QTableWidgetItem("✅ Aktif" if m.aktif == 1 else "⛔ Pasif")
                durum_item.setForeground(QtGui.QColor("#2ecc71" if m.aktif == 1 else "#718093"))

            row_items = [item_id, item_ad, item_tel, item_eposta, item_tc, item_bakiye, item_adres, durum_item]
            if m.aktif == 0:
                for it in row_items:
                    if it != durum_item:
                        it.setForeground(QtGui.QColor("#718093"))

            for c_idx, it in enumerate(row_items):
                self.tablo.setItem(r_idx, c_idx, it)

        if self.tablo.rowCount() == 0:
            self.lbl_sayi.setText("🔍 Aradığınız kriterlere uygun müşteri bulunamadı.")
            self.lbl_sayi.setStyleSheet("color: #ff9f43; font-weight: bold;")
        else:
            self.lbl_sayi.setText(f"Toplam {self.tablo.rowCount()} müşteri listeleniyor.")
            self.lbl_sayi.setStyleSheet("color: #dcdde1;")
        self.satir_secildi()

    def secili_musteri_id(self):
        secili = self.tablo.selectedItems()
        if not secili:
            return None
        satir = secili[0].row()
        return int(self.tablo.item(satir, 0).text())

    def yeni_musteri_ac(self):
        diyalog = MusteriDiyalog(self, self.musteri_servisi, aktif_kullanici=self.aktif_kullanici)
        apply_theme(diyalog)
        if diyalog.exec() == QDialog.Accepted:
            self.listeyi_guncelle()

    def musteri_duzenle_ac(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz müşteriyi seçiniz.")
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        diyalog = MusteriDiyalog(self, self.musteri_servisi, musteri, aktif_kullanici=self.aktif_kullanici)
        apply_theme(diyalog)
        if diyalog.exec() == QDialog.Accepted:
            self.listeyi_guncelle()

    def tahsilat_ac(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen tahsilat yapmak istediğiniz müşteriyi seçiniz.")
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        diyalog = TahsilatDiyalog(musteri, self.musteri_servisi, self.aktif_kullanici, self)
        apply_theme(diyalog)
        if diyalog.exec() == QDialog.Accepted:
            self.listeyi_guncelle()

    def ekstre_ac(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen ekstresini görmek istediğiniz müşteriyi seçiniz.")
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        diyalog = EkstreDiyalog(musteri, self.musteri_servisi, self)
        apply_theme(diyalog)
        diyalog.exec()

    def musteri_pasife_al(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen pasife almak istediğiniz müşteriyi seçiniz.")
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        if musteri.bakiye_kurus > 0:
            QMessageBox.warning(
                self,
                "Açık Bakiye Var",
                f"Bu müşterinin {kurus_to_tl_str(musteri.bakiye_kurus)} açık borcu bulunmaktadır!\n"
                "Bakiyesi kapanmadan müşteri pasife alınamaz."
            )
            return

        onay = QMessageBox.question(
            self,
            "Pasife Alma Onayı",
            f"'{musteri.ad_soyad}' cari hesabını pasife almak istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if onay == QMessageBox.Yes:
            self.musteri_servisi.musteri_pasife_al(m_id)
            QMessageBox.information(self, "Başarılı", "Müşteri cari hesabı pasife alındı.")
            self.listeyi_guncelle()

    def musteri_aktife_al(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen aktife almak istediğiniz müşteriyi seçiniz.")
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        onay = QMessageBox.question(
            self,
            "Aktife Alma Onayı",
            f"'{musteri.ad_soyad}' cari hesabını tekrar aktif hale getirmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if onay == QMessageBox.Yes:
            self.musteri_servisi.musteri_aktife_al(m_id)
            QMessageBox.information(self, "Başarılı", "Müşteri cari hesabı tekrar aktife alındı.")
            self.listeyi_guncelle()
