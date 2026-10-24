"""
Kasa, Ciro, Satış Analizi, En Çok Satanlar ve Excel Veri Ekranı
"""

from datetime import date
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.domain.money import kurus_to_tl_str
from app.services.rapor_servisi import RaporServisi
from app.services.urun_servisi import UrunServisi
from app.utils.export import urunleri_excelden_ice_aktar, urunleri_excele_aktar


class RaporlarPage(QWidget):
    """Mali Raporlar, Kasa Takibi ve Excel Veri Yönetimi."""

    def __init__(self, rapor_servisi: RaporServisi, urun_servisi: UrunServisi, parent=None):
        super().__init__(parent)
        self.rapor_servisi = rapor_servisi
        self.urun_servisi = urun_servisi

        self.init_ui()
        self.kasa_raporunu_tazele()
        self.ciro_raporunu_tazele()
        self.en_cok_satanlari_tazele()

    def init_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(12)

        # Başlık
        ust_bar = QHBoxLayout()
        baslik = QLabel("📈 RAPORLAR, KASA VE EXCEL YÖNETİMİ")
        baslik.setObjectName("headerTitle")
        ust_bar.addWidget(baslik)
        ust_bar.addStretch()

        btn_yenile = QPushButton("🔄 Tüm Raporları Yenile")
        btn_yenile.setObjectName("btnSecondary")
        btn_yenile.clicked.connect(self.tum_raporlari_tazele)
        ust_bar.addWidget(btn_yenile)

        ana_layout.addLayout(ust_bar)

        self.tabs = QTabWidget()

        # ==========================================
        # SEKME 1: Günlük Kasa Raporu
        # ==========================================
        tab_kasa = QWidget()
        k_layout = QVBoxLayout(tab_kasa)
        k_layout.setContentsMargins(10, 15, 10, 10)
        k_layout.setSpacing(15)

        k_filtre = QHBoxLayout()
        k_filtre.addWidget(QLabel("Rapor Günü:"))
        self.dt_kasa = QDateEdit()
        self.dt_kasa.setCalendarPopup(True)
        self.dt_kasa.setDate(QtCore.QDate.currentDate())
        self.dt_kasa.dateChanged.connect(self.kasa_raporunu_tazele)
        k_filtre.addWidget(self.dt_kasa)
        k_filtre.addStretch()
        k_layout.addLayout(k_filtre)

        # Kasa Kartları
        kart_grid = QtWidgets.QGridLayout()
        kart_grid.setSpacing(12)

        self.kart_nakit_satis = self._istatistik_karti("NAKİT SATIŞLAR", "0,00 ₺", "#2ecc71")
        self.kart_kart_satis = self._istatistik_karti("KREDİ KARTI SATIŞLARI", "0,00 ₺", "#00a8ff")
        self.kart_veresiye = self._istatistik_karti("VERESİYE (CARİ) SATIŞLAR", "0,00 ₺", "#e1b12c")
        self.kart_toplam_ciro = self._istatistik_karti("GÜNLÜK TOPLAM CİRO", "0,00 ₺", "#9b59b6")

        self.kart_nakit_tahsilat = self._istatistik_karti("NAKİT TAHSİLAT", "0,00 ₺", "#27ae60")
        self.kart_kart_tahsilat = self._istatistik_karti("KARTLA TAHSİLAT", "0,00 ₺", "#0984e3")
        self.kart_net_nakit_kasa = self._istatistik_karti("NET FİZİKİ NAKİT GİRİŞİ", "0,00 ₺", "#e67e22")
        self.kart_toplam_tahsilat = self._istatistik_karti("GÜNLÜK TOPLAM NAKİT+KART", "0,00 ₺", "#2ed573")

        kart_grid.addWidget(self.kart_nakit_satis, 0, 0)
        kart_grid.addWidget(self.kart_kart_satis, 0, 1)
        kart_grid.addWidget(self.kart_veresiye, 0, 2)
        kart_grid.addWidget(self.kart_toplam_ciro, 0, 3)

        kart_grid.addWidget(self.kart_nakit_tahsilat, 1, 0)
        kart_grid.addWidget(self.kart_kart_tahsilat, 1, 1)
        kart_grid.addWidget(self.kart_net_nakit_kasa, 1, 2)
        kart_grid.addWidget(self.kart_toplam_tahsilat, 1, 3)

        k_layout.addLayout(kart_grid)
        k_layout.addStretch()

        self.tabs.addTab(tab_kasa, "💰 Günlük Kasa Özeti")

        # ==========================================
        # SEKME 2: Dönemsel Ciro ve Kâr Analizi
        # ==========================================
        tab_ciro = QWidget()
        c_layout = QVBoxLayout(tab_ciro)
        c_layout.setContentsMargins(10, 15, 10, 10)
        c_layout.setSpacing(15)

        c_filtre = QHBoxLayout()
        c_filtre.addWidget(QLabel("Dönem Başlangıç:"))
        self.dt_ciro_baslangic = QDateEdit()
        self.dt_ciro_baslangic.setCalendarPopup(True)
        self.dt_ciro_baslangic.setDate(QtCore.QDate.currentDate().addDays(-30))
        c_filtre.addWidget(self.dt_ciro_baslangic)

        c_filtre.addWidget(QLabel("Bitiş:"))
        self.dt_ciro_bitis = QDateEdit()
        self.dt_ciro_bitis.setCalendarPopup(True)
        self.dt_ciro_bitis.setDate(QtCore.QDate.currentDate())
        c_filtre.addWidget(self.dt_ciro_bitis)

        btn_c_hesapla = QPushButton("Analiz Et")
        btn_c_hesapla.clicked.connect(self.ciro_raporunu_tazele)
        c_filtre.addWidget(btn_c_hesapla)
        c_filtre.addStretch()
        c_layout.addLayout(c_filtre)

        ciro_grid = QtWidgets.QGridLayout()
        ciro_grid.setSpacing(12)

        self.kart_c_siparis = self._istatistik_karti("TAMAMLANAN SİPARİŞ", "0 Adet", "#00a8ff")
        self.kart_c_toplam_matrah = self._istatistik_karti("NET SATIŞ MATRAHI (KDV HARİÇ)", "0,00 ₺", "#00cec9")
        self.kart_c_maliyet = self._istatistik_karti("TOPLAM MALİYET TUTARI", "0,00 ₺", "#e1b12c")
        self.kart_c_brut_kar = self._istatistik_karti("TAHMİNİ BRÜT KÂR", "0,00 ₺", "#2ecc71")

        ciro_grid.addWidget(self.kart_c_siparis, 0, 0)
        ciro_grid.addWidget(self.kart_c_toplam_matrah, 0, 1)
        ciro_grid.addWidget(self.kart_c_maliyet, 0, 2)
        ciro_grid.addWidget(self.kart_c_brut_kar, 0, 3)

        c_layout.addLayout(ciro_grid)
        c_layout.addStretch()

        self.tabs.addTab(tab_ciro, "📊 Ciro ve Kâr Analizi")

        # ==========================================
        # SEKME 3: En Çok Satan Parçalar
        # ==========================================
        tab_top = QWidget()
        top_layout = QVBoxLayout(tab_top)
        top_layout.setContentsMargins(10, 15, 10, 10)

        self.tablo_top = QTableWidget()
        self.tablo_top.setColumnCount(4)
        self.tablo_top.setHorizontalHeaderLabels(["Sıra", "Parça Kodu", "Parça Adı", "Toplam Satılan Adet", "Toplam Ciro (₺)"])
        self.tablo_top.setAlternatingRowColors(True)
        self.tablo_top.horizontalHeader().setMinimumSectionSize(140)
        self.tablo_top.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo_top.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        top_layout.addWidget(self.tablo_top)

        self.tabs.addTab(tab_top, "🏆 En Çok Satan Parçalar")

        # ==========================================
        # SEKME 4: Excel İçe/Dışa Aktarma
        # ==========================================
        tab_excel = QWidget()
        e_layout = QVBoxLayout(tab_excel)
        e_layout.setContentsMargins(15, 20, 15, 15)
        e_layout.setSpacing(15)

        e_bilgi = QLabel(
            "<b>Toplu Ürün Yönetimi (Excel .xlsx):</b><br>"
            "Tüm depo envanterini tek tıkla Excel dosyasına aktarabilir veya "
            "hazır Excel tablonuzdaki binlerce ürünü otomatik olarak sisteme yükleyebilirsiniz."
        )
        e_bilgi.setStyleSheet("color: #dcdde1; font-size: 10.5pt; line-height: 140%;")
        e_layout.addWidget(e_bilgi)

        btn_box = QHBoxLayout()
        self.btn_excel_aktar = QPushButton("📤 Tüm Ürünleri Excel'e Aktar (.xlsx)")
        self.btn_excel_aktar.setObjectName("btnSuccess")
        self.btn_excel_aktar.setMinimumHeight(40)
        self.btn_excel_aktar.clicked.connect(self.excele_aktar)
        btn_box.addWidget(self.btn_excel_aktar)

        self.btn_excel_yukle = QPushButton("📥 Excel'den Toplu Ürün İçe Aktar (.xlsx)")
        self.btn_excel_yukle.setObjectName("btnWarning")
        self.btn_excel_yukle.setMinimumHeight(40)
        self.btn_excel_yukle.clicked.connect(self.excelden_yukle)
        btn_box.addWidget(self.btn_excel_yukle)

        e_layout.addLayout(btn_box)

        # İlerleme Çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        e_layout.addWidget(self.progress_bar)

        self.lbl_excel_sonuc = QLabel("")
        self.lbl_excel_sonuc.setStyleSheet("color: #00a8ff; font-weight: bold; font-size: 10pt;")
        e_layout.addWidget(self.lbl_excel_sonuc)

        e_layout.addStretch()

        self.tabs.addTab(tab_excel, "📑 Toplu Excel İçe/Dışa Aktar")

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

    def tum_raporlari_tazele(self):
        self.kasa_raporunu_tazele()
        self.ciro_raporunu_tazele()
        self.en_cok_satanlari_tazele()

    def kasa_raporunu_tazele(self):
        tarih_str = self.dt_kasa.date().toString("yyyy-MM-dd")
        ozet = self.rapor_servisi.gunluk_kasa_ozeti(tarih_str)

        self.kart_nakit_satis.lbl_deger.setText(kurus_to_tl_str(ozet["nakit_satis_kurus"]))
        self.kart_kart_satis.lbl_deger.setText(kurus_to_tl_str(ozet["kart_satis_kurus"]))
        self.kart_veresiye.lbl_deger.setText(kurus_to_tl_str(ozet["veresiye_satis_kurus"]))
        self.kart_toplam_ciro.lbl_deger.setText(kurus_to_tl_str(ozet["toplam_ciro_kurus"]))

        self.kart_nakit_tahsilat.lbl_deger.setText(kurus_to_tl_str(ozet["nakit_tahsilat_kurus"]))
        self.kart_kart_tahsilat.lbl_deger.setText(kurus_to_tl_str(ozet["kart_tahsilat_kurus"]))
        self.kart_net_nakit_kasa.lbl_deger.setText(kurus_to_tl_str(ozet["net_nakit_kasa_kurus"]))
        self.kart_toplam_tahsilat.lbl_deger.setText(kurus_to_tl_str(ozet["gunluk_toplam_tahsilat_kurus"]))

    def ciro_raporunu_tazele(self):
        b = self.dt_ciro_baslangic.date().toString("yyyy-MM-dd")
        e = self.dt_ciro_bitis.date().toString("yyyy-MM-dd")
        ozet = self.rapor_servisi.satis_raporu(b, e)

        self.kart_c_siparis.lbl_deger.setText(f"{ozet['tamamlanan_siparis']} Sipariş")
        self.kart_c_toplam_matrah.lbl_deger.setText(kurus_to_tl_str(ozet["toplam_matrah_kurus"]))
        self.kart_c_maliyet.lbl_deger.setText(kurus_to_tl_str(ozet["toplam_maliyet_kurus"]))
        self.kart_c_brut_kar.lbl_deger.setText(kurus_to_tl_str(ozet["brut_kar_kurus"]))

    def en_cok_satanlari_tazele(self):
        urunler = self.rapor_servisi.en_cok_satanlar(limit=50)
        self.tablo_top.setColumnCount(5)
        self.tablo_top.setHorizontalHeaderLabels(["Sıra", "Parça Kodu", "Parça Adı", "Toplam Satılan Adet", "Toplam Ciro (₺)"])
        self.tablo_top.setRowCount(0)

        for idx, u in enumerate(urunler, start=1):
            r_idx = idx - 1
            self.tablo_top.insertRow(r_idx)
            self.tablo_top.setItem(r_idx, 0, QTableWidgetItem(str(idx)))
            self.tablo_top.setItem(r_idx, 1, QTableWidgetItem(u.get("parca_kodu") or "-"))
            self.tablo_top.setItem(r_idx, 2, QTableWidgetItem(u.get("urun_adi") or "-"))
            self.tablo_top.setItem(r_idx, 3, QTableWidgetItem(str(u.get("toplam_adet") or 0)))
            self.tablo_top.setItem(r_idx, 4, QTableWidgetItem(kurus_to_tl_str(u.get("toplam_ciro_kurus") or 0)))

    def excele_aktar(self):
        dosya_adi, _ = QFileDialog.getSaveFileName(
            self,
            "Excel Dosyasını Kaydet",
            f"oto_yedek_parca_listesi_{date.today().strftime('%Y%m%d')}.xlsx",
            "Excel Dosyası (*.xlsx)"
        )
        if not dosya_adi:
            return

        try:
            urunler = self.urun_servisi.urun_ara(limit=100000)
            yol = urunleri_excele_aktar(urunler, Path(dosya_adi))
            QMessageBox.information(
                self,
                "Aktarma Başarılı",
                f"Toplam {len(urunler)} ürün başarıyla Excel dosyasına aktarıldı:\n{yol}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def excelden_yukle(self):
        dosya_adi, _ = QFileDialog.getOpenFileName(
            self,
            "İçe Aktarılacak Excel Dosyasını Seçin",
            "",
            "Excel Dosyası (*.xlsx)"
        )
        if not dosya_adi:
            return

        try:
            sonuc = urunleri_excelden_ice_aktar(Path(dosya_adi), self.urun_servisi)

            detay_mesaj = sonuc.mesaj
            if sonuc.hatali_satirlar:
                detay_mesaj += "\n\nAtlanan Hatalı Satırlar (İlk 5):"
                for h in sonuc.hatali_satirlar[:5]:
                    detay_mesaj += f"\n- Satır {h['satir']} ({h['kod']}): {h['hata']}"

            QMessageBox.information(self, "İçe Aktarma Tamamlandı", detay_mesaj)
            self.lbl_excel_sonuc.setText(sonuc.mesaj)
        except Exception as e:
            QMessageBox.critical(self, "İçe Aktarma Hatası", str(e))
