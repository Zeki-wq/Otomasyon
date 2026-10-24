from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 720)

        # MODERN DARK TEMA
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

        QComboBox{
            background-color: #2f3640;
            border: 2px solid #3d3d3d;
            border-radius: 10px;
            padding: 6px;
            color: white;
        }

        QComboBox:hover{
            border: 2px solid #00a8ff;
        }

        QPushButton{
            background-color: #00a8ff;
            border: none;
            border-radius: 12px;
            padding: 10px;
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
            border-radius: 12px;
            gridline-color: #444;
            color: white;
        }

        QHeaderView::section{
            background-color: #00a8ff;
            color: white;
            padding: 5px;
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
        self.centralwidget.setObjectName("centralwidget")

        # =======================
        # SOL PANEL
        # =======================
        self.leftFrame = QtWidgets.QFrame(self.centralwidget)
        self.leftFrame.setGeometry(QtCore.QRect(20, 20, 360, 620))
        self.leftFrame.setStyleSheet("""
        QFrame{
            background-color:#262b33;
            border-radius:20px;
        }
        """)

        # BAŞLIK
        self.title = QtWidgets.QLabel(self.leftFrame)
        self.title.setGeometry(QtCore.QRect(20, 20, 300, 40))
        self.title.setText("🚗 OTO YEDEK PARÇA YÖNETİMİ")
        self.title.setStyleSheet("""
        font-size:18pt;
        font-weight:bold;
        color:#00a8ff;
        """)

        # ICON
        self.iconLabel = QtWidgets.QLabel(self.leftFrame)
        self.iconLabel.setGeometry(QtCore.QRect(280, 10, 60, 60))
        self.iconLabel.setText("🔧")
        self.iconLabel.setStyleSheet("font-size:30pt;")

        # FORM LABELS
        self.label = QtWidgets.QLabel("PARÇA KODU", self.leftFrame)
        self.label.setGeometry(20, 90, 120, 25)

        self.label_2 = QtWidgets.QLabel("PARÇA ADI", self.leftFrame)
        self.label_2.setGeometry(20, 150, 120, 25)

        self.label_3 = QtWidgets.QLabel("BİRİM FİYATI", self.leftFrame)
        self.label_3.setGeometry(20, 210, 120, 25)

        self.label_4 = QtWidgets.QLabel("STOK MİKTARI", self.leftFrame)
        self.label_4.setGeometry(20, 270, 120, 25)

        # INPUTLAR
        self.lneurunkodu = QtWidgets.QLineEdit(self.leftFrame)
        self.lneurunkodu.setGeometry(20, 115, 300, 40)

        self.lneurunad = QtWidgets.QLineEdit(self.leftFrame)
        self.lneurunad.setGeometry(20, 175, 300, 40)

        self.lnebrmfiyat = QtWidgets.QLineEdit(self.leftFrame)
        self.lnebrmfiyat.setGeometry(20, 235, 300, 40)

        self.lnestokmiktar = QtWidgets.QLineEdit(self.leftFrame)
        self.lnestokmiktar.setGeometry(20, 295, 300, 40)

        # AÇIKLAMA
        self.label_5 = QtWidgets.QLabel("ÜRÜN AÇIKLAMASI", self.leftFrame)
        self.label_5.setGeometry(20, 350, 200, 25)

        self.lneurunAcklama = QtWidgets.QLineEdit(self.leftFrame)
        self.lneurunAcklama.setGeometry(20, 380, 300, 50)

        # MARKA
        self.label_6 = QtWidgets.QLabel("PARÇA MARKASI", self.leftFrame)
        self.label_6.setGeometry(20, 450, 150, 25)

        self.cmburunmarka = QtWidgets.QComboBox(self.leftFrame)
        self.cmburunmarka.setGeometry(20, 480, 140, 40)

        markalar = [
            "Bosch", "Delphi", "Valeo", "Brembo", "Malhe", "TRW",
            "Mann Filter", "Denso", "NGK", "Contitech", "Sachs",
            "Ferodo", "Febi Bilstein", "Hella", "Lemförder", "KYB",
            "Textar", "SKF", "INA", "VDO", "Preiburg", "Behr",
            "Osram", "Champion", "Dayco", "Gates", "Beru",
            "Monroe", "ATE", "Zimmermann", "Bosal",
            "WIX Filters", "Lucas", "ACDelco", "Hitachi"
        ]

        self.cmburunmarka.addItems(markalar)

        # KATEGORİ
        self.label_7 = QtWidgets.QLabel("PARÇA KATEGORİSİ", self.leftFrame)
        self.label_7.setGeometry(180, 450, 170, 25)

        self.cmburunkategori = QtWidgets.QComboBox(self.leftFrame)
        self.cmburunkategori.setGeometry(180, 480, 140, 40)

        kategoriler = [
            "Motor Grubu",
            "Elektrik ve Elektronik",
            "Fren Sistemi",
            "Süspansiyon",
            "Şanzıman",
            "Soğutma Sistemi",
            "Kaporta",
            "İç Donanım",
            "Egzoz Sistemi",
            "Yakıt Sistemi"
        ]

        self.cmburunkategori.addItems(kategoriler)

        # =======================
        # SAĞ PANEL
        # =======================
        self.rightFrame = QtWidgets.QFrame(self.centralwidget)
        self.rightFrame.setGeometry(QtCore.QRect(400, 20, 780, 620))
        self.rightFrame.setStyleSheet("""
        QFrame{
            background-color:#262b33;
            border-radius:20px;
        }
        """)

        self.tableTitle = QtWidgets.QLabel(self.rightFrame)
        self.tableTitle.setGeometry(QtCore.QRect(20, 15, 400, 35))
        self.tableTitle.setText("📦 PARÇA LİSTESİ")
        self.tableTitle.setStyleSheet("""
        font-size:18pt;
        font-weight:bold;
        color:#00a8ff;
        """)

        # KATEGORİ FİLTRE
        self.label_8 = QtWidgets.QLabel("KATEGORİ FİLTRESİ", self.rightFrame)
        self.label_8.setGeometry(20, 70, 160, 25)

        self.cmbkategori = QtWidgets.QComboBox(self.rightFrame)
        self.cmbkategori.setGeometry(180, 65, 220, 40)
        self.cmbkategori.addItems(kategoriler)

        self.btnkategorilistele = QtWidgets.QPushButton("Listele", self.rightFrame)
        self.btnkategorilistele.setGeometry(420, 65, 120, 40)

        # TABLO
        self.tbllistetablo = QtWidgets.QTableWidget(self.rightFrame)
        self.tbllistetablo.setGeometry(QtCore.QRect(20, 120, 740, 350))
        self.tbllistetablo.setRowCount(30)
        self.tbllistetablo.setColumnCount(6)

        self.tbllistetablo.setHorizontalHeaderLabels([
            "Kod",
            "Parça Adı",
            "Fiyat",
            "Stok",
            "Marka",
            "Kategori"
        ])

        self.tbllistetablo.horizontalHeader().setStretchLastSection(True)
        self.tbllistetablo.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )

        # BUTONLAR
        self.btnekle = QtWidgets.QPushButton("➕ PARÇA EKLE", self.rightFrame)
        self.btnekle.setGeometry(20, 500, 170, 45)

        self.btnsil = QtWidgets.QPushButton("🗑 PARÇA SİL", self.rightFrame)
        self.btnsil.setGeometry(210, 500, 170, 45)

        self.btnguncelle = QtWidgets.QPushButton("✏ PARÇA GÜNCELLE", self.rightFrame)
        self.btnguncelle.setGeometry(400, 500, 190, 45)

        self.btnlistele = QtWidgets.QPushButton("📋 TÜMÜNÜ LİSTELE", self.rightFrame)
        self.btnlistele.setGeometry(610, 500, 150, 45)

        # ARAMA
        self.lneara = QtWidgets.QLineEdit(self.rightFrame)
        self.lneara.setGeometry(20, 560, 550, 40)
        self.lneara.setPlaceholderText("Parça ara...")

        self.btnara = QtWidgets.QPushButton("🔍 ARA", self.rightFrame)
        self.btnara.setGeometry(590, 560, 170, 40)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)