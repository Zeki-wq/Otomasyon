from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 500)

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
        }

        QPushButton{
            border:none;
            border-radius:15px;
            padding:12px;
            font-weight:bold;
            color:white;
            font-size:11pt;
        }

        QPushButton:hover{
            border:2px solid white;
        }

        QPushButton:pressed{
            padding-left:15px;
            padding-top:15px;
        }
        """)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # =========================
        # ANA FRAME
        # =========================
        self.mainFrame = QtWidgets.QFrame(self.centralwidget)
        self.mainFrame.setGeometry(QtCore.QRect(20, 20, 860, 430))
        self.mainFrame.setStyleSheet("""
        QFrame{
            background-color:#262b33;
            border-radius:25px;
        }
        """)

        # =========================
        # ÜST BAŞLIK
        # =========================
        self.label = QtWidgets.QLabel(self.mainFrame)
        self.label.setGeometry(QtCore.QRect(50, 20, 760, 80))

        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(24)
        font.setBold(True)

        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.label.setStyleSheet("""
        color:#00a8ff;
        background-color:#1f232b;
        border-radius:20px;
        padding:15px;
        """)

        # ICON
        self.iconLabel = QtWidgets.QLabel(self.mainFrame)
        self.iconLabel.setGeometry(QtCore.QRect(390, 105, 80, 60))
        self.iconLabel.setText("🚗")
        self.iconLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.iconLabel.setStyleSheet("""
        font-size:32pt;
        color:#00a8ff;
        """)

        # =========================
        # SOL BİLGİ PANELİ
        # =========================
        self.leftPanel = QtWidgets.QFrame(self.mainFrame)
        self.leftPanel.setGeometry(QtCore.QRect(70, 170, 250, 200))

        self.leftPanel.setStyleSheet("""
        QFrame{
            background-color:#1f232b;
            border-radius:20px;
        }
        """)

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.leftPanel)
        self.verticalLayout_2.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout_2.setSpacing(25)

        font2 = QtGui.QFont()
        font2.setPointSize(14)
        font2.setBold(True)

        self.label_4 = QtWidgets.QLabel(self.leftPanel)
        self.label_4.setFont(font2)
        self.label_4.setStyleSheet("color:#00cec9;")
        self.verticalLayout_2.addWidget(self.label_4)

        self.label_2 = QtWidgets.QLabel(self.leftPanel)
        self.label_2.setFont(font2)
        self.label_2.setStyleSheet("color:#74b9ff;")
        self.verticalLayout_2.addWidget(self.label_2)

        self.label_3 = QtWidgets.QLabel(self.leftPanel)
        self.label_3.setFont(font2)
        self.label_3.setStyleSheet("color:#ff7675;")
        self.verticalLayout_2.addWidget(self.label_3)

        # =========================
        # SAĞ BUTON PANELİ
        # =========================
        self.rightPanel = QtWidgets.QFrame(self.mainFrame)
        self.rightPanel.setGeometry(QtCore.QRect(500, 170, 250, 200))

        self.rightPanel.setStyleSheet("""
        QFrame{
            background-color:#1f232b;
            border-radius:20px;
        }
        """)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.rightPanel)
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setSpacing(20)

        # =========================
        # BUTON 1
        # =========================
        self.giris1 = QtWidgets.QPushButton(self.rightPanel)
        self.giris1.setMinimumHeight(45)

        self.giris1.setStyleSheet("""
        QPushButton{
            background-color:#00a8ff;
            border-radius:15px;
            color:white;
            font-weight:bold;
        }

        QPushButton:hover{
            background-color:#0097e6;
        }

        QPushButton:pressed{
            background-color:#40739e;
        }
        """)

        self.verticalLayout.addWidget(self.giris1)

        # =========================
        # BUTON 2
        # =========================
        self.giris2 = QtWidgets.QPushButton(self.rightPanel)
        self.giris2.setMinimumHeight(45)

        self.giris2.setStyleSheet("""
        QPushButton{
            background-color:#00b894;
            border-radius:15px;
            color:white;
            font-weight:bold;
        }

        QPushButton:hover{
            background-color:#00cec9;
        }

        QPushButton:pressed{
            background-color:#00997a;
        }
        """)

        self.verticalLayout.addWidget(self.giris2)

        # =========================
        # BUTON 3
        # =========================
        self.giris3 = QtWidgets.QPushButton(self.rightPanel)
        self.giris3.setMinimumHeight(45)

        self.giris3.setStyleSheet("""
        QPushButton{
            background-color:#d63031;
            border-radius:15px;
            color:white;
            font-weight:bold;
        }

        QPushButton:hover{
            background-color:#ff7675;
        }

        QPushButton:pressed{
            background-color:#b71540;
        }
        """)

        self.verticalLayout.addWidget(self.giris3)

        MainWindow.setCentralWidget(self.centralwidget)

        # =========================
        # MENUBAR & STATUSBAR
        # =========================
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate

        MainWindow.setWindowTitle(
            _translate("MainWindow", "Giriş Ekranı")
        )

        self.label.setText(
            _translate("MainWindow", "OTO YEDEK PARÇA SİSTEMİ")
        )

        self.label_4.setText(
            _translate("MainWindow", "📦 DEPO YÖNETİMİ")
        )

        self.label_2.setText(
            _translate("MainWindow", "🛒 SİPARİŞ AL")
        )

        self.label_3.setText(
            _translate("MainWindow", "📋 SİPARİŞLER")
        )

        self.giris1.setText(
            _translate("MainWindow", "🚗 Depo Girişi")
        )

        self.giris2.setText(
            _translate("MainWindow", "🛍 Sipariş Al")
        )

        self.giris3.setText(
            _translate("MainWindow", "📄 Siparişler")
        )