
    
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *

from arayüz1 import Ui_MainWindow
from PyQt5.QtWidgets import QMessageBox
import sqlite3
import sqlite3

baglanti = sqlite3.connect("urunler12.db")
islem = baglanti.cursor()
baglanti.commit()

baglanti = sqlite3.connect("urunler12.db")
islem = baglanti.cursor()



baglanti.commit()

uygulama = QApplication(sys.argv)
pencere = QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(pencere)



from PyQt5.QtWidgets import QTableWidgetItem


def kayit_ekle():

    UrunAdi = ui.lneurunad.text()
    BirimFiyat = int(ui.lnebrmfiyat.text())
    StokMiktari = int(ui.lnestokmiktar.text())
    UrunAciklama = ui.lneurunAcklama.text()
    Marka = ui.cmburunmarka.currentText()
    Kategori = ui.cmbkategori.currentText()

    try:
        ekle = "insert into urun (urunAdi,birimFiyat,stokMiktari,urunAciklama,marka,kategori) values (?,?,?,?,?,?)"
        islem.execute(ekle,(UrunAdi,BirimFiyat,StokMiktari,UrunAciklama,Marka,Kategori))
        baglanti.commit()
        kayit_listele()
        ui.statusbar.showMessage("Kayıt Ekleme İşlemi Başarılı",10000)
    except Exception as error:
        ui.statusbar.showMessage("Kayıt Eklenemedi Hata Çıktı === "+str(error))



def kayit_listele():
    ui.tbllistetablo.clear()
    ui.tbllistetablo.setHorizontalHeaderLabels(("Ürün Adi","Birim Fiyatı","Stok Miktarı","Ürün Açıklama","Markası","Kategori"))
    ui.tbllistetablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    sorgu = "select * from urun"
    islem.execute(sorgu)

    for indexSatir, kayitNumarasi in enumerate(islem):
        for indexSutun, kayitSutun in enumerate(kayitNumarasi):
            ui.tbllistetablo.setItem(indexSatir,indexSutun,QTableWidgetItem(str(kayitSutun)))

 
def kategoriye_gore_listele():
    listelenecek_kategori = ui.cmbkategori.currentText()

    sorgu = "select * from urun where kategori = ?"
    islem.execute(sorgu,(listelenecek_kategori,))
    ui.tbllistetablo.clear()
    for indexSatir, kayitNumarasi in enumerate(islem):
        for indexSutun, kayitSutun in enumerate(kayitNumarasi):
            ui.tbllistetablo.setItem(indexSatir,indexSutun+1,QTableWidgetItem(str(kayitSutun)))


def kayit_sil():
    sil_mesaj = QMessageBox.question(pencere,"Silme Onayı","Silmek İstediğinizden Emin Misiniz ?",QMessageBox.Yes | QMessageBox.No)

    if sil_mesaj == QMessageBox.Yes:
        secilen_kayit = ui.tbllistetablo.selectedItems()
        silinecek_kayit = secilen_kayit[0].text()

        sorgu = "delete from urun where urunKodu = ?"
        try:
            islem.execute(sorgu,(silinecek_kayit,))
            baglanti.commit()
            ui.statusbar.showMessage("Kayıt Başarıyla Silindi")
            kayit_listele()
        except Exception as error:
            ui.statusbar.showMessage("Kayıt Silinirken Hata Çıktı === "+str(error))
    
    else:
        ui.statusbar.showMessage("Silme İşlemi İptal Edildi")
    

