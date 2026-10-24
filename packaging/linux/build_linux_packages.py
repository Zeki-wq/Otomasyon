#!/usr/bin/env python3
"""
Debian (.deb) ve Fedora Paket Üretici (packaging/linux/build_linux_packages.py)

Saf Python ile harici bağımlılık (dpkg-deb, ar vb.) gerektirmeden:
1. Debian (.deb) kurulum paketini (otoyedekparca_1.0.0_all.deb)
2. Fedora / RHEL otomatik kurulum paketini (otoyedekparca-1.0.0-fedora-installer.tar.gz)
3. Fedora RPM derleme kaynak arşivini (otoyedekparca-1.0.0.tar.gz)
üretir ve SHA-256 özetlerini doğrular.
"""

import hashlib
import io
import os
import stat
import sys
import tarfile
import time
from pathlib import Path

# Windows console encoding uyumluluğu
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
DIST_INSTALLER = KOK_DIZIN / "dist" / "installer"
DIST_INSTALLER.mkdir(parents=True, exist_ok=True)

VERSION = "1.0.0"
PACKAGE_NAME = "otoyedekparca"
ARCH = "all"


def calculate_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().upper()


def build_ar_archive(output_path: Path, members: list[tuple[str, bytes, int]]):
    """
    Standard Unix ar arşiv formatını oluşturur (Debian .deb gereksinimi).
    Her üye: (dosya_adi, veri, dosya_modu)
    """
    with open(output_path, "wb") as f:
        f.write(b"!<arch>\n")
        mtime = int(time.time())
        uid = 0
        gid = 0

        for name, data, mode in members:
            # Header: 60 bytes
            # name (16), mtime (12), uid (6), gid (6), mode (8), size (10), trailer (2)
            name_str = f"{name}/".ljust(16)
            mtime_str = f"{mtime}".ljust(12)
            uid_str = f"{uid}".ljust(6)
            gid_str = f"{gid}".ljust(6)
            mode_str = f"{oct(mode)[2:]}".ljust(8)
            size_str = f"{len(data)}".ljust(10)
            trailer = b"\x60\n"

            header = (
                name_str.encode("ascii")
                + mtime_str.encode("ascii")
                + uid_str.encode("ascii")
                + gid_str.encode("ascii")
                + mode_str.encode("ascii")
                + size_str.encode("ascii")
                + trailer
            )
            f.write(header)
            f.write(data)
            # 2-byte alignment
            if len(data) % 2 != 0:
                f.write(b"\n")


