from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
import sys
import sqlite3


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 700)

        # =========================
        # MODERN DARK STYLE
        # =========================
        MainWindow.setStyleSheet("""
        QMainWindow{
            background-color: #1e1f26;
        }

        QWidget{
            color: white;
            font-family: Segoe UI;
            font-size: 10pt;
        }

        QLabel{
            color: #dcdde1;
            font-weight: 600;
        }

        QLineEdit{
            background-color: #2f3640;
            border: 2px solid #3d3d3d;
            border-radius: 10px;
            padding: 8px;
            color: white;
        }

        QLineEdit:focus{
            border: 2px solid #00a8ff;
        }

        QPushButton{
            background-color: #00a8ff;
            border: none;
            border-radius: 12px;
            padding: 8px;
            color: white;
            font-weight: bold;
        }

        QPushButton:hover{
            background-color: #0097e6;
        }

        QPushButton:pressed{
            background-color: #40739e;
        }

        QTableWidget{
            background-color: #2f3640;
            border-radius: 15px;
            gridline-color: #444;
            color: white;
            selection-background-color: #00a8ff;
        }

        QHeaderView::section{
            background-color: #00a8ff;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }

        QScrollBar:vertical{
            background: #2f3640;
            width: 10px;
        }

        QScrollBar::handle:vertical{
            background: #00a8ff;
            border-radius: 5px;
        }
        """)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # =========================
        # ANA FRAME
        # =========================
        self.mainFrame = QtWidgets.QFrame(self.centralwidget)
        self.mainFrame.setGeometry(QtCore.QRect(20, 20, 1160, 640))
        self.mainFrame.setStyleSheet("""
        QFrame{
            background-color:#262b33;
            border-radius:20px;
        }
        """)

        # =========================
        # BAŞLIK
        # =========================
        self.label = QtWidgets.QLabel(self.mainFrame)
        self.label.setGeometry(QtCore.QRect(30, 20, 500, 45))
        self.label.setText("📋 SİPARİŞ YÖNETİM PANELİ")
        self.label.setStyleSheet("""
        font-size:22px;
        font-weight:bold;
        color:#00a8ff;
        """)

        # ICON
        self.iconLabel = QtWidgets.QLabel(self.mainFrame)
        self.iconLabel.setGeometry(QtCore.QRect(1050, 10, 60, 60))
        self.iconLabel.setText("🚚")
        self.iconLabel.setStyleSheet("""
        font-size:30px;
        """)

        # =========================
        # PARÇA KODU
        # =========================
        self.label_2 = QtWidgets.QLabel(self.mainFrame)
        self.label_2.setGeometry(QtCore.QRect(30, 90, 150, 30))
        self.label_2.setText("🔧 Parça Kodu")

        self.lnparcakodu = QtWidgets.QLineEdit(self.mainFrame)
        self.lnparcakodu.setGeometry(QtCore.QRect(30, 120, 250, 40))
        self.lnparcakodu.setPlaceholderText("Parça kodu giriniz...")

        # =========================
        # PARÇA ADI
        # =========================
        self.label_3 = QtWidgets.QLabel(self.mainFrame)
        self.label_3.setGeometry(QtCore.QRect(320, 90, 150, 30))
        self.label_3.setText("🔍 Parça Adı")

        self.lnparcaadi = QtWidgets.QLineEdit(self.mainFrame)
        self.lnparcaadi.setGeometry(QtCore.QRect(320, 120, 250, 40))
        self.lnparcaadi.setPlaceholderText("Parça adı giriniz...")

        # =========================
        # BUTONLAR
        # =========================
        self.listele1 = QtWidgets.QPushButton(self.mainFrame)
        self.listele1.setGeometry(QtCore.QRect(620, 120, 230, 40))
        self.listele1.setText("📄 KODA GÖRE LİSTELE")

        self.listele2 = QtWidgets.QPushButton(self.mainFrame)
        self.listele2.setGeometry(QtCore.QRect(880, 120, 230, 40))
        self.listele2.setText("📄 ADA GÖRE LİSTELE")

        # =========================
        # TABLO
        # =========================
        self.tablo = QtWidgets.QTableWidget(self.mainFrame)
        self.tablo.setGeometry(QtCore.QRect(30, 200, 1080, 390))

        self.tablo.setRowCount(100)
        self.tablo.setColumnCount(6)

        self.tablo.setHorizontalHeaderLabels([
            "Kod",
            "Parça Adı",
            "Fiyat",
            "Açıklama",
            "Marka",
            "Kategori"
        ])

        self.tablo.horizontalHeader().setStretchLastSection(True)
        self.tablo.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )

        self.tablo.setAlternatingRowColors(True)

        # =========================
        # STATUS BAR
        # =========================
        MainWindow.setMenuBar(QtWidgets.QMenuBar(MainWindow))
        MainWindow.setStatusBar(QtWidgets.QStatusBar(MainWindow))

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle("Alınan Siparişler")