import sys
import sqlite3
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1250, 650)

        # =========================
        # MODERN DARK THEME
        # =========================
        MainWindow.setStyleSheet("""
        QMainWindow{
            background-color:#1e1f26;
        }

        QWidget{
            color:white;
            font-family:Segoe UI;
            font-size:10pt;
        }

        QLabel{
            color:#dcdde1;
            font-weight:600;
        }

        QLineEdit{
            background-color:#2f3640;
            border:2px solid #3d3d3d;
            border-radius:12px;
            padding:10px;
            color:white;
        }

        QLineEdit:focus{
            border:2px solid #00a8ff;
        }

        QPushButton{
            background-color:#00a8ff;
            border:none;
            border-radius:15px;
            padding:10px;
            color:white;
            font-weight:bold;
        }

        QPushButton:hover{
            background-color:#0097e6;
        }

        QPushButton:pressed{
            background-color:#40739e;
        }

        QDateEdit{
            background-color:#2f3640;
            border:2px solid #3d3d3d;
            border-radius:12px;
            padding:8px;
            color:white;
        }

        QDateEdit:focus{
            border:2px solid #00a8ff;
        }

        QTableWidget{
            background-color:#2f3640;
            border-radius:15px;
            gridline-color:#444;
            color:white;
            selection-background-color:#00a8ff;
        }

        QHeaderView::section{
            background-color:#00a8ff;
            color:white;
            padding:8px;
            border:none;
            font-weight:bold;
        }

        QScrollBar:vertical{
            background:#2f3640;
            width:10px;
        }

        QScrollBar::handle:vertical{
            background:#00a8ff;
            border-radius:5px;
        }
        """)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # =========================
        # ANA FRAME
        # =========================
        self.mainFrame = QtWidgets.QFrame(self.centralwidget)
        self.mainFrame.setGeometry(QtCore.QRect(20, 20, 1210, 600))

        self.mainFrame.setStyleSheet("""
        QFrame{
            background-color:#262b33;
            border-radius:25px;
        }
        """)

        # =========================
        # BAŞLIK
        # =========================
        self.label = QtWidgets.QLabel(self.mainFrame)
        self.label.setGeometry(QtCore.QRect(30, 20, 500, 50))

        titleFont = QtGui.QFont()
        titleFont.setFamily("Segoe UI")
        titleFont.setPointSize(20)
        titleFont.setBold(True)

        self.label.setFont(titleFont)

        self.label.setStyleSheet("""
        color:#00a8ff;
        """)

        self.label.setText("📦 PARÇA SİPARİŞ PANELİ")

        # ICON
        self.iconLabel = QtWidgets.QLabel(self.mainFrame)
        self.iconLabel.setGeometry(QtCore.QRect(1120, 15, 60, 60))
        self.iconLabel.setText("🚚")
        self.iconLabel.setStyleSheet("""
        font-size:30px;
        """)

        # =========================
        # SOL PANEL
        # =========================
        self.leftPanel = QtWidgets.QFrame(self.mainFrame)
        self.leftPanel.setGeometry(QtCore.QRect(30, 90, 320, 470))

        self.leftPanel.setStyleSheet("""
        QFrame{
            background-color:#1f232b;
            border-radius:20px;
        }
        """)

        # =========================
        # PARÇA ADI
        # =========================
        self.labelParca = QtWidgets.QLabel(self.leftPanel)
        self.labelParca.setGeometry(QtCore.QRect(20, 20, 200, 30))
        self.labelParca.setText("🔧 Parça Adı")

        self.lineEdit = QtWidgets.QLineEdit(self.leftPanel)
        self.lineEdit.setGeometry(QtCore.QRect(20, 55, 280, 45))
        self.lineEdit.setPlaceholderText("Parça adı giriniz...")

        # =========================
        # SİPARİŞ OLUŞTUR
        # =========================
        self.pushButton = QtWidgets.QPushButton(self.leftPanel)
        self.pushButton.setGeometry(QtCore.QRect(20, 120, 280, 45))
        self.pushButton.setText("📦 SİPARİŞ OLUŞTUR")

        # =========================
        # ADET
        # =========================
        self.label_3 = QtWidgets.QLabel(self.leftPanel)
        self.label_3.setGeometry(QtCore.QRect(20, 190, 200, 30))
        self.label_3.setText("📦 İstenen Adet")

        self.lineEdit_3 = QtWidgets.QLineEdit(self.leftPanel)
        self.lineEdit_3.setGeometry(QtCore.QRect(20, 225, 280, 45))
        self.lineEdit_3.setPlaceholderText("Adet giriniz...")

        # =========================
        # AÇIKLAMA
        # =========================
        self.label_4 = QtWidgets.QLabel(self.leftPanel)
        self.label_4.setGeometry(QtCore.QRect(20, 290, 220, 30))
        self.label_4.setText("📝 Açıklama / Adres")

        self.lineEdit_4 = QtWidgets.QLineEdit(self.leftPanel)
        self.lineEdit_4.setGeometry(QtCore.QRect(20, 325, 280, 45))
        self.lineEdit_4.setPlaceholderText("Adres veya açıklama...")

        # =========================
        # TARİH
        # =========================
        self.label_5 = QtWidgets.QLabel(self.leftPanel)
        self.label_5.setGeometry(QtCore.QRect(20, 390, 200, 30))
        self.label_5.setText("📅 Tarih Seç")

        self.dateEdit = QtWidgets.QDateEdit(self.leftPanel)
        self.dateEdit.setGeometry(QtCore.QRect(20, 425, 280, 45))
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(QtCore.QDate.currentDate())

        # =========================
        # SAĞ PANEL (TABLO)
        # =========================
        self.rightPanel = QtWidgets.QFrame(self.mainFrame)
        self.rightPanel.setGeometry(QtCore.QRect(380, 90, 800, 470))

        self.rightPanel.setStyleSheet("""
        QFrame{
            background-color:#1f232b;
            border-radius:20px;
        }
        """)

        # TABLO BAŞLIK
        self.tableTitle = QtWidgets.QLabel(self.rightPanel)
        self.tableTitle.setGeometry(QtCore.QRect(20, 15, 400, 40))

        self.tableTitle.setText("📋 OLUŞTURULAN SİPARİŞLER")

        self.tableTitle.setStyleSheet("""
        font-size:16pt;
        font-weight:bold;
        color:#00a8ff;
        """)

        # =========================
        # TABLO
        # =========================
        self.tableWidget = QtWidgets.QTableWidget(self.rightPanel)
        self.tableWidget.setGeometry(QtCore.QRect(20, 70, 760, 370))

        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(5)

        self.tableWidget.setAlternatingRowColors(True)

        self.tableWidget.setHorizontalHeaderLabels([
            "Parça Adı",
            "Adet",
            "Tarih",
            "Açıklama",
            "Durum"
        ])

        self.tableWidget.horizontalHeader().setStretchLastSection(True)

        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )

        MainWindow.setCentralWidget(self.centralwidget)

        # STATUSBAR
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)


class SiparisAlmaWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # MODERN ARAYÜZ (QSS) UYGULAMASI
        self.setStyleSheet("""
            QWidget { background-color: #f8f9fa; font-family: 'Segoe UI'; color: #212529; }
            QPushButton { 
                background-color: #198754; color: white; border-radius: 6px; 
                padding: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #157347; }
            QLineEdit, QDateEdit { 
                border: 1px solid #ced4da; border-radius: 5px; padding: 5px; background: white; 
            }
            QTableWidget { background-color: white; border: 1px solid #dee2e6; }
            QHeaderView::section { background-color: #f1f3f5; font-weight: bold; border: 1px solid #dee2e6; }
        """)

        # Butonu tek bir fonksiyona bağlıyoruz
        self.pushButton.clicked.connect(self.siparis_olustur_ve_stok_dus)

    def siparis_olustur_ve_stok_dus(self):
        urunadi = self.lineEdit.text().strip()
        aciklama = self.lineEdit_4.text().strip()
        tarih = self.dateEdit.date().toString("yyyy-MM-dd")

        if not urunadi:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lütfen bir parça adı girin!")
            return

        try:
            istenenadet = int(self.lineEdit_3.text().strip())
            if istenenadet <= 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Hata", "İstenen adet geçerli ve pozitif bir sayı olmalıdır!")
            return

        try:
            conn = sqlite3.connect("urunler12.db")
            cursor = conn.cursor()

            # 1. Stok Kontrolü (Ürün var mı ve yeterli stok var mı?)
            cursor.execute("SELECT stokMiktari FROM urun WHERE urunAdi = ?", (urunadi,))
            sonuc = cursor.fetchone()

            if sonuc is None:
                QtWidgets.QMessageBox.warning(self, "Hata", f"'{urunadi}' isimli ürün depoda bulunamadı!")
                return

            mevcut_stok = sonuc[0]
            if mevcut_stok < istenenadet:
                QtWidgets.QMessageBox.warning(self, "Hata", f"Yetersiz stok! Depodaki mevcut adet: {mevcut_stok}")
                return

            # 2. Siparişi siparisal2 Tablosuna Ekleme
            cursor.execute("""
                INSERT INTO siparisal2 (urunadi, istenenadet, aciklama, tarih)
                VALUES (?, ?, ?, ?)""", (urunadi, istenenadet, aciklama, tarih))

            # 3. Ürün Tablosundan Stoğu Düşme
            cursor.execute("""
                UPDATE urun SET stokMiktari = stokMiktari - ? 
                WHERE urunAdi = ?""", (istenenadet, urunadi))
            
            conn.commit()

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Veritabanı Hatası", f"İşlem sırasında hata oluştu:\n{e}")
            return
        finally:
            conn.close()

        # İşlem başarılıysa Arayüzdeki Tabloyu Güncelle
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(urunadi))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(str(istenenadet)))
        self.tableWidget.setItem(row, 2, QTableWidgetItem(tarih))
        self.tableWidget.setItem(row, 3, QTableWidgetItem(aciklama))
        self.tableWidget.setItem(row, 4, QTableWidgetItem("✅ Onaylandı"))

        QtWidgets.QMessageBox.information(self, "Başarılı", f"{urunadi} siparişi başarıyla oluşturuldu ve stoktan düşüldü.")

        # Alanları temizle (kullanıcı deneyimi için)
        self.lineEdit.clear()
        self.lineEdit_3.clear()
        self.lineEdit_4.clear()


def main():
    # Çift uygulama açılışını engellemek için kontrol
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
        
    global siparis_penceresi
    siparis_penceresi = SiparisAlmaWindow()
    siparis_penceresi.show()

if __name__== "__main__":
    main()