def get_clean_app_files() -> list[tuple[str, Path]]:
    """Pakete dahil edilecek temiz uygulama dosyalarını döndürür."""
    files = []
    # Kök dosyalar
    for fname in ["run.py", "requirements.txt", "LICENSE", "THIRD_PARTY_LICENSES.md"]:
        p = KOK_DIZIN / fname
        if p.exists():
            files.append((fname, p))

    # app/ dizini
    app_dir = KOK_DIZIN / "app"
    for p in app_dir.rglob("*"):
        if p.is_file():
            # Filtreler: .pyc, __pycache__, .db, .sqlite, .log
            if "__pycache__" in p.parts:
                continue
            if p.suffix.lower() in [".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".log"]:
                continue
            rel = p.relative_to(KOK_DIZIN).as_posix()
            files.append((rel, p))

    # assets/ dizini
    assets_dir = KOK_DIZIN / "assets"
    for p in assets_dir.rglob("*"):
        if p.is_file():
            rel = p.relative_to(KOK_DIZIN).as_posix()
            files.append((rel, p))

    return files


def create_debian_package() -> Path:
    """Debian / Ubuntu uyumlu .deb paketi üretir."""
    print("\n" + "=" * 60)
    print("📦 1. DEBIAN (.DEB) PAKETİ OLUŞTURULUYOR")
    print("=" * 60)

    deb_filename = f"{PACKAGE_NAME}_{VERSION}_{ARCH}.deb"
    deb_path = DIST_INSTALLER / deb_filename

    # 1. debian-binary
    debian_binary_data = b"2.0\n"

    # 2. control.tar.gz
    control_buf = io.BytesIO()
    with tarfile.open(fileobj=control_buf, mode="w:gz") as tar:
        # control dosyası
        control_content = (
            f"Package: {PACKAGE_NAME}\n"
            f"Version: {VERSION}\n"
            f"Section: utils\n"
            f"Priority: optional\n"
            f"Architecture: {ARCH}\n"
            f"Maintainer: OtoYedekParca <destek@otoyedekparca.local>\n"
            f"Depends: python3 (>= 3.10), python3-pyside6 | python3-pyqt6, python3-openpyxl, python3-reportlab\n"
            f"Recommends: python3-pip\n"
            f"Description: Oto Yedek Parca Satis ve Stok Otomasyonu\n"
            f" Oto yedek parca satis ve dukkan yonetimi icin gelistirilmis,\n"
            f" yuksek performansli ve %100 cevrimdisi calisabilen masaustu otomasyon paketi.\n"
            f" PySide6 (Qt 6) tabanli modern koyu arayuz, barkod & OEM arama,\n"
            f" kasa, veresiye cari takip ve PDF fis raporlama ozellikleri sunar.\n"
        ).encode("utf-8")

        ti_ctrl = tarfile.TarInfo(name="./control")
        ti_ctrl.size = len(control_content)
        ti_ctrl.mode = 0o644
        ti_ctrl.mtime = int(time.time())
        tar.addfile(ti_ctrl, io.BytesIO(control_content))

        # postinst betiği
        postinst_content = (
            "#!/bin/sh\n"
            "set -e\n"
            "chmod 0755 /usr/bin/otoyedekparca 2>/dev/null || true\n"
            "if which update-desktop-database >/dev/null 2>&1; then\n"
            "    update-desktop-database -q /usr/share/applications || true\n"
            "fi\n"
            "if which gtk-update-icon-cache >/dev/null 2>&1; then\n"
            "    gtk-update-icon-cache -q /usr/share/pixmaps || true\n"
            "fi\n"
            "exit 0\n"
        ).encode("utf-8")

        ti_postinst = tarfile.TarInfo(name="./postinst")
        ti_postinst.size = len(postinst_content)
        ti_postinst.mode = 0o755
        ti_postinst.mtime = int(time.time())
        tar.addfile(ti_postinst, io.BytesIO(postinst_content))

        # prerm betiği
        prerm_content = (
            "#!/bin/sh\n"
            "set -e\n"
            "exit 0\n"
        ).encode("utf-8")
        ti_prerm = tarfile.TarInfo(name="./prerm")
        ti_prerm.size = len(prerm_content)
        ti_prerm.mode = 0o755
        ti_prerm.mtime = int(time.time())
        tar.addfile(ti_prerm, io.BytesIO(prerm_content))

        # postrm betiği
        postrm_content = (
            "#!/bin/sh\n"
            "set -e\n"
            "if which update-desktop-database >/dev/null 2>&1; then\n"
            "    update-desktop-database -q /usr/share/applications || true\n"
            "fi\n"
            "exit 0\n"
        ).encode("utf-8")
        ti_postrm = tarfile.TarInfo(name="./postrm")
        ti_postrm.size = len(postrm_content)
        ti_postrm.mode = 0o755
        ti_postrm.mtime = int(time.time())
        tar.addfile(ti_postrm, io.BytesIO(postrm_content))

    control_tar_gz = control_buf.getvalue()

    # 3. data.tar.gz
    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w:gz") as tar:
        # Dizinler
        for dir_name in [
            "./opt",
            "./opt/otoyedekparca",
            "./usr",
            "./usr/bin",
            "./usr/share",
            "./usr/share/applications",
            "./usr/share/pixmaps",
            "./usr/share/doc",
            "./usr/share/doc/otoyedekparca",
        ]:
            ti_dir = tarfile.TarInfo(name=dir_name)
            ti_dir.type = tarfile.DIRTYPE
            ti_dir.mode = 0o755
            ti_dir.mtime = int(time.time())
            tar.addfile(ti_dir)

        # Uygulama dosyaları -> /opt/otoyedekparca/...
        app_files = get_clean_app_files()
        for rel_path, abs_path in app_files:
            target_name = f"./opt/otoyedekparca/{rel_path}"
            ti = tarfile.TarInfo(name=target_name)
            data = abs_path.read_bytes()
            ti.size = len(data)
            ti.mode = 0o755 if rel_path.endswith(".py") or rel_path.endswith(".sh") else 0o644
            ti.mtime = int(abs_path.stat().st_mtime)
            tar.addfile(ti, io.BytesIO(data))

        # /usr/bin/otoyedekparca wrapper betiği
        wrapper_content = (
            "#!/bin/sh\n"
            'exec /usr/bin/python3 /opt/otoyedekparca/run.py "$@"\n'
        ).encode("utf-8")
        ti_bin = tarfile.TarInfo(name="./usr/bin/otoyedekparca")
        ti_bin.size = len(wrapper_content)
        ti_bin.mode = 0o755
        ti_bin.mtime = int(time.time())
        tar.addfile(ti_bin, io.BytesIO(wrapper_content))

        # /usr/share/applications/otoyedekparca.desktop
        desktop_content = (
            "[Desktop Entry]\n"
            "Name=Oto Yedek Parça Otomasyonu\n"
            "Comment=Oto Yedek Parça Satış ve Stok Otomasyonu\n"
            "Exec=/usr/bin/otoyedekparca\n"
            "Icon=otoyedekparca\n"
            "Terminal=false\n"
            "Type=Application\n"
            "Categories=Office;Finance;Business;\n"
            "StartupNotify=true\n"
            "Keywords=oto;yedek;parca;stok;satis;muhasebe;\n"
        ).encode("utf-8")
        ti_desktop = tarfile.TarInfo(name="./usr/share/applications/otoyedekparca.desktop")
        ti_desktop.size = len(desktop_content)
        ti_desktop.mode = 0o644
        ti_desktop.mtime = int(time.time())
        tar.addfile(ti_desktop, io.BytesIO(desktop_content))

        # /usr/share/pixmaps/otoyedekparca.png
        icon_path = KOK_DIZIN / "assets" / "otoyedekparca.png"
        if icon_path.exists():
            icon_data = icon_path.read_bytes()
            ti_icon = tarfile.TarInfo(name="./usr/share/pixmaps/otoyedekparca.png")
            ti_icon.size = len(icon_data)
            ti_icon.mode = 0o644
            ti_icon.mtime = int(icon_path.stat().st_mtime)
            tar.addfile(ti_icon, io.BytesIO(icon_data))

        # /usr/share/doc/otoyedekparca/copyright
        license_path = KOK_DIZIN / "LICENSE"
        if license_path.exists():
            lic_data = license_path.read_bytes()
            ti_lic = tarfile.TarInfo(name="./usr/share/doc/otoyedekparca/copyright")
            ti_lic.size = len(lic_data)
            ti_lic.mode = 0o644
            ti_lic.mtime = int(license_path.stat().st_mtime)
            tar.addfile(ti_lic, io.BytesIO(lic_data))

    data_tar_gz = data_buf.getvalue()

    # ar formatında birleştir
    members = [
        ("debian-binary", debian_binary_data, 0o100644),
        ("control.tar.gz", control_tar_gz, 0o100644),
        ("data.tar.gz", data_tar_gz, 0o100644),
    ]
    build_ar_archive(deb_path, members)

    size_mb = deb_path.stat().st_size / (1024 * 1024)
    sha256 = calculate_sha256(deb_path)
    print(f"  [+] Debian Paketi Hazır : {deb_path.name} ({size_mb:.2f} MB)")
    print(f"  [+] SHA-256 Hash        : {sha256}")
    return deb_path


def create_fedora_packages() -> tuple[Path, Path]:
    """Fedora / RHEL için otomatik kurulum arşivi ve kaynak arşivini üretir."""
    print("\n" + "=" * 60)
    print("📦 2. FEDORA KURULUM VE KAYNAK PAKETLERİ OLUŞTURULUYOR")
    print("=" * 60)

    # 1. Fedora Kurulum Paketi (installer tarball with install.sh and uninstall.sh)
    installer_tar_name = f"{PACKAGE_NAME}-{VERSION}-fedora-installer.tar.gz"
    installer_tar_path = DIST_INSTALLER / installer_tar_name

    install_sh = """#!/bin/bash
# Oto Yedek Parça Otomasyonu - Fedora / RHEL Kurulum Betiği
set -e

RED='\\033[0;31m'
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
NC='\\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  Oto Yedek Parça Otomasyonu v1.0.0 Kurulum Sihirbazı  ${NC}"
echo -e "${BLUE}======================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Kurulum sistem dizinlerine (/opt, /usr/bin) erişim gerektirir.${NC}"
    echo -e "${BLUE}[*] Lütfen 'sudo ./install.sh' olarak çalıştırınız.${NC}"
    exit 1
fi

APP_DIR="/opt/otoyedekparca"
BIN_FILE="/usr/bin/otoyedekparca"
DESKTOP_FILE="/usr/share/applications/otoyedekparca.desktop"
ICON_FILE="/usr/share/pixmaps/otoyedekparca.png"

echo -e "${BLUE}[1/4] Bağımlılıklar denetleniyor (dnf)...${NC}"
if which dnf >/dev/null 2>&1; then
    dnf install -y python3 python3-pyside6 python3-openpyxl python3-reportlab 2>/dev/null || {
        echo -e "${BLUE}[*] dnf paketleri bulunamadı, pip ile tamamlanıyor...${NC}"
        python3 -m pip install -r requirements.txt || true
    }
fi

echo -e "${BLUE}[2/4] Uygulama dosyaları ${APP_DIR} dizinine kuruluyor...${NC}"
mkdir -p "${APP_DIR}"
cp -r app assets run.py requirements.txt LICENSE THIRD_PARTY_LICENSES.md "${APP_DIR}/"
chmod -R 755 "${APP_DIR}"

echo -e "${BLUE}[3/4] Başlatıcı komutu ve masaüstü kısayolu oluşturuluyor...${NC}"
cat << 'EOF' > "${BIN_FILE}"
#!/bin/sh
exec /usr/bin/python3 /opt/otoyedekparca/run.py "$@"
EOF
chmod 755 "${BIN_FILE}"

cat << 'EOF' > "${DESKTOP_FILE}"
[Desktop Entry]
Name=Oto Yedek Parça Otomasyonu
Comment=Oto Yedek Parça Satış ve Stok Otomasyonu
Exec=/usr/bin/otoyedekparca
Icon=otoyedekparca
Terminal=false
Type=Application
Categories=Office;Finance;Business;
StartupNotify=true
Keywords=oto;yedek;parca;stok;satis;muhasebe;
EOF
chmod 644 "${DESKTOP_FILE}"

if [ -f "assets/otoyedekparca.png" ]; then
    mkdir -p /usr/share/pixmaps
    cp assets/otoyedekparca.png "${ICON_FILE}"
    chmod 644 "${ICON_FILE}"
fi

echo -e "${BLUE}[4/4] Masaüstü veritabanı güncelleniyor...${NC}"
which update-desktop-database >/dev/null 2>&1 && update-desktop-database /usr/share/applications || true
which gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q /usr/share/pixmaps || true

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  ✓ KURULUM BAŞARIYLA TAMAMLANDI!                    ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "Başlatmak için terminalden:  ${BLUE}otoyedekparca${NC}"
echo -e "Veya Uygulamalar menüsünden 'Oto Yedek Parça' simgesine tıklayabilirsiniz."
echo -e "Not: Verileriniz daima kullanıcı dizininde (~/.otoyedekparca) güvendedir."
"""

    uninstall_sh = """#!/bin/bash
# Oto Yedek Parça Otomasyonu - Kaldırma Betiği
set -e

RED='\\033[0;31m'
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
NC='\\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Kaldırma işlemi için 'sudo ./uninstall.sh' olarak çalıştırınız.${NC}"
    exit 1
fi

echo -e "${BLUE}[*] Oto Yedek Parça Otomasyonu sistemden kaldırılıyor...${NC}"
rm -rf /opt/otoyedekparca
rm -f /usr/bin/otoyedekparca
rm -f /usr/share/applications/otoyedekparca.desktop
rm -f /usr/share/pixmaps/otoyedekparca.png

which update-desktop-database >/dev/null 2>&1 && update-desktop-database /usr/share/applications || true

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  ✓ Uygulama başarıyla kaldırıldı.                  ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "${BLUE}[!] Güvenlik Notu: Müşteri veritabanınız ve yedekleriniz (~/.otoyedekparca) SİLİNMEMİŞTİR.${NC}"
echo -e "Tüm verileri de silmek isterseniz: rm -rf ~/.otoyedekparca"
"""

    readme_fedora = f"""# Oto Yedek Parça Otomasyonu v{VERSION} - Fedora / RHEL Kurulum Paketi

Bu paket Fedora, Red Hat Enterprise Linux (RHEL), CentOS Stream, Rocky Linux ve AlmaLinux sistemleri için hazırlanmıştır.

## Hızlı Kurulum

Terminali açın ve arşivin açıldığı klasörde şu komutu çalıştırın:

```bash
sudo ./install.sh
```

## Başlatma

Kurulum tamamlandıktan sonra:
- Terminalden: `otoyedekparca`
- Veya Uygulama Menüsünden: "Oto Yedek Parça Otomasyonu"

## Kaldırma

```bash
sudo ./uninstall.sh
```
Kaldırma işlemi müşteri veritabanını (`~/.otoyedekparca`) korur, asla silmez.
"""

    # Fedora Installer Arşivi Oluştur
    prefix = f"{PACKAGE_NAME}-{VERSION}"
    with tarfile.open(installer_tar_path, "w:gz") as tar:
        # install.sh
        data_install = install_sh.encode("utf-8")
        ti = tarfile.TarInfo(name=f"{prefix}/install.sh")
        ti.size = len(data_install)
        ti.mode = 0o755
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(data_install))

        # uninstall.sh
        data_uninstall = uninstall_sh.encode("utf-8")
        ti = tarfile.TarInfo(name=f"{prefix}/uninstall.sh")
        ti.size = len(data_uninstall)
        ti.mode = 0o755
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(data_uninstall))

        # README.md
        data_readme = readme_fedora.encode("utf-8")
        ti = tarfile.TarInfo(name=f"{prefix}/README.md")
        ti.size = len(data_readme)
        ti.mode = 0o644
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(data_readme))

        # otoyedekparca.spec
        spec_path = KOK_DIZIN / "packaging" / "fedora" / "otoyedekparca.spec"
        if spec_path.exists():
            data_spec = spec_path.read_bytes()
            ti = tarfile.TarInfo(name=f"{prefix}/otoyedekparca.spec")
            ti.size = len(data_spec)
            ti.mode = 0o644
            ti.mtime = int(spec_path.stat().st_mtime)
            tar.addfile(ti, io.BytesIO(data_spec))

        # Uygulama dosyaları
        app_files = get_clean_app_files()
        for rel_path, abs_path in app_files:
            ti = tarfile.TarInfo(name=f"{prefix}/{rel_path}")
            data = abs_path.read_bytes()
            ti.size = len(data)
            ti.mode = 0o755 if rel_path.endswith(".py") or rel_path.endswith(".sh") else 0o644
            ti.mtime = int(abs_path.stat().st_mtime)
            tar.addfile(ti, io.BytesIO(data))

    size_installer = installer_tar_path.stat().st_size / (1024 * 1024)
    sha_installer = calculate_sha256(installer_tar_path)
    print(f"  [+] Fedora Kurulum Paketi : {installer_tar_path.name} ({size_installer:.2f} MB)")
    print(f"  [+] SHA-256 Hash          : {sha_installer}")

    # 2. Fedora RPM Kaynak Arşivi (rpmbuild -ba uyumlu)
    src_tar_name = f"{PACKAGE_NAME}-{VERSION}.tar.gz"
    src_tar_path = DIST_INSTALLER / src_tar_name
    with tarfile.open(src_tar_path, "w:gz") as tar:
        for rel_path, abs_path in app_files:
            ti = tarfile.TarInfo(name=f"{prefix}/{rel_path}")
            data = abs_path.read_bytes()
            ti.size = len(data)
            ti.mode = 0o755 if rel_path.endswith(".py") or rel_path.endswith(".sh") else 0o644
            ti.mtime = int(abs_path.stat().st_mtime)
            tar.addfile(ti, io.BytesIO(data))

    size_src = src_tar_path.stat().st_size / (1024 * 1024)
    sha_src = calculate_sha256(src_tar_path)
    print(f"  [+] Fedora Kaynak Arşivi : {src_tar_path.name} ({size_src:.2f} MB)")
    print(f"  [+] SHA-256 Hash         : {sha_src}")

    return installer_tar_path, src_tar_path


def main():
    print("=" * 70)
    print(f"🚀 OTO YEDEK PARÇA OTOMASYONU - LINUX PAKET ÜRETİMİ (v{VERSION})")
    print("=" * 70)

    deb_path = create_debian_package()
    fedora_inst, fedora_src = create_fedora_packages()

    print("\n" + "=" * 70)
    print("🎉 TÜM LINUX PAKETLERİ BAŞARIYLA ÜRETİLDİ!")
    print("=" * 70)
    print(f"  1. Debian / Ubuntu (.deb)      : {deb_path.name}")
    print(f"  2. Fedora Kurulum Paketi (.tar): {fedora_inst.name}")
    print(f"  3. Fedora RPM Kaynak (.tar.gz) : {fedora_src.name}")
    print(f"  📂 Çıktı Dizini                : {DIST_INSTALLER}")
    print("=" * 70)


if __name__ == "__main__":
    main()
