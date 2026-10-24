"""
GitHub Release Oluşturma ve Kurulum Paketini (setup.exe) Yükleme Betiği
(packaging/create_github_release.py)
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Windows console encoding uyumluluğu
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

KOK_DIZIN = Path(__file__).resolve().parent.parent
SETUP_EXE = KOK_DIZIN / "dist" / "installer" / "OtoYedekParca_Setup_v1.0.0.exe"
REPO = "Zeki-wq/Otomasyon"
TAG = "v1.0.0-rc1"


def get_token() -> str:
    """Git Credential Manager'dan kayıtlı GitHub token'ını çeker."""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        capture_output=True,
        text=True,
        check=True
    )
    creds = dict(line.split("=", 1) for line in p.stdout.splitlines() if "=" in line)
    token = creds.get("password")
    if not token:
        raise RuntimeError("GitHub kimlik bilgisi (token) bulunamadı!")
    return token


def file_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().upper()


def main():
    if not SETUP_EXE.exists():
        print(f"[-] HATA: Setup dosyası bulunamadı: {SETUP_EXE}")
        sys.exit(1)

    dosya_boyutu = SETUP_EXE.stat().st_size
    boyut_mb = dosya_boyutu / (1024 * 1024)
    sha256_hash = file_sha256(SETUP_EXE)

    print(f"[*] Kurulum dosyası: {SETUP_EXE.name} ({boyut_mb:.2f} MB)")
    print(f"[*] SHA-256 Hash   : {sha256_hash}")

    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "OtoYedekParca-Release-Tool"
    }

    # 1. Mevcut release kontrolü
    print(f"\n[*] '{TAG}' için GitHub Release kontrol ediliyor...")
    check_url = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
    req = urllib.request.Request(check_url, headers=headers)
    release = None
    try:
        with urllib.request.urlopen(req) as r:
            release = json.loads(r.read())
            print(f"  [+] Mevcut Release bulundu: ID {release['id']}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("  [*] Release henüz mevcut değil, yeni release oluşturuluyor...")
        else:
            raise

    # 2. Release oluştur (yoksa)
    if not release:
        create_url = f"https://api.github.com/repos/{REPO}/releases"
        body_text = (
            f"## Oto Yedek Parça Otomasyonu v1.0.0-rc1\n\n"
            f"Oto yedek parça satış ve dükkan yönetimi için geliştirilmiş, yüksek performanslı ve %100 çevrimdışı çalışabilen masaüstü otomasyon paketi.\n\n"
            f"### 📦 İndirme ve Kurulum Dosyası\n"
            f"- **Dosya:** `{SETUP_EXE.name}`\n"
            f"- **Boyut:** {boyut_mb:.2f} MB\n"
            f"- **SHA-256 Doğrulama Hash'i:** `{sha256_hash}`\n\n"
            f"### 🚀 Öne Çıkan Özellikler\n"
            f"- **PySide6 (Qt 6):** Modern koyu tema, WCAG uyumlu yüksek kontrast, 1366x768 ve High-DPI tam uyumu.\n"
            f"- **Temiz Veritabanı:** Kurulumda sıfır test verisi; otomatik ilk kurulum sihirbazı.\n"
            f"- **Veri Koruma:** Yeniden kurulum ve güncellemede veriler ASLA silinmez; şema yükseltmede otomatik yedek ve rollback koruması.\n"
            f"- **Hızlı Satış & Stok:** Barkod, OEM, parça kodu anlık arama, sepet yönetimi, veresiye cari hesap ve PDF fiş dökümü.\n"
            f"- **Güvenli Kaldırma:** Kaldırıcı veri silmez (etkileşimli modda varsayılan cevap Hayır'dır).\n"
            f"- **Fabrika Ayarlarına Dönüş:** Yönetici parolası + 'SIFIRLA' onayı ile güvenli sıfırlama.\n"
        )
        payload = {
            "tag_name": TAG,
            "target_commitish": "master",
            "name": f"Oto Yedek Parça Otomasyonu {TAG}",
            "body": body_text,
            "draft": False,
            "prerelease": True
        }
        create_req = urllib.request.Request(
            create_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(create_req) as r:
            release = json.loads(r.read())
            print(f"  [+] Yeni Release başarıyla oluşturuldu: ID {release['id']}")

    release_id = release["id"]
    upload_url_template = release.get("upload_url", "")
    upload_url = upload_url_template.split("{")[0]

    # 3. Mevcut asset kontrolü
    for existing_asset in release.get("assets", []):
        if existing_asset["name"] == SETUP_EXE.name:
            print(f"[*] Eski asset '{SETUP_EXE.name}' siliniyor (ID: {existing_asset['id']})...")
            del_url = f"https://api.github.com/repos/{REPO}/releases/assets/{existing_asset['id']}"
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            with urllib.request.urlopen(del_req) as del_r:
                pass
            print("  [+] Eski asset silindi.")

    # 4. Kurulum dosyasını (setup.exe) release'e yükle
    print(f"\n[*] '{SETUP_EXE.name}' GitHub Release'e yükleniyor ({boyut_mb:.2f} MB)...")
    target_upload_url = f"{upload_url}?name={urllib.parse.quote(SETUP_EXE.name)}"

    with open(SETUP_EXE, "rb") as f:
        file_data = f.read()

    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "Content-Length": str(len(file_data)),
        "User-Agent": "OtoYedekParca-Release-Tool"
    }

    upload_req = urllib.request.Request(target_upload_url, data=file_data, headers=upload_headers)
    with urllib.request.urlopen(upload_req) as r:
        asset_info = json.loads(r.read())

    print("\n" + "=" * 70)
    print("🎉 KURULUM PAKETİ GITHUB RELEASE'E BAŞARIYLA YÜKLENDİ!")
    print("=" * 70)
    print(f"  📌 Release Adı   : {release.get('name')}")
    print(f"  🏷️  Tag           : {release.get('tag_name')}")
    print(f"  📦 Asset Adı     : {asset_info.get('name')}")
    print(f"  📊 Boyut         : {asset_info.get('size') / (1024*1024):.2f} MB")
    print(f"  📥 İndirme Linki : {asset_info.get('browser_download_url')}")
    print(f"  🌐 Release Linki : {release.get('html_url')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
