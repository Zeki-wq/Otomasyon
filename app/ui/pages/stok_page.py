"""
Stok Hareketleri, Envanter Değeri ve Kritik Stok Uyarı Ekranı
"""

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.domain.money import kurus_to_tl_str
from app.services.stok_servisi import StokServisi
from app.services.urun_servisi import UrunServisi


class StokPage(QWidget):
    """Stok Defteri, Kritik Stok Uyarıları ve Envanter Değer Ekranı."""

    def __init__(self, stok_servisi: StokServisi, urun_servisi: UrunServisi, parent=None):
        super().__init__(parent)
        self.stok_servisi = stok_servisi
        self.urun_servisi = urun_servisi

        self.init_ui()
        self.verileri_tazele()

    def init_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(12)

        # Üst Başlık ve Yenile Butonu
        ust_bar = QHBoxLayout()
        baslik = QLabel("📊 STOK HAREKETLERİ & ENVANTER ANALİZİ")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setObjectName("btnSecondary")
        btn_yenile.clicked.connect(self.verileri_tazele)
        ust_bar.addWidget(btn_yenile)

        ana_layout.addLayout(ust_bar)

        # 1. Envanter Özet İstatistik Kartları
        kart_layout = QHBoxLayout()
        kart_layout.setSpacing(12)

        # Kalem Sayısı Kartı
        self.kart_kalem = self._istatistik_karti("TOPLAM KALEM", "0 Kalem", "#00a8ff")
        kart_layout.addWidget(self.kart_kalem)

        # Toplam Adet Kartı
        self.kart_adet = self._istatistik_karti("DEPO STOK ADEDİ", "0 Adet", "#00cec9")
        kart_layout.addWidget(self.kart_adet)

        # Maliyet Değeri Kartı
        self.kart_maliyet = self._istatistik_karti("ENVANTER MALİYETİ", "0,00 ₺", "#e1b12c")
        kart_layout.addWidget(self.kart_maliyet)

        # Satış Değeri Kartı
        self.kart_satis = self._istatistik_karti("ENVANTER PERAKENDE DEĞERİ", "0,00 ₺", "#2ed573")
        kart_layout.addWidget(self.kart_satis)

        ana_layout.addLayout(kart_layout)

        # 2. Sekmeli Alan: Stok Hareket Defteri ve Kritik Stok Rozetleri
        self.tabs = QTabWidget()

        # Sekme 1: Stok Hareket Defteri
        tab_hareket = QWidget()
        h_layout = QVBoxLayout(tab_hareket)
        h_layout.setContentsMargins(5, 10, 5, 5)

        self.tablo_hareket = QTableWidget()
        self.tablo_hareket.setColumnCount(8)
        self.tablo_hareket.setHorizontalHeaderLabels([
            "ID", "Tarih", "Parça Kodu", "Ürün Adı",
            "Hareket Tipi", "Değişim (±)", "Önceki -> Sonraki", "Açıklama"
        ])
        self.tablo_hareket.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tablo_hareket.horizontalHeader().setMinimumSectionSize(65)
        h_widths = [50, 130, 110, 200, 100, 85, 120, 150]
        for col, w in enumerate(h_widths):
            self.tablo_hareket.setColumnWidth(col, w)
        h_layout.addWidget(self.tablo_hareket)

        self.tabs.addTab(tab_hareket, "📜 Stok Hareket Defteri (Denetim İzi)")

        # Sekme 2: Kritik Stok Seviyesindeki Ürünler
        tab_kritik = QWidget()
        k_layout = QVBoxLayout(tab_kritik)
        k_layout.setContentsMargins(5, 10, 5, 5)

        self.lbl_kritik_uyari = QLabel("⚠️ Aşağıdaki ürünler kritik stok seviyesine veya altına inmiştir!")
        self.lbl_kritik_uyari.setStyleSheet("color: #ff4757; font-weight: bold; font-size: 11pt; margin-bottom: 5px;")
        k_layout.addWidget(self.lbl_kritik_uyari)

        self.tablo_kritik = QTableWidget()
        self.tablo_kritik.setColumnCount(8)
        self.tablo_kritik.setHorizontalHeaderLabels([
            "ID", "Parça Kodu", "OEM No", "Ürün Adı",
            "Marka", "Raf Yeri", "Mevcut Stok", "Kritik Eşik"
        ])
        self.tablo_kritik.setAlternatingRowColors(True)
        self.tablo_kritik.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tablo_kritik.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tablo_kritik.horizontalHeader().setMinimumSectionSize(65)
        k_widths = [50, 110, 100, 220, 100, 80, 90, 85]
        for col, w in enumerate(k_widths):
            self.tablo_kritik.setColumnWidth(col, w)
        k_layout.addWidget(self.tablo_kritik)

        self.tabs.addTab(tab_kritik, "⚠️ Kritik Stok Uyarıları (Sipariş Verilmeli)")

        ana_layout.addWidget(self.tabs)

    def _istatistik_karti(self, baslik: str, varsayilan_deger: str, vurgu_renk: str) -> QFrame:
        kart = QFrame()
        kart.setObjectName("cardFrame")
        layout = QVBoxLayout(kart)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)

        lbl_baslik = QLabel(baslik)
        lbl_baslik.setObjectName("statLabel")
        layout.addWidget(lbl_baslik)

        lbl_deger = QLabel(varsayilan_deger)
        lbl_deger.setObjectName("statValue")
        lbl_deger.setStyleSheet(f"color: {vurgu_renk};")
        layout.addWidget(lbl_deger)

        kart.lbl_deger = lbl_deger
        return kart

    def verileri_tazele(self):
        # 1. Envanter Özetini Doldur
        ozet = self.stok_servisi.toplam_stok_degeri()
        self.kart_kalem.lbl_deger.setText(f"{ozet['toplam_kalem']} Kalem")
        self.kart_adet.lbl_deger.setText(f"{ozet['toplam_adet']} Adet")
        self.kart_maliyet.lbl_deger.setText(kurus_to_tl_str(ozet["maliyet_kurus"]))
        self.kart_satis.lbl_deger.setText(kurus_to_tl_str(ozet["satis_kurus"]))

        # 2. Stok Hareketlerini Doldur
        hareketler = self.stok_servisi.stok_hareketlerini_getir(limit=200)
        self.tablo_hareket.setRowCount(0)

        for r_idx, h in enumerate(hareketler):
            self.tablo_hareket.insertRow(r_idx)
            self.tablo_hareket.setItem(r_idx, 0, QTableWidgetItem(str(h.id)))
            self.tablo_hareket.setItem(r_idx, 1, QTableWidgetItem(str(h.tarih)))
            self.tablo_hareket.setItem(r_idx, 2, QTableWidgetItem(h.parca_kodu))
            self.tablo_hareket.setItem(r_idx, 3, QTableWidgetItem(h.urun_adi))

            tip_item = QTableWidgetItem(h.hareket_tipi.upper())
            degisim_item = QTableWidgetItem(f"{'+' if h.adet_degisim > 0 else ''}{h.adet_degisim}")

            if h.adet_degisim > 0:
                degisim_item.setForeground(QtGui.QColor("#2ecc71"))
            else:
                degisim_item.setForeground(QtGui.QColor("#e74c3c"))

            self.tablo_hareket.setItem(r_idx, 4, tip_item)
            self.tablo_hareket.setItem(r_idx, 5, degisim_item)
            self.tablo_hareket.setItem(r_idx, 6, QTableWidgetItem(f"{h.onceki_stok} ➔ {h.sonraki_stok}"))
            self.tablo_hareket.setItem(r_idx, 7, QTableWidgetItem(h.aciklama))

        # 3. Kritik Stok Tablosunu Doldur
        kritik_urunler = self.stok_servisi.kritik_stok_urunleri_getir()
        self.tablo_kritik.setRowCount(0)

        for r_idx, u in enumerate(kritik_urunler):
            self.tablo_kritik.insertRow(r_idx)
            self.tablo_kritik.setItem(r_idx, 0, QTableWidgetItem(str(u.id)))
            self.tablo_kritik.setItem(r_idx, 1, QTableWidgetItem(u.parca_kodu))
            self.tablo_kritik.setItem(r_idx, 2, QTableWidgetItem(u.oem_no))
            self.tablo_kritik.setItem(r_idx, 3, QTableWidgetItem(u.ad))
            self.tablo_kritik.setItem(r_idx, 4, QTableWidgetItem(u.marka_adi))
            self.tablo_kritik.setItem(r_idx, 5, QTableWidgetItem(u.raf_yeri))

            stok_item = QTableWidgetItem(str(u.stok))
            stok_item.setForeground(QtGui.QColor("#ff4757"))
            stok_item.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
            self.tablo_kritik.setItem(r_idx, 6, stok_item)

            self.tablo_kritik.setItem(r_idx, 7, QTableWidgetItem(str(u.kritik_stok)))

        self.tabs.setTabText(1, f"⚠️ Kritik Stok Uyarıları ({len(kritik_urunler)} Ürün)")
