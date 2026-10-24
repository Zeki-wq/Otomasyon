"""
Oto Yedek Parça Otomasyonu - Tek Komutlu Dağıtım ve Kurulum Paketi Üretim Betiği
(packaging/build_release.py)

Akış:
1. Testler (pytest -v --timeout=120)
2. PyInstaller --onedir Derlemesi (packaging/otoyedekparca.spec)
3. Paket Doğrulama ve Güvenlik Denetimi (packaging/dogrula_paket.py)
4. Kod İmzalama Kontrolü (varsa signtool, yoksa İMZASIZ uyarısı)
5. Inno Setup Derlemesi (ISCC.exe ile OtoYedekParca_Setup_v1.0.0.exe üretimi)
"""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Windows console encoding uyumluluğu (cp1254 / UTF-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

KOK_DIZIN = Path(__file__).resolve().parent.parent
SPEC_DOSYASI = KOK_DIZIN / "packaging" / "otoyedekparca.spec"
SETUP_ISS = KOK_DIZIN / "packaging" / "setup.iss"
DOGRU_SCRIPT = KOK_DIZIN / "packaging" / "dogrula_paket.py"
OUTPUT_DIR = KOK_DIZIN / "dist" / "installer"


def _dosya_sha256(dosya_yolu: Path) -> str:
    sha = hashlib.sha256()
    with open(dosya_yolu, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def bul_iscc() -> Path | None:
    """Sistemde Inno Setup Komut Satırı Derleyicisini (ISCC.exe) bulur."""
    adaylar = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]
    for aday in adaylar:
        if aday.exists():
            return aday

    # PATH içinde ara
    path_iscc = shutil.which("iscc")
    if path_iscc:
        return Path(path_iscc)

    return None


def main():
    print("=" * 70, flush=True)
    print("🚀 OTO YEDEK PARÇA OTOMASYONU - RESMİ SÜRÜM ÜRETİM SÜRECİ", flush=True)
    print("=" * 70, flush=True)

    # 1. ADIM: Testler
    print("\n[ADIM 1/5] Otomatik Testler Çalıştırılıyor (pytest)...", flush=True)
    test_komut = [sys.executable, "-m", "pytest", "-v", "--timeout=120"]
    test_sonuc = subprocess.run(test_komut, cwd=str(KOK_DIZIN))
    if test_sonuc.returncode != 0:
        print(f"\n[-] HATA: Testler başarısız oldu (Hata Kodu: {test_sonuc.returncode})! Dağıtım paketi üretimi durduruldu.", flush=True)
        sys.exit(1)
    print("  ✅ Tüm testler başarıyla geçti.", flush=True)

    # 2. ADIM: PyInstaller Onedir Derlemesi
    print("\n[ADIM 2/5] PyInstaller ile Bağımsız Paket Derleniyor...")
    build_komut = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_DOSYASI)
    ]
    build_sonuc = subprocess.run(build_komut, cwd=str(KOK_DIZIN))
    if build_sonuc.returncode != 0:
        print("\n[-] HATA: PyInstaller derlemesi başarısız oldu!")
        sys.exit(1)
    print("  ✅ PyInstaller derlemesi tamamlandı.")

    # 3. ADIM: Paket Temizlik ve Güvenlik Denetimi
    print("\n[ADIM 3/5] Paket Güvenlik ve Temizlik Doğrulaması Yapılıyor...")
    denetim_komut = [sys.executable, str(DOGRU_SCRIPT)]
    denetim_sonuc = subprocess.run(denetim_komut, cwd=str(KOK_DIZIN))
    if denetim_sonuc.returncode != 0:
        print("\n[-] HATA: Paket güvenlik denetiminden geçemedi!")
        sys.exit(1)
    print("  ✅ Paket denetimi onaylandı.")

    # 4. ADIM: Kod İmzalama Adımı
    print("\n[ADIM 4/5] Kod İmzalama Adımı...")
    cert_path = os.environ.get("CODESIGN_CERT_PATH")
    cert_pass = os.environ.get("CODESIGN_CERT_PASSWORD")
    exe_path = KOK_DIZIN / "dist" / "OtoYedekParca" / "OtoYedekParca.exe"

    if cert_path and Path(cert_path).exists():
        print(f"  [*] Sertifika tespit edildi: {cert_path}")
        signtool = shutil.which("signtool")
        if signtool:
            sign_cmd = [
                signtool, "sign", "/f", cert_path,
                "/p", cert_pass or "",
                "/tr", "http://timestamp.digicert.com",
                "/td", "sha256", "/fd", "sha256",
                str(exe_path)
            ]
            subprocess.run(sign_cmd, check=True)
            print("  ✅ OtoYedekParca.exe başarıyla imzalandı.")
        else:
            print("  ⚠️ signtool.exe bulunamadı, imzalama atlandı.")
    else:
        print("  ⚠️ UYARI: CODESIGN_CERT_PATH ortam değişkeni tanımlı değil.")
        print("  ⚠️ DİKKAT: İMZASIZ SÜRÜM ÜRETİLİYOR! Müşteriye sunulmadan önce sertifika ile imzalanmalıdır.")

    # 5. ADIM: Inno Setup ile Kurulum Paketi (setup.exe) Derleme
    print("\n[ADIM 5/5] Inno Setup ile Windows Kurulum Programı Derleniyor...")
    iscc_path = bul_iscc()
    if not iscc_path:
        print("  [-] HATA: Inno Setup derleyicisi (ISCC.exe) sistemde bulunamadı!")
        print("      Lütfen Inno Setup 6 kurunuz: winget install JRSoftware.InnoSetup")
        sys.exit(1)

    print(f"  [*] ISCC Derleyici: {iscc_path}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    iscc_komut = [str(iscc_path), str(SETUP_ISS)]
    iscc_sonuc = subprocess.run(iscc_komut, cwd=str(KOK_DIZIN))
    if iscc_sonuc.returncode != 0:
        print("\n[-] HATA: Inno Setup kurulum paketi derlemesi başarısız oldu!")
        sys.exit(1)

    # Üretilen setup.exe dosyasını doğrula
    setup_exe = OUTPUT_DIR / "OtoYedekParca_Setup_v1.0.0.exe"
    if not setup_exe.exists():
        print(f"\n[-] HATA: Kurulum dosyası üretilemedi: {setup_exe}")
        sys.exit(1)

    boyut_mb = setup_exe.stat().st_size / (1024 * 1024)
    sha256_hash = _dosya_sha256(setup_exe)

    print("\n" + "=" * 70)
    print("🎉 WINDOWS KURULUM PROGRAMI (SETUP.EXE) BAŞARIYLA ÜRETİLDİ!")
    print("=" * 70)
    print(f"  📁 Çıktı Dosyası : {setup_exe}")
    print(f"  📊 Dosya Boyutu  : {boyut_mb:.2f} MB")
    print(f"  🔒 SHA-256 Hash  : {sha256_hash}")
    print("=" * 70)


if __name__ == "__main__":
    main()
