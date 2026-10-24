"""
Müşteri (Cari Hesap), Tahsilat ve Hesap Ekstresi Ekranı
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QFormLayout, QFrame, QRadioButton, QButtonGroup, QTextEdit
)
from app.domain.models import Musteri
from app.domain.money import kurus_to_tl_str, tl_str_to_kurus
from app.services.musteri_servisi import MusteriServisi


class MusteriDiyalog(QDialog):
    """Yeni müşteri ekleme ve düzenleme penceresi."""

    def __init__(self, parent=None, musteri_servisi: MusteriServisi = None, musteri: Musteri = None):
        super().__init__(parent)
        self.musteri_servisi = musteri_servisi
        self.musteri = musteri
        self.setWindowTitle("Müşteri Düzenle" if musteri else "Yeni Müşteri Ekle")
        self.resize(480, 420)
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

        self.txt_ad = QLineEdit()
        self.txt_ad.setPlaceholderText("Örn: Mehmet Usta / Örnek Oto Servis")
        form.addRow("Ad Soyad / Ünvan (*):", self.txt_ad)

        self.txt_tel = QLineEdit()
        self.txt_tel.setPlaceholderText("Örn: 0532 123 4567")
        form.addRow("Telefon Numarası:", self.txt_tel)

        self.txt_eposta = QLineEdit()
        self.txt_eposta.setPlaceholderText("Örn: info@ornekservis.com")
        form.addRow("E-Posta Adresi:", self.txt_eposta)

        self.txt_vergi = QLineEdit()
        self.txt_vergi.setPlaceholderText("TC Kimlik veya Vergi No")
        form.addRow("Vergi No / TCKN:", self.txt_vergi)

        self.txt_adres = QTextEdit()
        self.txt_adres.setMaximumHeight(70)
        self.txt_adres.setPlaceholderText("Açık adres...")
        form.addRow("Adres:", self.txt_adres)

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
            self.txt_vergi.setText(self.musteri.vergi_no_tc)
            self.txt_adres.setPlainText(self.musteri.adres)

    def kaydet(self):
        ad = self.txt_ad.text().strip()
        if not ad:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen müşteri adı veya firma ünvanını giriniz.")
            self.txt_ad.setFocus()
            return

        try:
            if self.musteri:
                self.musteri.ad_soyad = ad
                self.musteri.telefon = self.txt_tel.text().strip()
                self.musteri.eposta = self.txt_eposta.text().strip()
                self.musteri.vergi_no_tc = self.txt_vergi.text().strip()
                self.musteri.adres = self.txt_adres.toPlainText().strip()
                self.musteri_servisi.musteri_guncelle(self.musteri)
                QMessageBox.information(self, "Başarılı", "Müşteri bilgileri güncellendi.")
            else:
                yeni = Musteri(
                    id=None,
                    ad_soyad=ad,
                    telefon=self.txt_tel.text().strip(),
                    eposta=self.txt_eposta.text().strip(),
                    vergi_no_tc=self.txt_vergi.text().strip(),
                    adres=self.txt_adres.toPlainText().strip()
                )
                self.musteri_servisi.musteri_ekle(yeni)
                QMessageBox.information(self, "Başarılı", f"'{ad}' cari hesabı açıldı.")

            self.accept()
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
        self.resize(420, 360)
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
        self.resize(800, 500)
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

        # Arama Barı
        filtre_kart = QFrame()
        filtre_kart.setObjectName("filterFrame")
        filtre_layout = QHBoxLayout(filtre_kart)
        filtre_layout.setContentsMargins(10, 8, 10, 8)
        filtre_layout.setSpacing(10)

        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("🔍 Müşteri adı, telefon veya vergi/TC no ile ara...")
        self.txt_ara.textChanged.connect(self.listeyi_guncelle)
        filtre_layout.addWidget(self.txt_ara)

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
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tablo.doubleClicked.connect(self.musteri_duzenle_ac)
        ana_layout.addWidget(self.tablo)

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

        alt_bar.addStretch()
        self.lbl_sayi = QLabel("Toplam 0 müşteri")
        alt_bar.addWidget(self.lbl_sayi)

        ana_layout.addLayout(alt_bar)

    def listeyi_guncelle(self):
        terim = self.txt_ara.text().strip()
        musteriler = self.musteri_servisi.musterileri_getir(arama_metni=terim)

        self.tablo.setRowCount(0)
        for r_idx, m in enumerate(musteriler):
            self.tablo.insertRow(r_idx)
            self.tablo.setItem(r_idx, 0, QTableWidgetItem(str(m.id)))
            self.tablo.setItem(r_idx, 1, QTableWidgetItem(m.ad_soyad))
            self.tablo.setItem(r_idx, 2, QTableWidgetItem(m.telefon))
            self.tablo.setItem(r_idx, 3, QTableWidgetItem(m.eposta))
            self.tablo.setItem(r_idx, 4, QTableWidgetItem(m.vergi_no_tc))

            # Bakiye
            bakiye_item = QTableWidgetItem(kurus_to_tl_str(m.bakiye_kurus))
            if m.bakiye_kurus > 0:
                bakiye_item.setForeground(QtGui.QColor("#ff4757"))
                bakiye_item.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
            self.tablo.setItem(r_idx, 5, bakiye_item)

            self.tablo.setItem(r_idx, 6, QTableWidgetItem(m.adres))
            self.tablo.setItem(r_idx, 7, QTableWidgetItem("Aktif" if m.aktif == 1 else "Pasif"))

        self.lbl_sayi.setText(f"Toplam {len(musteriler)} müşteri kayıtlı.")

    def secili_musteri_id(self):
        secili = self.tablo.selectedItems()
        if not secili:
            return None
        satir = secili[0].row()
        return int(self.tablo.item(satir, 0).text())

    def yeni_musteri_ac(self):
        diyalog = MusteriDiyalog(self, self.musteri_servisi)
        if diyalog.exec_() == QDialog.Accepted:
            self.listeyi_guncelle()

    def musteri_duzenle_ac(self):
        m_id = self.secili_musteri_id()
        if not m_id:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz müşteriyi seçiniz.")
            return

        musteri = self.musteri_servisi.musteri_getir(m_id)
        if not musteri:
            return

        diyalog = MusteriDiyalog(self, self.musteri_servisi, musteri)
        if diyalog.exec_() == QDialog.Accepted:
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
        if diyalog.exec_() == QDialog.Accepted:
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
        diyalog.exec_()

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
