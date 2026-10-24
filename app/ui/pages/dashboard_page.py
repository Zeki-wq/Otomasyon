"""
Ana Panel (Dashboard) - Özet İstatistikler ve Hızlı Kısayollar
"""

from datetime import date

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.domain.money import kurus_to_tl_str
from app.services.rapor_servisi import RaporServisi
from app.services.satis_servisi import SatisServisi
from app.services.stok_servisi import StokServisi


class DashboardPage(QWidget):
    """Ana Panel: Günlük durum, kritik uyarılar ve son siparişler."""

    def __init__(
        self,
        rapor_servisi: RaporServisi,
        stok_servisi: StokServisi,
        satis_servisi: SatisServisi,
        nav_callback=None,
        parent=None
    ):
        super().__init__(parent)
        self.rapor_servisi = rapor_servisi
        self.stok_servisi = stok_servisi
        self.satis_servisi = satis_servisi
        self.nav_callback = nav_callback

        self.init_ui()
        self.verileri_tazele()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Karşılama Başlığı
        ust_bar = QHBoxLayout()
        baslik = QLabel("🏠 GÜNLÜK DÜKKAN ÖZETİ")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        self.lbl_tarih = QLabel(f"Bugün: {date.today().strftime('%d.%m.%Y')}")
        self.lbl_tarih.setStyleSheet("color: #a4b0be; font-size: 11pt; font-weight: bold;")
        ust_bar.addWidget(self.lbl_tarih)

        layout.addLayout(ust_bar)

        # 1. Büyük İstatistik Kartları
        kart_grid = QtWidgets.QGridLayout()
        kart_grid.setSpacing(12)

        self.kart_ciro = self._kart("BUGÜNKÜ CİRO", "0,00 ₺", "#2ecc71")
        self.kart_siparis = self._kart("BUGÜNKÜ SİPARİŞ", "0 Adet", "#00a8ff")
        self.kart_kritik = self._kart("KRİTİK STOK UYARISI", "0 Ürün", "#ff4757")
        self.kart_envanter = self._kart("ENVANTER MALİYETİ", "0,00 ₺", "#e1b12c")

        kart_grid.addWidget(self.kart_ciro, 0, 0)
        kart_grid.addWidget(self.kart_siparis, 0, 1)
        kart_grid.addWidget(self.kart_kritik, 0, 2)
        kart_grid.addWidget(self.kart_envanter, 0, 3)

        layout.addLayout(kart_grid)

        # 2. Hızlı Kısayol Butonları
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        btn_hizli_satis = QPushButton("🛒 Yeni Hızlı Satış Aç")
        btn_hizli_satis.setObjectName("btnSuccess")
        btn_hizli_satis.setFixedHeight(40)
        btn_hizli_satis.clicked.connect(lambda: self.nav_callback and self.nav_callback("satis"))
        btn_bar.addWidget(btn_hizli_satis)

        btn_yeni_urun = QPushButton("➕ Yeni Parça Ekle")
        btn_yeni_urun.setFixedHeight(40)
        btn_yeni_urun.clicked.connect(lambda: self.nav_callback and self.nav_callback("urunler"))
        btn_bar.addWidget(btn_yeni_urun)

        btn_tahsilat = QPushButton("💵 Tahsilat / Cari İşlem")
        btn_tahsilat.setObjectName("btnWarning")
        btn_tahsilat.setFixedHeight(40)
        btn_tahsilat.clicked.connect(lambda: self.nav_callback and self.nav_callback("musteriler"))
        btn_bar.addWidget(btn_tahsilat)

        layout.addLayout(btn_bar)

        # 3. Son Siparişler Tablosu
        layout.addWidget(QLabel("<b>Son Yapılan Satışlar:</b>"))
        self.tablo_son_siparis = QTableWidget()
        self.tablo_son_siparis.setColumnCount(6)
        self.tablo_son_siparis.setHorizontalHeaderLabels([
            "Sipariş No", "Tarih / Saat", "Müşteri", "Ödeme Tipi", "Tutar (₺)", "Durum"
        ])
        self.tablo_son_siparis.setAlternatingRowColors(True)
        self.tablo_son_siparis.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo_son_siparis.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tablo_son_siparis.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tablo_son_siparis)

    def _kart(self, baslik: str, deger: str, renk: str) -> QFrame:
        kart = QFrame()
        kart.setObjectName("cardFrame")
        k_layout = QVBoxLayout(kart)
        k_layout.setContentsMargins(15, 12, 15, 12)
        k_layout.setSpacing(4)

        lbl_b = QLabel(baslik)
        lbl_b.setObjectName("statLabel")
        k_layout.addWidget(lbl_b)

        lbl_d = QLabel(deger)
        lbl_d.setObjectName("statValue")
        lbl_d.setStyleSheet(f"color: {renk}; font-size: 18pt;")
        k_layout.addWidget(lbl_d)

        kart.lbl_d = lbl_d
        return kart

    def verileri_tazele(self):
        bugun_str = date.today().strftime("%Y-%m-%d")
        kasa = self.rapor_servisi.gunluk_kasa_ozeti(bugun_str)
        stok_ozet = self.stok_servisi.toplam_stok_degeri()
        kritik_sayisi = self.stok_servisi.kritik_stok_sayisi()

        self.kart_ciro.lbl_d.setText(kurus_to_tl_str(kasa["toplam_ciro_kurus"]))
        self.kart_siparis.lbl_d.setText(f"{kasa['toplam_siparis_adedi']} Sipariş")
        self.kart_kritik.lbl_d.setText(f"{kritik_sayisi} Ürün")
        self.kart_envanter.lbl_d.setText(kurus_to_tl_str(stok_ozet["maliyet_kurus"]))

        # Son 10 siparişi listele
        siparisler = self.satis_servisi.siparisleri_getir(limit=10)
        self.tablo_son_siparis.setRowCount(0)
        for idx, s in enumerate(siparisler):
            self.tablo_son_siparis.insertRow(idx)
            self.tablo_son_siparis.setItem(idx, 0, QTableWidgetItem(s.siparis_no))
            self.tablo_son_siparis.setItem(idx, 1, QTableWidgetItem(str(s.tarih)))
            self.tablo_son_siparis.setItem(idx, 2, QTableWidgetItem(s.musteri_adi))
            self.tablo_son_siparis.setItem(idx, 3, QTableWidgetItem(s.odeme_tipi.upper()))
            self.tablo_son_siparis.setItem(idx, 4, QTableWidgetItem(kurus_to_tl_str(s.genel_toplam_kurus)))

            durum_item = QTableWidgetItem(s.durum.upper())
            if s.durum == "tamamlandi":
                durum_item.setForeground(QtGui.QColor("#2ecc71"))
            else:
                durum_item.setForeground(QtGui.QColor("#ff4757"))
            self.tablo_son_siparis.setItem(idx, 5, durum_item)
