"""
Ana Uygulama Penceresi (Single MainWindow Architecture)
Kenar çubuğu gezintisi, sayfa yığını (QStackedWidget) ve tek event loop.
"""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME, APP_VERSION
from app.ui.pages.ayarlar_page import AyarlarPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.musteriler_page import MusterilerPage
from app.ui.pages.raporlar_page import RaporlarPage
from app.ui.pages.satis_page import SatisPage
from app.ui.pages.siparisler_page import SiparislerPage
from app.ui.pages.stok_page import StokPage
from app.ui.pages.urunler_page import UrunlerPage
from app.ui.theme import apply_theme


class MainWindow(QMainWindow):
    """Oto Yedek Parça Otomasyonu Ana Ekranı."""

    def __init__(
        self,
        urun_servisi,
        stok_servisi,
        satis_servisi,
        musteri_servisi,
        kimlik_servisi,
        yedek_servisi,
        rapor_servisi,
        aktif_kullanici,
        db_path=None
    ):
        super().__init__()
        self.urun_servisi = urun_servisi
        self.stok_servisi = stok_servisi
        self.satis_servisi = satis_servisi
        self.musteri_servisi = musteri_servisi
        self.kimlik_servisi = kimlik_servisi
        self.yedek_servisi = yedek_servisi
        self.rapor_servisi = rapor_servisi
        self.aktif_kullanici = aktif_kullanici
        self.db_path = db_path

        self.nav_butonlari = {}

        self.setWindowTitle(f"{APP_NAME} - v{APP_VERSION}")
        self.resize(1366, 768)
        self.setMinimumSize(1100, 680)

        self.init_ui()
        apply_theme(self)
        self.sayfa_degistir("dashboard")

    def init_ui(self):
        merkezi_widget = QWidget(self)
        self.setCentralWidget(merkezi_widget)
        ana_layout = QHBoxLayout(merkezi_widget)
        ana_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.setSpacing(0)

        # ==========================================
        # SOL MENÜ: Kenar Çubuğu (Sidebar)
        # ==========================================
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame#sidebarFrame {
                background-color: #1a1b21;
                border-right: 1px solid #2f3640;
                border-radius: 0px;
            }
        """)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(10, 15, 10, 15)
        s_layout.setSpacing(8)

        # Logo ve Marka
        marka_box = QHBoxLayout()
        logo_icon = QLabel("🚗")
        logo_icon.setStyleSheet("font-size: 20pt;")
        marka_box.addWidget(logo_icon)

        marka_metin = QVBoxLayout()
        lbl_m1 = QLabel("OTO YEDEK")
        lbl_m1.setStyleSheet("color: #00a8ff; font-weight: bold; font-size: 11pt; letter-spacing: 1px;")
        lbl_m2 = QLabel("PARÇA YÖNETİMİ")
        lbl_m2.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 9pt;")
        marka_metin.addWidget(lbl_m1)
        marka_metin.addWidget(lbl_m2)
        marka_box.addLayout(marka_metin)
        marka_box.addStretch()
        s_layout.addLayout(marka_box)

        cizgi = QFrame()
        cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet("color: #2f3640; margin: 10px 0;")
        s_layout.addWidget(cizgi)

        # Menü Butonları
        menuler = [
            ("dashboard", "🏠  Ana Panel"),
            ("satis", "🛒  Hızlı Satış"),
            ("urunler", "📦  Parça & Depo"),
            ("siparisler", "📋  Siparişler"),
            ("musteriler", "👥  Cari Müşteriler"),
            ("stok", "📊  Stok Hareketleri"),
            ("raporlar", "📈  Raporlar"),
            ("ayarlar", "⚙️  Sistem Ayarları")
        ]

        for anahtar, metin in menuler:
            btn = QPushButton(metin)
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #dcdde1;
                    text-align: left;
                    padding-left: 15px;
                    border-radius: 8px;
                    font-size: 10pt;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #262b33;
                    color: #00a8ff;
                }
                QPushButton#activeNav {
                    background-color: #00a8ff;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked, k=anahtar: self.sayfa_degistir(k))
            s_layout.addWidget(btn)
            self.nav_butonlari[anahtar] = btn

        s_layout.addStretch()

        # Kullanıcı Bilgisi ve Çıkış Kutusu
        user_card = QFrame()
        user_card.setStyleSheet("background-color: #262b33; border-radius: 8px; padding: 10px;")
        u_layout = QVBoxLayout(user_card)
        u_layout.setSpacing(4)

        u_ad = self.aktif_kullanici.ad_soyad if self.aktif_kullanici else "Kullanıcı"
        u_rol = "Yönetici" if self.aktif_kullanici and self.aktif_kullanici.rol == "yonetici" else "Personel"

        lbl_u_ad = QLabel(f"👤 {u_ad}")
        lbl_u_ad.setStyleSheet("font-weight: bold; color: #ffffff;")
        u_layout.addWidget(lbl_u_ad)

        lbl_u_rol = QLabel(f"Yetki: {u_rol}")
        lbl_u_rol.setStyleSheet("color: #a4b0be; font-size: 8.5pt;")
        u_layout.addWidget(lbl_u_rol)

        btn_cikis = QPushButton("Çıkış Yap")
        btn_cikis.setObjectName("btnSecondary")
        btn_cikis.setMinimumHeight(30)
        btn_cikis.setStyleSheet("font-size: 9pt; padding: 4px;")
        btn_cikis.clicked.connect(self.close)
        u_layout.addWidget(btn_cikis)

        s_layout.addWidget(user_card)
        ana_layout.addWidget(sidebar)

        # ==========================================
        # SAĞ ALAN: Sayfa Yığını (QStackedWidget)
        # ==========================================
        self.stack = QStackedWidget()

        # Sayfaları Oluştur
        self.page_dashboard = DashboardPage(self.rapor_servisi, self.stok_servisi, self.satis_servisi, nav_callback=self.sayfa_degistir)
        self.page_satis = SatisPage(self.satis_servisi, self.urun_servisi, self.musteri_servisi, self.aktif_kullanici)
        self.page_urunler = UrunlerPage(self.urun_servisi, self.stok_servisi, self.aktif_kullanici)
        self.page_siparisler = SiparislerPage(self.satis_servisi, self.musteri_servisi, self.aktif_kullanici)
        self.page_musteriler = MusterilerPage(self.musteri_servisi, self.aktif_kullanici)
        self.page_stok = StokPage(self.stok_servisi, self.urun_servisi)
        self.page_raporlar = RaporlarPage(self.rapor_servisi, self.urun_servisi)
        self.page_ayarlar = AyarlarPage(self.yedek_servisi, self.kimlik_servisi, self.db_path, self.aktif_kullanici)

        self.sayfa_haritasi = {
            "dashboard": self.page_dashboard,
            "satis": self.page_satis,
            "urunler": self.page_urunler,
            "siparisler": self.page_siparisler,
            "musteriler": self.page_musteriler,
            "stok": self.page_stok,
            "raporlar": self.page_raporlar,
            "ayarlar": self.page_ayarlar
        }

        for p in self.sayfa_haritasi.values():
            self.stack.addWidget(p)

        ana_layout.addWidget(self.stack, stretch=1)

        # Durum Çubuğu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Sistem Hazır  |  Veritabanı: WAL Modu (Aktif)  |  Kullanıcı: {u_ad} ({u_rol})")

    def sayfa_degistir(self, anahtar: str):
        if anahtar in self.sayfa_haritasi:
            # Buton stillerini güncelle
            for k, btn in self.nav_butonlari.items():
                if k == anahtar:
                    btn.setObjectName("activeNav")
                else:
                    btn.setObjectName("")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            hedef_sayfa = self.sayfa_haritasi[anahtar]
            self.stack.setCurrentWidget(hedef_sayfa)

            # Sayfa yenileme fonksiyonu varsa tetikle
            if hasattr(hedef_sayfa, "listeyi_guncelle"):
                hedef_sayfa.listeyi_guncelle()
            elif hasattr(hedef_sayfa, "verileri_tazele"):
                hedef_sayfa.verileri_tazele()
            elif hasattr(hedef_sayfa, "tum_raporlari_tazele"):
                hedef_sayfa.tum_raporlari_tazele()
