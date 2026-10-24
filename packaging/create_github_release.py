"""
GitHub Release Oluşturma ve Tüm Kurulum Paketlerini (Windows, Debian, Fedora RPM) Yükleme Betiği
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
DIST_INSTALLER = KOK_DIZIN / "dist" / "installer"
REPO = "Zeki-wq/Otomasyon"
TAG = "v1.0.0-rc1"

ASSET_FILES = [
    DIST_INSTALLER / "OtoYedekParca_Setup_v1.0.0.exe",
    DIST_INSTALLER / "otoyedekparca_1.0.0_all.deb",
    DIST_INSTALLER / "otoyedekparca-1.0.0-1.noarch.rpm",
    DIST_INSTALLER / "otoyedekparca-1.0.0-fedora-installer.tar.gz",
    DIST_INSTALLER / "otoyedekparca-1.0.0.tar.gz",
]


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
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "OtoYedekParca-Release-Tool"
    }

    # Dosya kontrolleri
    available_assets = []
    print("=" * 70)
    print("📦 YÜKLENECEK SÜRÜM DOSYALARI DENETLENİYOR")
    print("=" * 70)
    for asset_path in ASSET_FILES:
        if asset_path.exists():
            size_mb = asset_path.stat().st_size / (1024 * 1024)
            sha = file_sha256(asset_path)
            available_assets.append((asset_path, size_mb, sha))
            print(f"  [+] {asset_path.name:<45} : {size_mb:>6.2f} MB | SHA256: {sha[:16]}...")
        else:
            print(f"  [-] EKSİK: {asset_path.name}")

    if not available_assets:
        print("[-] HATA: Yüklenecek hiçbir paket bulunamadı!")
        sys.exit(1)

    # Release açıklama metni
    body_text = (
        f"## Oto Yedek Parça Otomasyonu v1.0.0\n\n"
        f"Oto yedek parça satış ve dükkan yönetimi için geliştirilmiş, yüksek performanslı ve %100 çevrimdışı çalışabilen masaüstü otomasyon paketi.\n\n"
        f"### 📦 İndirme ve Kurulum Paketleri\n\n"
        f"| Platform / Dağıtım | Paket Formatı | Dosya Adı | Boyut | Kurulum Komutu |\n"
        f"| :--- | :--- | :--- | :--- | :--- |\n"
        f"| **Windows 10/11 (64-bit)** | Setup Sihirbazı | `OtoYedekParca_Setup_v1.0.0.exe` | ~46.5 MB | Çift tıklayarak kurun |\n"
        f"| **Debian / Ubuntu / Mint** | Standart `.deb` | `otoyedekparca_1.0.0_all.deb` | ~0.07 MB | `sudo apt install ./otoyedekparca_1.0.0_all.deb` |\n"
        f"| **Fedora / RHEL / CentOS** | Resmi `.rpm` | `otoyedekparca-1.0.0-1.noarch.rpm` | ~0.07 MB | `sudo dnf install ./otoyedekparca-1.0.0-1.noarch.rpm` |\n"
        f"| **Fedora / RHEL Çevrimdışı** | Installer Tarball | `otoyedekparca-1.0.0-fedora-installer.tar.gz` | ~0.07 MB | `sudo ./install.sh` |\n"
        f"| **Fedora RPM Kaynak** | Source Tarball | `otoyedekparca-1.0.0.tar.gz` | ~0.07 MB | `rpmbuild -ba otoyedekparca.spec` |\n\n"
        f"### 🔐 Dosya Doğrulama Özetleri (SHA-256)\n"
    )
    for asset_path, size_mb, sha in available_assets:
        body_text += f"- **`{asset_path.name}`**:\n  `{sha}`\n"

    body_text += (
        f"\n### 🚀 Öne Çıkan Özellikler\n"
        f"- **PySide6 (Qt 6):** Modern koyu tema, WCAG uyumlu yüksek kontrast, 1366x768 ve High-DPI tam uyumu.\n"
        f"- **Temiz Veritabanı:** Kurulumda sıfır test verisi; otomatik ilk kurulum sihirbazı.\n"
        f"- **Veri Koruma:** Yeniden kurulum ve güncellemede veriler ASLA silinmez; şema yükseltmede otomatik yedek ve rollback koruması.\n"
        f"- **Çapraz Platform Yalıtımı:** Windows'ta `%APPDATA%\\OtoYedekParca`, Linux'ta `~/.otoyedekparca` altında tam yalıtımlı veri.\n"
        f"- **Hızlı Satış & Stok:** Barkod, OEM, parça kodu anlık arama, sepet yönetimi, veresiye cari hesap ve PDF fiş dökümü.\n"
        f"- **Güvenli Kaldırma:** Kaldırıcı müşteri veritabanını silmez.\n"
        f"- **Fabrika Ayarlarına Dönüş:** Yönetici parolası + 'SIFIRLA' onayı ile güvenli sıfırlama.\n"
    )

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

    # 2. Release oluştur veya güncelle (prerelease: False yaparak resmi sürüm yapıyoruz)
    if not release:
        create_url = f"https://api.github.com/repos/{REPO}/releases"
        payload = {
            "tag_name": TAG,
            "target_commitish": "master",
            "name": f"Oto Yedek Parça Otomasyonu {TAG}",
            "body": body_text,
            "draft": False,
            "prerelease": False
        }
        create_req = urllib.request.Request(
            create_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(create_req) as r:
            release = json.loads(r.read())
            print(f"  [+] Yeni Release oluşturuldu: ID {release['id']}")
    else:
        patch_url = f"https://api.github.com/repos/{REPO}/releases/{release['id']}"
        patch_payload = {
            "name": f"Oto Yedek Parça Otomasyonu {TAG}",
            "body": body_text,
            "prerelease": False
        }
        patch_req = urllib.request.Request(
            patch_url,
            data=json.dumps(patch_payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PATCH"
        )
        with urllib.request.urlopen(patch_req) as r:
            release = json.loads(r.read())
            print("  [+] Release açıklama metni ve durumu güncellendi (Official Release).")

    upload_url_template = release.get("upload_url", "")
    upload_url = upload_url_template.split("{")[0]

    existing_assets = {a["name"]: a["id"] for a in release.get("assets", [])}

    # 3. Dosyaları release'e yükle
    uploaded_assets_info = []
    print("\n" + "=" * 70)
    print("📤 TÜM PAKETLER GITHUB RELEASE'E YÜKLENİYOR")
    print("=" * 70)

    for asset_path, size_mb, sha in available_assets:
        fname = asset_path.name
        if fname in existing_assets:
            print(f"[*] Eski '{fname}' siliniyor (Asset ID: {existing_assets[fname]})...")
            del_url = f"https://api.github.com/repos/{REPO}/releases/assets/{existing_assets[fname]}"
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            with urllib.request.urlopen(del_req):
                pass
            print(f"  [+] Eski asset silindi: {fname}")

        print(f"[*] Yükleniyor: {fname} ({size_mb:.2f} MB)...")
        target_upload_url = f"{upload_url}?name={urllib.parse.quote(fname)}"
        with open(asset_path, "rb") as f:
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
            uploaded_assets_info.append(asset_info)
            print(f"  [✓] Yüklendi: {asset_info['name']} -> {asset_info['browser_download_url']}")

    print("\n" + "=" * 70)
    print("🎉 TÜM DOSYALAR GITHUB RELEASE'E BAŞARIYLA YÜKLENDİ!")
    print("=" * 70)
    print(f"  📌 Release Adı   : {release.get('name')}")
    print(f"  🏷️  Tag           : {release.get('tag_name')}")
    print(f"  🌐 Release Linki : {release.get('html_url')}")
    print("\n  📦 Yüklenen Paketler:")
    for a in uploaded_assets_info:
        mb = a.get("size", 0) / (1024 * 1024)
        print(f"     - {a.get('name')} ({mb:.2f} MB)")
        print(f"       İndirme: {a.get('browser_download_url')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
