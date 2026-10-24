"""
Kullanıcı Girişi ve İlk Çalıştırma Sihirbazı Diyaloğu
Kayıtlı kullanıcı yoksa otomatik olarak Yönetici Hesabı Oluşturma Sihirbazı açılır.
"""

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.db.connection import get_db_connection
from app.services.kimlik_servisi import KimlikServisi


class LoginDialog(QDialog):
    """Giriş Ekranı ve İlk Kurulum Sihirbazı."""

    def __init__(self, kimlik_servisi: KimlikServisi, parent=None):
        super().__init__(parent)
        self.kimlik_servisi = kimlik_servisi
        self.giris_yapan_kullanici = None

        self.setWindowTitle("Oto Yedek Parça - Giriş")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.init_ui()
        if self.ilk_kurulum:
            self.setMinimumSize(480, 650)
            self.resize(500, 700)
        else:
            self.setMinimumSize(440, 420)
            self.resize(440, 430)


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
            self.lbl_alt.setText("Dükkan bilgilerinizi ve ilk yönetici hesabını tanımlayınız")

            self.txt_ad_soyad = QLineEdit()
            self.txt_ad_soyad.setPlaceholderText("Örn: Ahmet Yılmaz")
            self.form_layout.addRow("Yönetici Ad Soyad (*):", self.txt_ad_soyad)

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

            self.txt_dukkan_adi = QLineEdit()
            self.txt_dukkan_adi.setPlaceholderText("Örn: Yıldız Oto Yedek Parça")
            self.txt_dukkan_adi.setText("Oto Yedek Parça")
            self.form_layout.addRow("Dükkan Ünvanı (*):", self.txt_dukkan_adi)

            self.txt_telefon = QLineEdit()
            self.txt_telefon.setPlaceholderText("Örn: 0532 123 4567")
            self.form_layout.addRow("İletişim Telefonu:", self.txt_telefon)

            self.txt_adres = QLineEdit()
            self.txt_adres.setPlaceholderText("Örn: Sanayi Sitesi 4. Blok No:12")
            self.form_layout.addRow("Dükkan Adresi:", self.txt_adres)

            self.spn_kdv = QSpinBox()
            self.spn_kdv.setRange(0, 100)
            self.spn_kdv.setValue(20)
            self.spn_kdv.setSuffix(" %")
            self.spn_kdv.setMinimumHeight(38)
            self.form_layout.addRow("Varsayılan KDV Oranı:", self.spn_kdv)

            self.btn_legacy_sec = QPushButton("📁 Eski Dosyadan İçe Aktar (İsteğe Bağlı)")
            self.btn_legacy_sec.setObjectName("btnSecondary")
            self.btn_legacy_sec.setMinimumHeight(38)
            self.btn_legacy_sec.clicked.connect(self.eski_dosyadan_ice_aktar)
            self.form_layout.addRow("Eski Veri:", self.btn_legacy_sec)

        layout.addWidget(kart)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.btn_giris = QPushButton("Yöneticiyi Oluştur ve Başla" if self.ilk_kurulum else "Giriş Yap")
        self.btn_giris.setObjectName("btnSuccess")
        self.btn_giris.setMinimumHeight(38)
        self.btn_giris.clicked.connect(self.islem_yap)
        btn_layout.addWidget(self.btn_giris)

        layout.addLayout(btn_layout)

        # Enter tuşuna basıldığında giriş yap
        self.txt_parola.returnPressed.connect(self.islem_yap)
        if self.ilk_kurulum:
            self.txt_parola_tekrar.returnPressed.connect(self.islem_yap)


    def eski_dosyadan_ice_aktar(self):
        secilen, _ = QFileDialog.getOpenFileName(
            self,
            "Eski Veritabanı Seç (urunler12.db)",
            "",
            "SQLite Veritabanı (*.db *.sqlite);;Tüm Dosyalar (*.*)"
        )
        if secilen:
            try:
                from app.db.legacy_import import import_legacy_database
                sonuc = import_legacy_database(secilen, self.kimlik_servisi.db_path)
                QMessageBox.information(
                    self,
                    "İçe Aktarma Tamamlandı",
                    f"Eski veritabanı başarıyla içe aktarıldı!\n\n"
                    f"Aktarılan Ürün Sayısı: {sonuc.get('urun_sayisi', 0)}\n"
                    f"Aktarılan Sipariş Sayısı: {sonuc.get('siparis_sayisi', 0)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "İçe Aktarma Hatası", f"Dosya aktarılırken hata oluştu:\n{e}")

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

                # Dükkan ve sistem ayarlarını kaydet
                try:
                    conn = get_db_connection(self.kimlik_servisi.db_path)
                    cur = conn.cursor()
                    with conn:
                        dukkan = self.txt_dukkan_adi.text().strip() if hasattr(self, "txt_dukkan_adi") else "Oto Yedek Parça"
                        tel = self.txt_telefon.text().strip() if hasattr(self, "txt_telefon") else ""
                        adr = self.txt_adres.text().strip() if hasattr(self, "txt_adres") else ""
                        kdv_val = str(self.spn_kdv.value()) if hasattr(self, "spn_kdv") else "20"

                        cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('dukkan_adi', ?)", (dukkan or "Oto Yedek Parça",))
                        cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('telefon', ?)", (tel,))
                        cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('adres', ?)", (adr,))
                        cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('varsayilan_kdv', ?)", (kdv_val,))
                    conn.close()
                except Exception as ae:
                    pass

                QMessageBox.information(
                    self,
                    "Kurulum Tamamlandı",
                    f"Yönetici hesabı '{k_adi}' ve dükkan bilgileri başarıyla kaydedildi!\nSisteme giriş yapılıyor."
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))


        else:
            try:
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
            except ValueError as ve:
                QMessageBox.critical(self, "Hesap Kilitlendi", str(ve))
                self.txt_parola.clear()
                self.txt_parola.setFocus()
