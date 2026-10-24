import sys
import sqlite3
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QMessageBox, QHeaderView

# Kendi arayüz dosyanı içe aktar
from arayüz2 import Ui_MainWindow
# Modern stil dosyamızı içe aktar (Önceki adımda oluşturduysan)
try:
    import modern_stil
except ImportError:
    modern_stil = None

class AlinanSiparisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # MODERN STİL UYGULAMASI
        if modern_stil:
            self.setStyleSheet(modern_stil.get_modern_qss())
        else:
            # Stil dosyası yoksa temel bir güzelleştirme yap
            self.setStyleSheet("QTableWidget { background-color: white; } QHeaderView::section { font-weight: bold; }")

        # Tablo ayarları
        self.ui.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tablo.setAlternatingRowColors(True)

        # Buton Bağlantıları (Arayüzündeki buton isimlerine göre kontrol et)
        # Not: arayüz2.py içindeki buton isimlerin listele1 ve listele2 olarak görünüyor
        self.ui.listele1.clicked.connect(self.koda_gore_listele)
        self.ui.listele2.clicked.connect(self.ada_gore_listele)

        # Açılışta tüm siparişleri listele
        self.tumunu_listele()

    def verileri_getir(self, kod=None, ad=None):
        try:
            baglanti = sqlite3.connect("urunler12.db")
            imlec = baglanti.cursor()
            
            if kod:
                imlec.execute("SELECT * FROM siparisal2 WHERE urunadi LIKE ?", (f"%{kod}%",)) # Veya urun kodu sütunun hangisiyse
            elif ad:
                imlec.execute("SELECT * FROM siparisal2 WHERE urunadi LIKE ?", (f"%{ad}%",))
            else:
                imlec.execute("SELECT * FROM siparisal2")

            sonuc = imlec.fetchall()
            baglanti.close()
            return sonuc
        except Exception as e:
            print(f"Hata: {e}")
            return []

    def tumunu_listele(self):
        veriler = self.verileri_getir()
        self.tabloyu_doldur(veriler)

    def koda_gore_listele(self):
        metin = self.ui.lnparcakodu.text().strip()
        if metin:
            self.tabloyu_doldur(self.verileri_getir(kod=metin))
        else:
            self.tumunu_listele()

    def ada_gore_listele(self):
        ad = self.ui.lnparcaadi.text().strip()
        if ad:
            self.tabloyu_doldur(self.verileri_getir(ad=ad))
        else:
            self.tumunu_listele()

    def tabloyu_doldur(self, veriler):
        self.ui.tablo.setRowCount(0)
        if not veriler:
            return

        for indexSatir, kayit in enumerate(veriler):
            self.ui.tablo.insertRow(indexSatir)
            for indexSutun, veri in enumerate(kayit):
                self.ui.tablo.setItem(indexSatir, indexSutun, QTableWidgetItem(str(veri)))

# --- KRİTİK DÜZELTME BURASI ---
def main():
    # 1. Mevcut bir uygulama (QApplication) var mı kontrol et
    app = QtWidgets.QApplication.instance()
    if not app:
        # Eğer yoksa (dosya tek başına çalıştırılıyorsa) yeni oluştur
        app = QtWidgets.QApplication(sys.argv)
        
    global alinan_siparis_penceresi
    alinan_siparis_penceresi = AlinanSiparisWindow()
    alinan_siparis_penceresi.show()

    # 2. Sadece dosya tek başına çalıştırılıyorsa exec_() çağır
    # Eğer giris1.py içinden çağrılıyorsa burası çalışmaz ve hata almazsın
    if app.property("is_main"): # Veya sadece if __name__ == "__main__": kontrolü yeterli
        sys.exit(app.exec_())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setProperty("is_main", True) # Ana uygulama olduğunu işaretle
    window = AlinanSiparisWindow()
    window.show()
    sys.exit(app.exec_())