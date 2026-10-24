"""
Sistem Ayarları, Yedekleme, Veritabanı Sağlığı ve Kullanıcı Yönetim Ekranı
"""

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.db.connection import check_db_health, get_db_connection
from app.services.kimlik_servisi import KimlikServisi
from app.services.yedek_servisi import YedekServisi


class AyarlarPage(QWidget):
    """Genel Ayarlar, Yedekleme & Geri Yükleme ve Kullanıcı Yönetimi."""

    def __init__(
        self,
        yedek_servisi: YedekServisi,
        kimlik_servisi: KimlikServisi,
        db_path=None,
        aktif_kullanici=None,
        parent=None
    ):
        super().__init__(parent)
        self.yedek_servisi = yedek_servisi
        self.kimlik_servisi = kimlik_servisi
        self.db_path = db_path
        self.aktif_kullanici = aktif_kullanici

        self.init_ui()
        self.ayarlari_yukle()
        self.yedekleri_yukle()
        if self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici":
            self.kullanicilari_yukle()

    def init_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(12)

        # Başlık
        ust_bar = QHBoxLayout()
        baslik = QLabel("⚙️ SİSTEM AYARLARI VE YEDEKLEME")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        self.btn_saglik = QPushButton("🩺 Veritabanı Sağlık Kontrolü")
        self.btn_saglik.setObjectName("btnSecondary")
        self.btn_saglik.clicked.connect(self.saglik_kontrolu_yap)
        ust_bar.addWidget(self.btn_saglik)

        ana_layout.addLayout(ust_bar)

        # Sekmeli Alan
        self.tabs = QTabWidget()

        # 1. SEKME: Dükkan ve Fiş Bilgileri
        tab_dukkan = QWidget()
        d_layout = QVBoxLayout(tab_dukkan)
        d_layout.setContentsMargins(10, 15, 10, 10)

        d_kart = QFrame()
        d_kart.setObjectName("cardFrame")
        d_form = QFormLayout(d_kart)
        d_form.setSpacing(12)

        self.txt_dukkan_adi = QLineEdit()
        d_form.addRow("Dükkan Ünvanı (*):", self.txt_dukkan_adi)

        self.txt_telefon = QLineEdit()
        d_form.addRow("İletişim Telefonu:", self.txt_telefon)

        self.txt_adres = QLineEdit()
        d_form.addRow("Dükkan Adresi:", self.txt_adres)

        self.spn_kdv = QSpinBox()
        self.spn_kdv.setRange(0, 100)
        self.spn_kdv.setValue(20)
        self.spn_kdv.setSuffix(" %")
        d_form.addRow("Varsayılan KDV Oranı:", self.spn_kdv)

        self.txt_fis_notu = QLineEdit()
        d_form.addRow("Satış Fişi Alt Notu:", self.txt_fis_notu)

        d_layout.addWidget(d_kart)

        btn_d_kaydet = QPushButton("💾 Dükkan Ayarlarını Kaydet")
        btn_d_kaydet.setObjectName("btnSuccess")
        btn_d_kaydet.clicked.connect(self.ayarlari_kaydet)
        d_layout.addWidget(btn_d_kaydet, alignment=QtCore.Qt.AlignLeft)
        d_layout.addStretch()

        self.tabs.addTab(tab_dukkan, "🏪 Dükkan & Fiş Bilgileri")

        # 2. SEKME: Veri Yedekleme ve Geri Yükleme
        tab_yedek = QWidget()
        y_layout = QVBoxLayout(tab_yedek)
        y_layout.setContentsMargins(10, 15, 10, 10)

        y_islem_bar = QHBoxLayout()
        self.btn_yedek_al = QPushButton("💾 Şimdi Yedek Al")
        self.btn_yedek_al.setObjectName("btnSuccess")
        self.btn_yedek_al.clicked.connect(self.manuel_yedek_al)
        y_islem_bar.addWidget(self.btn_yedek_al)

        self.btn_harici_yedek = QPushButton("📁 Harici Konuma / USB'ye Yedekle")
        self.btn_harici_yedek.setObjectName("btnSecondary")
        self.btn_harici_yedek.clicked.connect(self.harici_konuma_yedekle)
        y_islem_bar.addWidget(self.btn_harici_yedek)

        self.btn_geri_yukle = QPushButton("🔄 Seçilen Yedekten Geri Yükle")
        self.btn_geri_yukle.setObjectName("btnWarning")
        self.btn_geri_yukle.clicked.connect(self.secili_yedekten_geri_yukle)
        y_islem_bar.addWidget(self.btn_geri_yukle)

        y_islem_bar.addStretch()
        y_layout.addLayout(y_islem_bar)

        self.tablo_yedek = QTableWidget()
        self.tablo_yedek.setColumnCount(4)
        self.tablo_yedek.setHorizontalHeaderLabels(["Yedek Dosyası", "Tarih / Saat", "Boyut (KB)", "Tam Yol"])
        self.tablo_yedek.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tablo_yedek.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tablo_yedek.setAlternatingRowColors(True)
        self.tablo_yedek.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo_yedek.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        y_layout.addWidget(self.tablo_yedek)

        is_admin = self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici"
        if is_admin:
            alt_bar = QHBoxLayout()
            alt_bar.addStretch()
            self.btn_fabrika_sifirla = QPushButton("⚠️ Fabrika Ayarlarına Dön (Tüm Verileri Sil)")
            self.btn_fabrika_sifirla.setObjectName("btnDanger")
            self.btn_fabrika_sifirla.setMinimumHeight(38)
            self.btn_fabrika_sifirla.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 6px 14px;")
            self.btn_fabrika_sifirla.clicked.connect(self.fabrika_ayarlarina_don)
            alt_bar.addWidget(self.btn_fabrika_sifirla)
            y_layout.addLayout(alt_bar)

        self.tabs.addTab(tab_yedek, "🗄️ Yedekleme & Geri Yükleme")

        # 3. SEKME: Kullanıcı ve Personel Yönetimi (Yöneticiye Özel)
        tab_kullanici = QWidget()
        k_layout = QVBoxLayout(tab_kullanici)
        k_layout.setContentsMargins(10, 15, 10, 10)

        is_admin = self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici"

        if is_admin:
            k_ust = QHBoxLayout()
            self.btn_yeni_kullanici = QPushButton("➕ Yeni Kullanıcı / Personel Ekle")
            self.btn_yeni_kullanici.setObjectName("btnSuccess")
            self.btn_yeni_kullanici.clicked.connect(self.yeni_kullanici_ac)
            k_ust.addWidget(self.btn_yeni_kullanici)
            k_ust.addStretch()
            k_layout.addLayout(k_ust)

            self.tablo_kullanici = QTableWidget()
            self.tablo_kullanici.setColumnCount(5)
            self.tablo_kullanici.setHorizontalHeaderLabels(["ID", "Kullanıcı Adı", "Ad Soyad", "Rol / Yetki", "Durum"])
            self.tablo_kullanici.setAlternatingRowColors(True)
            self.tablo_kullanici.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            k_layout.addWidget(self.tablo_kullanici)
        else:
            lbl_yetkisiz = QLabel("🔒 Kullanıcı yönetimi yalnızca 'Yönetici' rolüne sahip kullanıcılar tarafından görüntülenebilir.")
            lbl_yetkisiz.setStyleSheet("color: #e74c3c; font-size: 11pt; padding: 20px;")
            k_layout.addWidget(lbl_yetkisiz)

        self.tabs.addTab(tab_kullanici, "👥 Kullanıcılar & Yetkiler")

        ana_layout.addWidget(self.tabs)

    def ayarlari_yukle(self):
        try:
            conn = get_db_connection(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT anahtar, deger FROM ayar")
            ayarlar = {r["anahtar"]: r["deger"] for r in cur.fetchall()}
            conn.close()

            self.txt_dukkan_adi.setText(ayarlar.get("dukkan_adi", "Oto Yedek Parça Dükkanı"))
            self.txt_telefon.setText(ayarlar.get("telefon", ""))
            self.txt_adres.setText(ayarlar.get("adres", ""))
            self.spn_kdv.setValue(int(ayarlar.get("varsayilan_kdv", 20)))
            self.txt_fis_notu.setText(ayarlar.get("fis_alti_notu", "Bilgi fişidir, mali değeri yoktur."))
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Ayarlar yüklenemedi: {e}")

    def ayarlari_kaydet(self):
        if self.aktif_kullanici and self.aktif_kullanici.rol != "yonetici":
            QMessageBox.warning(self, "Yetkisiz İşlem", "Dükkan ayarlarını yalnızca Yönetici değiştirebilir.")
            return

        try:
            conn = get_db_connection(self.db_path)
            cur = conn.cursor()
            with conn:
                cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('dukkan_adi', ?)", (self.txt_dukkan_adi.text().strip(),))
                cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('telefon', ?)", (self.txt_telefon.text().strip(),))
                cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('adres', ?)", (self.txt_adres.text().strip(),))
                cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('varsayilan_kdv', ?)", (str(self.spn_kdv.value()),))
                cur.execute("INSERT OR REPLACE INTO ayar (anahtar, deger) VALUES ('fis_alti_notu', ?)", (self.txt_fis_notu.text().strip(),))
            conn.close()
            QMessageBox.information(self, "Başarılı", "Dükkan ayarları başarıyla kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def yedekleri_yukle(self):
        yedekler = self.yedek_servisi.mevcut_yedekleri_listele()
        self.tablo_yedek.setRowCount(0)
        for idx, y in enumerate(yedekler):
            self.tablo_yedek.insertRow(idx)
            self.tablo_yedek.setItem(idx, 0, QTableWidgetItem(y["dosya_adi"]))
            self.tablo_yedek.setItem(idx, 1, QTableWidgetItem(y["tarih"]))
            self.tablo_yedek.setItem(idx, 2, QTableWidgetItem(f"{y['boyut_kb']} KB"))
            self.tablo_yedek.setItem(idx, 3, QTableWidgetItem(y["yol"]))

    def manuel_yedek_al(self):
        try:
            dosya = self.yedek_servisi.yedek_al()
            QMessageBox.information(self, "Yedek Alındı", f"Veritabanı yedeği başarıyla oluşturuldu:\n{dosya.name}")
            self.yedekleri_yukle()
        except Exception as e:
            QMessageBox.critical(self, "Yedek Hatası", str(e))

    def harici_konuma_yedekle(self):
        dizin = QFileDialog.getExistingDirectory(self, "Yedek Kaydedilecek Konumu / USB Sürücüyü Seçin")
        if dizin:
            try:
                dosya = self.yedek_servisi.yedek_al(ozel_hedef_dizin=dizin)
                QMessageBox.information(self, "Yedek Alındı", f"Yedek başarıyla seçilen konuma kaydedildi:\n{dosya}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def secili_yedekten_geri_yukle(self):
        if self.aktif_kullanici and self.aktif_kullanici.rol != "yonetici":
            QMessageBox.warning(self, "Yetkisiz İşlem", "Veritabanını geri yükleme yetkisi yalnızca Yöneticiye aittir.")
            return

        secili = self.tablo_yedek.selectedItems()
        if not secili:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen listeden geri yüklemek istediğiniz yedek dosyasını seçiniz.")
            return

        satir = secili[0].row()
        yedek_yolu = self.tablo_yedek.item(satir, 3).text()

        onay = QMessageBox.warning(
            self,
            "DİKKAT: Veritabanı Geri Yükleme",
            f"Seçilen yedeği geri yüklemek üzeresiniz:\n{yedek_yolu}\n\n"
            "Bu işlem mevcut veritabanını seçilen yedeğin durumuyla değiştirecektir!\n"
            "(İşlem öncesinde mevcut veritabanınızın otomatik güvenlik yedeği alınacaktır)\n\n"
            "Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if onay == QMessageBox.Yes:
            try:
                self.yedek_servisi.yedekten_geri_yukle(yedek_yolu)
                QMessageBox.information(
                    self,
                    "Geri Yükleme Başarılı",
                    "Veritabanı seçilen yedekten başarıyla geri yüklendi!\n"
                    "Verilerin güncellenmesi için uygulama yeniden başlatılabilir veya ekranlar yenilenebilir."
                )
                self.ayarlari_yukle()
                self.yedekleri_yukle()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def saglik_kontrolu_yap(self):
        saglikli, mesaj = check_db_health(self.db_path)
        if saglikli:
            QMessageBox.information(self, "Veritabanı Sağlam", f"✅ PRAGMA quick_check Sonucu:\n\n{mesaj}\nVeritabanı bütünlüğü kusursuzdur.")
        else:
            QMessageBox.critical(self, "Bozukluk Tespit Edildi", f"⚠️ Veritabanında hata tespit edildi:\n\n{mesaj}\nLütfen en son sağlam yedekten geri yükleme yapınız.")

    def kullanicilari_yukle(self):
        if not hasattr(self, "tablo_kullanici"):
            return
        kullanicilar = self.kimlik_servisi.kullanicilari_listele()
        self.tablo_kullanici.setRowCount(0)
        for idx, k in enumerate(kullanicilar):
            self.tablo_kullanici.insertRow(idx)
            self.tablo_kullanici.setItem(idx, 0, QTableWidgetItem(str(k.id)))
            self.tablo_kullanici.setItem(idx, 1, QTableWidgetItem(k.kullanici_adi))
            self.tablo_kullanici.setItem(idx, 2, QTableWidgetItem(k.ad_soyad))
            rol_str = "Yönetici" if k.rol == "yonetici" else "Personel (Tezgahtar)"
            self.tablo_kullanici.setItem(idx, 3, QTableWidgetItem(rol_str))
            self.tablo_kullanici.setItem(idx, 4, QTableWidgetItem("Aktif" if k.aktif == 1 else "Pasif"))

    def yeni_kullanici_ac(self):
        diyalog = QDialog(self)
        from app.ui.theme import apply_theme
        apply_theme(diyalog)
        diyalog.setWindowTitle("Yeni Kullanıcı Ekle")
        diyalog.resize(380, 280)
        d_layout = QVBoxLayout(diyalog)

        kart = QFrame()
        kart.setObjectName("cardFrame")
        form = QFormLayout(kart)

        txt_ad = QLineEdit()
        form.addRow("Ad Soyad (*):", txt_ad)

        txt_kadi = QLineEdit()
        form.addRow("Kullanıcı Adı (*):", txt_kadi)

        txt_parola = QLineEdit()
        txt_parola.setEchoMode(QLineEdit.Password)
        form.addRow("Parola (*):", txt_parola)

        cmb_rol = QComboBox()
        cmb_rol.addItem("Personel (Tezgahtar)", "personel")
        cmb_rol.addItem("Yönetici (Tam Yetkili)", "yonetici")
        form.addRow("Yetki Rolü:", cmb_rol)

        d_layout.addWidget(kart)

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        d_layout.addWidget(btn_box)

        def kaydet():
            ad = txt_ad.text().strip()
            kadi = txt_kadi.text().strip()
            parola = txt_parola.text().strip()
            rol = cmb_rol.currentData()

            if not ad or not kadi or not parola:
                QMessageBox.warning(diyalog, "Eksik", "Lütfen tüm zorunlu alanları doldurunuz.")
                return

            try:
                self.kimlik_servisi.kullanici_olustur(kadi, parola, ad, rol)
                QMessageBox.information(diyalog, "Başarılı", f"'{kadi}' kullanıcısı oluşturuldu.")
                diyalog.accept()
                self.kullanicilari_yukle()
            except Exception as e:
                QMessageBox.critical(diyalog, "Hata", str(e))

        btn_box.accepted.connect(kaydet)
        btn_box.rejected.connect(diyalog.reject)
        diyalog.exec()

    def fabrika_ayarlarina_don(self):
        """
        Yönetici doğrulaması ve 'SIFIRLA' onayı ile tüm verileri sıfırlar.
        Önce tam otomatik güvenlik yedeği alır, denetim kaydına yazar ve
        işlem sonunda ilk kurulum sihirbazını tetikler.
        """
        if not self.aktif_kullanici or self.aktif_kullanici.rol != "yonetici":
            QMessageBox.warning(self, "Yetkisiz İşlem", "Bu işlem yalnızca Yönetici yetkisine sahip kullanıcılar tarafından gerçekleştirilebilir.")
            return

        diyalog = QDialog(self)
        from app.ui.theme import apply_theme
        apply_theme(diyalog)
        diyalog.setWindowTitle("⚠️ Fabrika Ayarlarına Sıfırlama Onayı")
        diyalog.setWindowFlags(diyalog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        diyalog.resize(460, 320)
        d_layout = QVBoxLayout(diyalog)
        d_layout.setSpacing(12)

        lbl_uyari = QLabel(
            "<b>DİKKAT: TÜM VERİLER SİLİNECEKTİR!</b><br><br>"
            "Bu işlem mevcut tüm ürünleri, stokları, siparişleri, cari hesapları "
            "ve ayarları kalıcı olarak silecektir.<br>"
            "İşlem öncesinde veritabanınızın tam bir <b>güvenlik yedeği</b> otomatik olarak alınacaktır.<br><br>"
            "Devam etmek için yönetici parolanızı giriniz ve onay kutusuna <b>SIFIRLA</b> yazınız."
        )
        lbl_uyari.setWordWrap(True)
        lbl_uyari.setStyleSheet("color: #e74c3c; font-size: 10pt;")
        d_layout.addWidget(lbl_uyari)

        kart = QFrame()
        kart.setObjectName("cardFrame")
        form = QFormLayout(kart)

        txt_parola = QLineEdit()
        txt_parola.setEchoMode(QLineEdit.Password)
        txt_parola.setPlaceholderText("Yönetici parolanız")
        form.addRow("Yönetici Parolası (*):", txt_parola)

        txt_kelime = QLineEdit()
        txt_kelime.setPlaceholderText("SIFIRLA")
        form.addRow("Onay Kelimesi (*):", txt_kelime)

        d_layout.addWidget(kart)

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Tüm Verileri Sıfırla")
        d_layout.addWidget(btn_box)

        # Referanslar
        diyalog.txt_parola = txt_parola
        diyalog.txt_kelime = txt_kelime

        def onayla():
            parola = txt_parola.text().strip()
            kelime = txt_kelime.text().strip()

            if not parola:
                QMessageBox.warning(diyalog, "Eksik Bilgi", "Lütfen yönetici parolanızı giriniz.")
                return

            # 1. Parola doğrula
            try:
                dogrulandi = self.kimlik_servisi.giris_yap(self.aktif_kullanici.kullanici_adi, parola)
            except Exception:
                dogrulandi = None

            if not dogrulandi:
                QMessageBox.critical(
                    diyalog,
                    "Hatalı Parola",
                    "Girdiğiniz yönetici parolası hatalı! İşlem iptal edildi, hiçbir veri silinmedi."
                )
                diyalog.reject()
                return

            # 2. Onay kelimesi doğrula
            if kelime != "SIFIRLA":
                QMessageBox.critical(
                    diyalog,
                    "Hatalı Onay Kelimesi",
                    "Onay kelimesi tam olarak 'SIFIRLA' olmalıdır! İşlem iptal edildi, hiçbir veri silinmedi."
                )
                diyalog.reject()
                return

            # 3. İki kontrol de geçti: Güvenlik yedeği al
            try:
                yedek_dosyasi = self.yedek_servisi.yedek_al()
            except Exception as ye:
                QMessageBox.critical(
                    diyalog,
                    "Güvenlik Yedeği Alınamadı",
                    f"Sıfırlama öncesi otomatik güvenlik yedeği alınamadığı için işlem durduruldu:\n{ye}"
                )
                diyalog.reject()
                return

            # 4. Denetim kaydı ve veritabanı sıfırlama
            try:
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                with conn:
                    # Denetim kaydı ekle
                    cur.execute(
                        "INSERT INTO denetim_log (kullanici_id, islem, detay) VALUES (?, 'FABRIKA_AYARLARI_SIFIRLAMA', ?)",
                        (self.aktif_kullanici.id, f"Güvenlik yedeği alındı: {yedek_dosyasi.name}")
                    )
                    # Tabloları temizle
                    tablolar = [
                        "siparis_kalem", "siparis", "stok_hareket", "tahsilat",
                        "mal_kabul_kalem", "mal_kabul", "tedarikci",
                        "musteri", "urun", "marka", "kategori", "ayar", "kullanici"
                    ]
                    for t in tablolar:
                        cur.execute(f"DELETE FROM {t}")
                conn.close()

                QMessageBox.information(
                    diyalog,
                    "Fabrika Ayarlarına Sıfırlandı",
                    "Tüm veriler başarıyla sıfırlandı ve otomatik güvenlik yedeği alındı.\n"
                    "Sistem ilk kurulum sihirbazına yönlendiriliyor."
                )
                diyalog.accept()

                # İlk kurulum sihirbazını aç
                from app.ui.pages.login_dialog import LoginDialog
                sihirbaz = LoginDialog(self.kimlik_servisi, self.window())
                apply_theme(sihirbaz)
                sihirbaz.exec()

            except Exception as e:
                QMessageBox.critical(diyalog, "Sıfırlama Hatası", f"Veritabanı sıfırlanırken hata oluştu:\n{e}")

        btn_box.accepted.connect(onayla)
        btn_box.rejected.connect(diyalog.reject)
        diyalog.exec()

