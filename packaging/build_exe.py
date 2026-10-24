"""
PyInstaller Otomatik Derleme Betiği
Windows üzerinde tek tıkla çalıştırılabilir paket üretir.
"""

import sys
import subprocess
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent


def build():
    spec_dosyasi = KOK_DIZIN / "packaging" / "otoyedekparca.spec"
    print(f"[*] PyInstaller paketi derleniyor: {spec_dosyasi}")

    komut = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_dosyasi)
    ]

    sonuc = subprocess.run(komut, cwd=str(KOK_DIZIN))
    if sonuc.returncode == 0:
        print("\n[+] Derleme Başarılı!")
        print(f"Çıktı klasörü: {KOK_DIZIN / 'dist' / 'OtoYedekParca'}")
        print("Çalıştırılabilir dosya: OtoYedekParca.exe")
    else:
        print(f"\n[-] Derleme hatası! Hata kodu: {sonuc.returncode}")
        sys.exit(sonuc.returncode)


if __name__ == "__main__":
    build()
