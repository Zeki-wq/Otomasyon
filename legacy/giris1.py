import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from arayüz3giris import Ui_MainWindow

# Diğer modülleri içe aktarıyoruz
import pyton1
import siparisalma3
import alinansiparis

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # --- MODERN ARAYÜZ STİLİ (QSS) ---
        # Tüm programa modern bir görünüm kazandırır
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #212529;
            }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton#giris3 { /* Siparişler butonu için farklı renk örneği */
                background-color: #198754;
            }
            QPushButton#giris3:hover {
                background-color: #157347;
            }
            QLabel {
                color: #343a40;
            }
            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 6px;
                background-color: white;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                gridline-color: #e9ecef;
            }
            QHeaderView::section {
                background-color: #f1f3f5;
                padding: 4px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #dee2e6;
            }
        """)

        # Butonların işlevlerini bağlıyoruz
        self.ui.giris1.clicked.connect(self.run_pyton1)
        self.ui.giris2.clicked.connect(self.run_siparisalma3)
        self.ui.giris3.clicked.connect(self.run_alinansiparis1)
        
    def run_pyton1(self):
        # Depo/Ürün Yönetimi ekranını açar
        pyton1.main()

    def run_siparisalma3(self):
        # Yeni Sipariş Alma ekranını açar
        siparisalma3.main()

    def run_alinansiparis1(self):
        # Alınan Siparişleri Listeleme ekranını açar
        alinansiparis.main()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())