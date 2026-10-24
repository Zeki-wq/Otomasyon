"""
Kullanıcı Girişi ve İlk Çalıştırma Sihirbazı Diyaloğu
Kayıtlı kullanıcı yoksa otomatik olarak Yönetici Hesabı Oluşturma Sihirbazı açılır.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame, QFormLayout
)
from app.services.kimlik_servisi import KimlikServisi


class LoginDialog(QDialog):
    """Giriş Ekranı ve İlk Kurulum Sihirbazı."""

    def __init__(self, kimlik_servisi: KimlikServisi, parent=None):
        super().__init__(parent)
        self.kimlik_servisi = kimlik_servisi
        self.giris_yapan_kullanici = None

        self.setWindowTitle("Oto Yedek Parça - Giriş")
        self.setFixedSize(450, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Logo / Başlık
        baslik_layout = QVBoxLayout()
        baslik_layout.setAlignment(QtCore.Qt.AlignCenter)

        logo = QLabel("🚗")
        logo.setStyleSheet("font-size: 36pt;")
        logo.setAlignment(QtCore.Qt.AlignCenter)
        baslik_layout.addWidget(logo)

        self.lbl_baslik = QLabel("OTO YEDEK PARÇA OTOMASYONU")
        self.lbl_baslik.setObjectName("headerTitle")
        self.lbl_baslik.setStyleSheet("font-size: 13pt; font-weight: bold; color: #00a8ff;")
        self.lbl_baslik.setAlignment(QtCore.Qt.AlignCenter)
        baslik_layout.addWidget(self.lbl_baslik)

        self.lbl_alt = QLabel("Lütfen giriş yapınız")
        self.lbl_alt.setStyleSheet("color: #a4b0be; font-size: 9pt;")
        self.lbl_alt.setAlignment(QtCore.Qt.AlignCenter)
        baslik_layout.addWidget(self.lbl_alt)

        layout.addLayout(baslik_layout)

        # Kart İçeriği
        kart = QFrame()
        kart.setObjectName("cardFrame")
        self.form_layout = QFormLayout(kart)
        self.form_layout.setSpacing(10)

        # İlk kurulum mu kontrol et
        self.ilk_kurulum = self.kimlik_servisi.kullanici_sayisi() == 0

        if self.ilk_kurulum:
            self.lbl_baslik.setText("İLK KURULUM SİHİRBAZI")
            self.lbl_alt.setText("Sisteme ilk yönetici hesabını tanımlayınız")

            self.txt_ad_soyad = QLineEdit()
            self.txt_ad_soyad.setPlaceholderText("Örn: Ahmet Yılmaz")
            self.form_layout.addRow("Ad Soyad (*):", self.txt_ad_soyad)

        self.txt_kullanici_adi = QLineEdit()
        self.txt_kullanici_adi.setPlaceholderText("Kullanıcı adınız")
        self.form_layout.addRow("Kullanıcı Adı (*):", self.txt_kullanici_adi)

        self.txt_parola = QLineEdit()
        self.txt_parola.setEchoMode(QLineEdit.Password)
        self.txt_parola.setPlaceholderText("Parolanız")
        self.form_layout.addRow("Parola (*):", self.txt_parola)

        if self.ilk_kurulum:
            self.txt_parola_tekrar = QLineEdit()
            self.txt_parola_tekrar.setEchoMode(QLineEdit.Password)
            self.txt_parola_tekrar.setPlaceholderText("Parola tekrarı")
            self.form_layout.addRow("Parola Tekrar (*):", self.txt_parola_tekrar)

        layout.addWidget(kart)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.btn_giris = QPushButton("Yöneticiyi Oluştur ve Başla" if self.ilk_kurulum else "Giriş Yap")
        self.btn_giris.setObjectName("btnSuccess")
        self.btn_giris.setFixedHeight(38)
        self.btn_giris.clicked.connect(self.islem_yap)
        btn_layout.addWidget(self.btn_giris)

        layout.addLayout(btn_layout)

        # Enter tuşuna basıldığında giriş yap
        self.txt_parola.returnPressed.connect(self.islem_yap)
        if self.ilk_kurulum:
            self.txt_parola_tekrar.returnPressed.connect(self.islem_yap)

    def islem_yap(self):
        k_adi = self.txt_kullanici_adi.text().strip().lower()
        parola = self.txt_parola.text().strip()

        if not k_adi:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen kullanıcı adını giriniz.")
            self.txt_kullanici_adi.setFocus()
            return

        if not parola:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen parolayı giriniz.")
            self.txt_parola.setFocus()
            return

        if self.ilk_kurulum:
            ad_soyad = self.txt_ad_soyad.text().strip()
            tekrar = self.txt_parola_tekrar.text().strip()

            if not ad_soyad:
                QMessageBox.warning(self, "Eksik Bilgi", "Lütfen adınızı ve soyadınızı giriniz.")
                self.txt_ad_soyad.setFocus()
                return

            if parola != tekrar:
                QMessageBox.warning(self, "Uyuşmazlık", "Girdiğiniz parolalar birbiriyle eşleşmiyor!")
                self.txt_parola_tekrar.selectAll()
                self.txt_parola_tekrar.setFocus()
                return

            try:
                yonetici = self.kimlik_servisi.kullanici_olustur(
                    kullanici_adi=k_adi,
                    parola=parola,
                    ad_soyad=ad_soyad,
                    rol="yonetici"
                )
                self.giris_yapan_kullanici = yonetici
                QMessageBox.information(
                    self,
                    "Kurulum Tamamlandı",
                    f"Yönetici hesabı '{k_adi}' başarıyla oluşturuldu!\nSisteme giriş yapılıyor."
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

        else:
            kullanici = self.kimlik_servisi.giris_yap(k_adi, parola)
            if kullanici:
                self.giris_yapan_kullanici = kullanici
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Hatalı Giriş",
                    "Kullanıcı adı veya parola hatalı!\nLütfen kontrol edip tekrar deneyiniz."
                )
                self.txt_parola.clear()
                self.txt_parola.setFocus()