def kayit_guncelle():
    guncelle_mesaj = QMessageBox.question(pencere,"Güncelleme Onayı","Bu kaydı Güncellemek istediğinizden Emin Misiniz ?",QMessageBox.Yes | QMessageBox.No)

    if guncelle_mesaj == QMessageBox.Yes:
        try:
            UrunKodu = ui.lneurunkodu.text()
            UrunAdi = ui.lneurunad.text()
            BirimFiyati = ui.lnebrmfiyat.text()
            StokMiktari = ui.lnestokmiktar.text()
            UrunAciklama = ui.lneurunAcklama.text()
            Marka = ui.cmburunmarka.currentText()
            Kategori = ui.cmbkategori.currentText()

            if UrunAdi == "" and BirimFiyati == "" and StokMiktari == "" and UrunAciklama == "" and Marka == "":
                islem.execute("update urun set kategori = ? where urunKodu = ?",(Kategori,UrunKodu))

            elif UrunAdi == "" and BirimFiyati == "" and StokMiktari == "" and UrunAciklama == "" and Kategori == "":
                islem.execute("update urun set marka = ? where urunKodu = ?",(Marka,UrunKodu)) 

            elif UrunAdi == "" and BirimFiyati == "" and StokMiktari == "" and Marka == "" and Kategori == "":
                islem.execute("update urun set urunAciklama = ? where urunKodu = ?",(UrunAciklama,UrunKodu))
            elif UrunAdi == "" and BirimFiyati == "" and UrunAciklama == "" and Marka == "" and Kategori == "":
                islem.execute("update urun set stokMiktari = ? where urunKodu = ?",(StokMiktari,UrunKodu))
            elif UrunAdi == "" and StokMiktari == "" and UrunAciklama == "" and Marka == "" and Kategori == "":
                islem.execute("update urun set birimFiyat = ? where urunKodu = ?",(BirimFiyati,UrunKodu))
            elif BirimFiyati == "" and StokMiktari == "" and UrunAciklama == "" and Marka == "" and Kategori == "":
                islem.execute("update urun set urunAdi = ? where urunKodu = ?",(UrunAdi,UrunKodu))
            else:
                islem.execute("update urun set urunAdi = ?, birimFiyat = ? , stokMiktari = ?, urunAciklaması = ?, marka = ?, kategori = ? where urunKodu = ?",(UrunAdi,BirimFiyati,StokMiktari,UrunAciklama,Marka, Kategori,UrunKodu))
            baglanti.commit()
            kayit_listele()
            ui.statusbar.showMessage("Kayıt Başarıyla Güncellendi")
        except Exception as error:
            ui.statusbar.showMessage("Kayıt Güncellemede Hata Çıktı === "+str(error))
    else:
        ui.statusbar.showMessage("Güncelleme İptal Edildi")
        
        
        
        
def urun_ara():
    try:
        aranan_kod = ui.lneara.text()
        if aranan_kod:
            ui.tbllistetablo.clear()
            ui.tbllistetablo.setColumnCount(6)
            ui.tbllistetablo.setHorizontalHeaderLabels(
                [ "ürün adı", "birim fiyatı", "stok miktarı", "ürün açıklaması", "marka", "kategori"]
            )
            sorgu = "SELECT * FROM urun WHERE urunkodu = ?"
            islem.execute(sorgu, (aranan_kod,))
            for indexSatır, kayıtNumarası in enumerate(islem):
                for indexSutun, kayıtsutun in enumerate(kayıtNumarası):
                    ui.tbllistetablo.setItem(indexSatır, indexSutun, QTableWidgetItem(str(kayıtsutun)))
            ui.statusbar.showMessage("Arama tamamlandı.", 5000)
        else:
            ui.statusbar.showMessage("Lütfen ürün kodu girin.", 5000)
    except Exception as error:
        ui.statusbar.showMessage("Arama hatası: " + str(error), 5000)
        
        
        
        
def main():
    global pencere
    pencere.show()

    ui.btnekle.clicked.connect(kayit_ekle)
    ui.btnlistele.clicked.connect(kayit_listele)
    ui.btnkategorilistele.clicked.connect(kategoriye_gore_listele)
    ui.btnsil.clicked.connect(kayit_sil)
    ui.btnguncelle.clicked.connect(kayit_guncelle)
    ui.btnara.clicked.connect(urun_ara)
    uygulama.exec_()


if __name__ == "__main__":
    main()

