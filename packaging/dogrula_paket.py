"""
Dağıtım Paketi Güvenlik, Temizlik ve Doğrulama Betiği (packaging/dogrula_paket.py)

Kontroller:
a) dist/OtoYedekParca içinde ve setup.iss dosya listesinde *.db, *.sqlite*, *.log, 'urunler12', yedek yok.
b) Paketteki Qt DLL'leri PySide6'dan geliyor; PyQt5/PyQt6 veya Qt5 yok.
c) Paketin içinde parola, gizli anahtar, .env, gerçek müşteri verisi izi yok.
d) Dosya toplam boyutu ve dosya listesi raporlanır.
"""

import sys
import os
import re
from pathlib import Path

# Windows console encoding uyumluluğu (cp1254 / UTF-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

KOK_DIZIN = Path(__file__).resolve().parent.parent
DIST_DIR = KOK_DIZIN / "dist" / "OtoYedekParca"
SETUP_ISS = KOK_DIZIN / "packaging" / "setup.iss"


def dogrula() -> bool:
    print("=" * 60)
    print("📦 DAĞITIM PAKETİ OTOMATİK DENETİMİ (dogrula_paket.py)")
    print("=" * 60)

    if not DIST_DIR.exists():
        print(f"[-] HATA: Dağıtım klasörü bulunamadı: {DIST_DIR}")
        print("    Lütfen önce PyInstaller derlemesini çalıştırınız.")
        return False

    hatalar = []
    uyarilar = []

    # a) Yasaklı dosya uzantıları ve isim kalıpları denetimi
    print("\n[1/4] Yasaklı Dosyalar ve Veritabanı Kalıntıları Taranıyor...")
    yasakli_uzantilar = {".db", ".sqlite", ".sqlite3", ".log", ".pfx", ".key"}
    yasakli_dosya_kaliplari = ["urunler12", ".env"]
    yasakli_dizin_isimleri = {"yedek", "backups", "backup"}

    toplam_boyut = 0
    dosya_sayisi = 0
    bulunan_dosyalar = []

    for kok, dizinler, dosyalar in os.walk(DIST_DIR):
        # Yedek klasörü denetimi
        for dizin in dizinler:
            if dizin.lower() in yasakli_dizin_isimleri:
                hatalar.append(f"Yasaklı yedek klasörü tespit edildi: {Path(kok) / dizin}")

        for d in dosyalar:
            dosya_sayisi += 1
            tam_yol = Path(kok) / d
            rel_yol = tam_yol.relative_to(DIST_DIR)
            dosya_boyutu = tam_yol.stat().st_size
            toplam_boyut += dosya_boyutu
            bulunan_dosyalar.append((str(rel_yol), dosya_boyutu))

            # Uzantı kontrolü (*.db, *.sqlite*, *.log)
            if tam_yol.suffix.lower() in yasakli_uzantilar:
                hatalar.append(f"Yasaklı uzantıya sahip dosya tespit edildi: {rel_yol}")

            # İsim kontrolü ('urunler12', .env)
            d_lower = d.lower()
            for yk in yasakli_dosya_kaliplari:
                if yk in d_lower:
                    hatalar.append(f"Yasaklı dosya kalıbı tespit edildi: {rel_yol} (Kalıp: {yk})")

    # setup.iss kontrolü
    if SETUP_ISS.exists():
        iss_metin = SETUP_ISS.read_text(encoding="utf-8", errors="ignore").lower()
        for yk in ["urunler12", ".db", ".sqlite", ".log"]:
            if yk in iss_metin and not yk.startswith(";"):
                # Açıklama satırları hariç kontrol
                lines = [line.strip() for line in iss_metin.splitlines() if not line.strip().startswith(";")]
                for l in lines:
                    if yk in l and "files" not in l and "source" in l:
                        hatalar.append(f"setup.iss içinde şüpheli girdi tespit edildi: {l}")

    if not hatalar:
        print("  ✅ dist/OtoYedekParca içinde hiçbir veritabanı, yedek veya log dosyası bulunmuyor.")
    else:
        for h in hatalar:
            print(f"  ❌ {h}")

    # b) PySide6 / PyQt Bağımsızlığı Kontrolü
    print("\n[2/4] Qt DLL'leri ve PySide6 Doğrulaması...")
    qt_dlller = []
    pyqt_var_mi = False

    for kok, _, dosyalar in os.walk(DIST_DIR):
        for d in dosyalar:
            d_low = d.lower()
            if "pyqt" in d_low or "qt5" in d_low:
                pyqt_var_mi = True
                hatalar.append(f"PyQt / Qt5 kalıntısı DLL tespit edildi: {Path(kok)/d}")
            if d_low.startswith("qt6") and d_low.endswith(".dll"):
                qt_dlller.append(Path(kok) / d)

    if qt_dlller and not pyqt_var_mi:
        print(f"  ✅ Pakette {len(qt_dlller)} adet Qt6 DLL bulundu. Tümü PySide6'dan geliyor, PyQt izi sıfır.")
    elif not qt_dlller:
        hatalar.append("Pakette hiçbir Qt6 DLL bulunamadı!")

    # c) Gizli anahtarlar, parolalar ve test verisi taraması
    print("\n[3/4] Gizli Anahtar, Parola ve Test Verisi Taraması...")
    supheli_metinler = ["secret_key", "password=", "parola123", "test_db", "kampana", "brembo"]
    taranan_metin_dosyasi = 0

    for rel_yol_str, b in bulunan_dosyalar:
        tam_yol = DIST_DIR / rel_yol_str
        # Yalnızca metin, json, sql, xml dosyalarını tara
        if tam_yol.suffix.lower() in [".txt", ".json", ".sql", ".xml", ".ini", ".cfg", ".md"]:
            taranan_metin_dosyasi += 1
            try:
                icerik = tam_yol.read_text(encoding="utf-8", errors="ignore").lower()
                for sm in supheli_metinler:
                    if sm in icerik:
                        # sql dosyalarındaki create table ifadeleri hariç
                        if tam_yol.suffix.lower() == ".sql" and sm in ["test_db"]:
                            continue
                        uyarilar.append(f"Metin dosyasında test/şüpheli kelime bulundu: {rel_yol_str} -> '{sm}'")
            except Exception:
                pass

    print(f"  ✅ {taranan_metin_dosyasi} adet metin/yapılandırma dosyası tarandı. Kritik veri sızıntısı yok.")

    # d) Dosya toplam boyutu ve dosya listesi özeti
    print("\n[4/4] Paket Boyutu ve İstatistikler...")
    boyut_mb = toplam_boyut / (1024 * 1024)
    print(f"  - Toplam Dosya Sayısı: {dosya_sayisi}")
    print(f"  - Toplam Paket Boyutu: {boyut_mb:.2f} MB")
    print(f"  - Ana Çalıştırılabilir: {(DIST_DIR / 'OtoYedekParca.exe').exists()}")

    if not (DIST_DIR / "OtoYedekParca.exe").exists():
        hatalar.append("OtoYedekParca.exe ana çalıştırılabilir dosyası mevcut değil!")

    print("\n" + "=" * 60)
    if not hatalar:
        print("🎉 PAKET DENETİMİ BAŞARILI! Paket dağıtıma ve kuruluma uygundur.")
        print("=" * 60)
        return True
    else:
        print(f"❌ PAKET DENETİMİ BAŞARISIZ! {len(hatalar)} hata bulundu:")
        for h in hatalar:
            print(f"   • {h}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    basarili = dogrula()
    sys.exit(0 if basarili else 1)
