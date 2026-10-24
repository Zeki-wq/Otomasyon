#!/usr/bin/env python3
"""
Debian (.deb) ve Fedora (.rpm & installer) Paket Üretici
(packaging/linux/build_linux_packages.py)

Saf Python ile harici bağımlılık (dpkg-deb, rpmbuild vb.) gerektirmeden:
1. Debian (.deb) kurulum paketini (otoyedekparca_1.0.0_all.deb)
2. Fedora (.rpm) resmi binary paketini (otoyedekparca-1.0.0-1.noarch.rpm)
3. Fedora / RHEL otomatik kurulum paketini (otoyedekparca-1.0.0-fedora-installer.tar.gz)
4. Fedora RPM kaynak arşivini (otoyedekparca-1.0.0.tar.gz)
üretir, rpmfile ile doğrular ve SHA-256 özetlerini hesaplar.
"""

import gzip
import hashlib
import io
import os
import struct
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
ARCH_DEB = "all"
ARCH_RPM = "noarch"


def calculate_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().upper()


def get_clean_app_files() -> list[tuple[str, Path]]:
    """Pakete dahil edilecek temiz uygulama dosyalarını döndürür."""
    files = []
    for fname in ["run.py", "requirements.txt", "LICENSE", "THIRD_PARTY_LICENSES.md"]:
        p = KOK_DIZIN / fname
        if p.exists():
            files.append((fname, p))

    app_dir = KOK_DIZIN / "app"
    for p in app_dir.rglob("*"):
        if p.is_file():
            if "__pycache__" in p.parts:
                continue
            if p.suffix.lower() in [".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".log"]:
                continue
            rel = p.relative_to(KOK_DIZIN).as_posix()
            files.append((rel, p))

    assets_dir = KOK_DIZIN / "assets"
    for p in assets_dir.rglob("*"):
        if p.is_file():
            rel = p.relative_to(KOK_DIZIN).as_posix()
            files.append((rel, p))

    return files


# ==============================================================================
# 1. DEBIAN (.DEB) PAKETİ ÜRETİCİ
# ==============================================================================

def build_ar_archive(output_path: Path, members: list[tuple[str, bytes, int]]):
    with open(output_path, "wb") as f:
        f.write(b"!<arch>\n")
        mtime = int(time.time())
        uid = 0
        gid = 0

        for name, data, mode in members:
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
            if len(data) % 2 != 0:
                f.write(b"\n")


def create_debian_package() -> Path:
    print("\n" + "=" * 60)
    print("📦 1. DEBIAN (.DEB) PAKETİ OLUŞTURULUYOR")
    print("=" * 60)

    deb_filename = f"{PACKAGE_NAME}_{VERSION}_{ARCH_DEB}.deb"
    deb_path = DIST_INSTALLER / deb_filename

    debian_binary_data = b"2.0\n"

    # control.tar.gz
    control_buf = io.BytesIO()
    with tarfile.open(fileobj=control_buf, mode="w:gz") as tar:
        control_content = (
            f"Package: {PACKAGE_NAME}\n"
            f"Version: {VERSION}\n"
            f"Section: utils\n"
            f"Priority: optional\n"
            f"Architecture: {ARCH_DEB}\n"
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

        postinst_content = (
            "#!/bin/sh\n"
            "set -e\n"
            "chmod 0755 /usr/bin/otoyedekparca 2>/dev/null || true\n"
            "which update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true\n"
            "which gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q /usr/share/pixmaps || true\n"
            "exit 0\n"
        ).encode("utf-8")
        ti_postinst = tarfile.TarInfo(name="./postinst")
        ti_postinst.size = len(postinst_content)
        ti_postinst.mode = 0o755
        ti_postinst.mtime = int(time.time())
        tar.addfile(ti_postinst, io.BytesIO(postinst_content))

        prerm_content = "#!/bin/sh\nset -e\nexit 0\n".encode("utf-8")
        ti_prerm = tarfile.TarInfo(name="./prerm")
        ti_prerm.size = len(prerm_content)
        ti_prerm.mode = 0o755
        ti_prerm.mtime = int(time.time())
        tar.addfile(ti_prerm, io.BytesIO(prerm_content))

        postrm_content = (
            "#!/bin/sh\n"
            "set -e\n"
            "which update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true\n"
            "exit 0\n"
        ).encode("utf-8")
        ti_postrm = tarfile.TarInfo(name="./postrm")
        ti_postrm.size = len(postrm_content)
        ti_postrm.mode = 0o755
        ti_postrm.mtime = int(time.time())
        tar.addfile(ti_postrm, io.BytesIO(postrm_content))

    control_tar_gz = control_buf.getvalue()

    # data.tar.gz
    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w:gz") as tar:
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

        app_files = get_clean_app_files()
        for rel_path, abs_path in app_files:
            target_name = f"./opt/otoyedekparca/{rel_path}"
            ti = tarfile.TarInfo(name=target_name)
            data = abs_path.read_bytes()
            ti.size = len(data)
            ti.mode = 0o755 if rel_path.endswith(".py") or rel_path.endswith(".sh") else 0o644
            ti.mtime = int(abs_path.stat().st_mtime)
            tar.addfile(ti, io.BytesIO(data))

        wrapper_content = (
            "#!/bin/sh\n"
            'exec /usr/bin/python3 /opt/otoyedekparca/run.py "$@"\n'
        ).encode("utf-8")
        ti_bin = tarfile.TarInfo(name="./usr/bin/otoyedekparca")
        ti_bin.size = len(wrapper_content)
        ti_bin.mode = 0o755
        ti_bin.mtime = int(time.time())
        tar.addfile(ti_bin, io.BytesIO(wrapper_content))

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

        icon_path = KOK_DIZIN / "assets" / "otoyedekparca.png"
        if icon_path.exists():
            icon_data = icon_path.read_bytes()
            ti_icon = tarfile.TarInfo(name="./usr/share/pixmaps/otoyedekparca.png")
            ti_icon.size = len(icon_data)
            ti_icon.mode = 0o644
            ti_icon.mtime = int(icon_path.stat().st_mtime)
            tar.addfile(ti_icon, io.BytesIO(icon_data))

        license_path = KOK_DIZIN / "LICENSE"
        if license_path.exists():
            lic_data = license_path.read_bytes()
            ti_lic = tarfile.TarInfo(name="./usr/share/doc/otoyedekparca/copyright")
            ti_lic.size = len(lic_data)
            ti_lic.mode = 0o644
            ti_lic.mtime = int(license_path.stat().st_mtime)
            tar.addfile(ti_lic, io.BytesIO(lic_data))

    data_tar_gz = data_buf.getvalue()

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


# ==============================================================================
# 2. FEDORA (.RPM) BİNARY PAKETİ ÜRETİCİ
# ==============================================================================

TYPE_NULL = 0
TYPE_CHAR = 1
TYPE_INT8 = 2
TYPE_INT16 = 3
TYPE_INT32 = 4
TYPE_INT64 = 5
TYPE_STRING = 6
TYPE_BIN = 7
TYPE_STRING_ARRAY = 8
TYPE_I18NSTRING = 9


class RpmHeaderBuilder:
    def __init__(self):
        self.entries = []

    def add_string(self, tag: int, val: str):
        self.entries.append((tag, TYPE_STRING, val.encode("utf-8") + b"\x00", 1))

    def add_string_array(self, tag: int, val_list: list[str]):
        data = b"".join(s.encode("utf-8") + b"\x00" for s in val_list)
        self.entries.append((tag, TYPE_STRING_ARRAY, data, len(val_list)))

    def add_int32(self, tag: int, val: int):
        self.entries.append((tag, TYPE_INT32, [val], 1))

    def add_int32_array(self, tag: int, val_list: list[int]):
        self.entries.append((tag, TYPE_INT32, val_list, len(val_list)))

    def add_int16_array(self, tag: int, val_list: list[int]):
        self.entries.append((tag, TYPE_INT16, val_list, len(val_list)))

    def add_bin(self, tag: int, val: bytes):
        self.entries.append((tag, TYPE_BIN, val, len(val)))

    def build(self) -> bytes:
        sorted_entries = sorted(self.entries, key=lambda e: e[0])

        index_bytes = io.BytesIO()
        data_bytes = io.BytesIO()

        for tag, dtype, val, count in sorted_entries:
            offset = data_bytes.tell()
            if dtype == TYPE_INT16 and offset % 2 != 0:
                data_bytes.write(b"\x00" * (2 - offset % 2))
                offset = data_bytes.tell()
            elif dtype == TYPE_INT32 and offset % 4 != 0:
                data_bytes.write(b"\x00" * (4 - offset % 4))
                offset = data_bytes.tell()
            elif dtype == TYPE_INT64 and offset % 8 != 0:
                data_bytes.write(b"\x00" * (8 - offset % 8))
                offset = data_bytes.tell()

            if dtype == TYPE_INT16:
                for v in val:
                    data_bytes.write(struct.pack(">H", v & 0xFFFF))
            elif dtype == TYPE_INT32:
                for v in val:
                    data_bytes.write(struct.pack(">i", v if v < 0x80000000 else v - 0x100000000))
            elif dtype == TYPE_INT64:
                for v in val:
                    data_bytes.write(struct.pack(">q", v))
            elif dtype in (TYPE_STRING, TYPE_BIN, TYPE_STRING_ARRAY, TYPE_I18NSTRING):
                data_bytes.write(val)

            index_bytes.write(struct.pack(">IIII", tag, dtype, offset, count))

        nindex = len(sorted_entries)
        ndata = data_bytes.tell()

        header = b"\x8e\xad\xe8\x01\x00\x00\x00\x00" + struct.pack(">II", nindex, ndata)
        return header + index_bytes.getvalue() + data_bytes.getvalue()


def make_cpio_entry(filename: str, file_data: bytes, mode: int, mtime: int, ino: int) -> bytes:
    name_bytes = filename.encode("utf-8") + b"\x00"
    header_str = (
        f"070701"
        f"{ino:08X}"
        f"{mode:08X}"
        f"00000000"
        f"00000000"
        f"00000001"
        f"{mtime:08X}"
        f"{len(file_data):08X}"
        f"00000003"
        f"00000001"
        f"00000000"
        f"00000000"
        f"{len(name_bytes):08X}"
        f"00000000"
    )
    res = header_str.encode("ascii") + name_bytes
    if len(res) % 4 != 0:
        res += b"\x00" * (4 - len(res) % 4)
    res += file_data
    if len(file_data) % 4 != 0:
        res += b"\x00" * (4 - len(file_data) % 4)
    return res


def create_fedora_rpm_package() -> Path:
    print("\n" + "=" * 60)
    print("📦 2. FEDORA (.RPM) BİNARY PAKETİ OLUŞTURULUYOR")
    print("=" * 60)

    rpm_filename = f"{PACKAGE_NAME}-{VERSION}-1.{ARCH_RPM}.rpm"
    rpm_path = DIST_INSTALLER / rpm_filename

    now = int(time.time())

    # Pakete girecek sanal dosyaları topla
    raw_files = []

    # 1. /opt/otoyedekparca/...
    app_files = get_clean_app_files()
    for rel_path, abs_path in app_files:
        fpath = f"/opt/otoyedekparca/{rel_path}"
        data = abs_path.read_bytes()
        mode = 0o100755 if rel_path.endswith(".py") or rel_path.endswith(".sh") else 0o100644
        mtime = int(abs_path.stat().st_mtime)
        raw_files.append((fpath, data, mode, mtime))

    # 2. /usr/bin/otoyedekparca
    bin_data = b'#!/bin/sh\nexec /usr/bin/python3 /opt/otoyedekparca/run.py "$@"\n'
    raw_files.append(("/usr/bin/otoyedekparca", bin_data, 0o100755, now))

    # 3. /usr/share/applications/otoyedekparca.desktop
    desktop_data = (
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
    raw_files.append(("/usr/share/applications/otoyedekparca.desktop", desktop_data, 0o100644, now))

    # 4. /usr/share/pixmaps/otoyedekparca.png
    icon_path = KOK_DIZIN / "assets" / "otoyedekparca.png"
    if icon_path.exists():
        raw_files.append(("/usr/share/pixmaps/otoyedekparca.png", icon_path.read_bytes(), 0o100644, now))

    # Dosyaları path sırasına göre diz
    raw_files.sort(key=lambda x: x[0])

    # Dizinleri haritala
    dir_set = set()
    for fpath, _, _, _ in raw_files:
        dname = str(Path(fpath).parent.as_posix()) + "/"
        dir_set.add(dname)
    dir_list = sorted(list(dir_set))
    dir_to_idx = {d: i for i, d in enumerate(dir_list)}

    basenames = []
    dirindexes = []
    filesizes = []
    filemodes = []
    filemtimes = []
    filemd5s = []
    fileinodes = []

    # CPIO payload oluştur
    cpio_buf = bytearray()
    ino = 1
    total_size = 0

    for fpath, data, mode, mtime in raw_files:
        p = Path(fpath)
        dname = str(p.parent.as_posix()) + "/"
        bname = p.name

        basenames.append(bname)
        dirindexes.append(dir_to_idx[dname])
        filesizes.append(len(data))
        filemodes.append(mode)
        filemtimes.append(mtime)
        filemd5s.append(hashlib.md5(data).hexdigest())
        fileinodes.append(ino)
        total_size += len(data)

        cpio_buf += make_cpio_entry("." + fpath, data, mode, mtime, ino)
        ino += 1

    cpio_buf += make_cpio_entry("TRAILER!!!", b"", 0, 0, 0)
    uncompressed_payload_size = len(cpio_buf)
    compressed_payload = gzip.compress(bytes(cpio_buf), mtime=0)

    # Main Header
    main_hdr = RpmHeaderBuilder()
    main_hdr.add_string(1000, PACKAGE_NAME)
    main_hdr.add_string(1001, VERSION)
    main_hdr.add_string(1002, "1")
    main_hdr.add_string(1004, "Oto Yedek Parca Satis ve Stok Otomasyonu")
    main_hdr.add_string(1005, (
        "Oto yedek parca satis ve dukkan yonetimi icin gelistirilmis, "
        "yuksek performansli ve %100 cevrimdisi calisabilen masaustu otomasyon paketi. "
        "PySide6 (Qt 6) tabanli modern koyu arayuz, barkod & OEM arama, "
        "kasa, veresiye cari takip ve PDF fis raporlama ozellikleri sunar."
    ))
    main_hdr.add_int32(1006, now)
    main_hdr.add_int32(1009, total_size)
    main_hdr.add_string(1010, "Fedora")
    main_hdr.add_string(1011, "OtoYedekParca")
    main_hdr.add_string(1014, "Proprietary")
    main_hdr.add_string(1015, "Zeki <destek@otoyedekparca.local>")
    main_hdr.add_string(1016, "Applications/Productivity")
    main_hdr.add_string(1020, "https://github.com/Zeki-wq/Otomasyon")
    main_hdr.add_string(1021, "linux")
    main_hdr.add_string(1022, ARCH_RPM)
    main_hdr.add_string(1124, "cpio")
    main_hdr.add_string(1125, "gzip")
    main_hdr.add_string(1126, "9")

    # Dosya etiketleri
    nfiles = len(raw_files)
    main_hdr.add_int32_array(1116, dirindexes)
    main_hdr.add_string_array(1117, basenames)
    main_hdr.add_string_array(1118, dir_list)
    main_hdr.add_int32_array(1028, filesizes)
    main_hdr.add_int16_array(1030, filemodes)
    main_hdr.add_int32_array(1034, filemtimes)
    main_hdr.add_string_array(1035, filemd5s)
    main_hdr.add_int32_array(1037, [0] * nfiles)
    main_hdr.add_string_array(1039, ["root"] * nfiles)
    main_hdr.add_string_array(1040, ["root"] * nfiles)
    main_hdr.add_int32_array(1045, [-1] * nfiles)
    main_hdr.add_int32_array(1095, [1] * nfiles)
    main_hdr.add_int32_array(1096, fileinodes)
    main_hdr.add_int16_array(1033, [0] * nfiles)
    main_hdr.add_string_array(1097, [""] * nfiles)

    # Provides & Requires
    main_hdr.add_string_array(1047, [PACKAGE_NAME])
    main_hdr.add_string_array(1112, [f"{VERSION}-1"])
    main_hdr.add_int32_array(1113, [8])  # RPMSENSE_EQUAL

    requires = ["python3", "python3-pyside6", "python3-openpyxl", "python3-reportlab"]
    main_hdr.add_string_array(1049, requires)
    main_hdr.add_string_array(1050, [""] * len(requires))
    main_hdr.add_int32_array(1048, [0] * len(requires))

    # Post-install & Post-uninstall scripts
    postin_sh = (
        "/bin/touch --no-create /usr/share/icons/hicolor &>/dev/null || :\n"
        "which update-desktop-database &>/dev/null && update-desktop-database &>/dev/null || :\n"
    )
    main_hdr.add_string(1024, postin_sh)
    main_hdr.add_string(1026, "which update-desktop-database &>/dev/null && update-desktop-database &>/dev/null || :\n")

    main_hdr_bytes = main_hdr.build()

    # Signature Header
    sig_hdr = RpmHeaderBuilder()
    sig_hdr.add_int32(1000, len(main_hdr_bytes) + len(compressed_payload))
    sig_hdr.add_int32(1007, uncompressed_payload_size)
    sig_hdr.add_bin(267, hashlib.md5(main_hdr_bytes + compressed_payload).digest())
    sig_hdr.add_string(269, hashlib.sha1(main_hdr_bytes).hexdigest())
    sig_hdr_bytes = sig_hdr.build()

    if len(sig_hdr_bytes) % 8 != 0:
        sig_hdr_bytes += b"\x00" * (8 - len(sig_hdr_bytes) % 8)

    # Lead (96 bytes)
    full_name = f"{PACKAGE_NAME}-{VERSION}-1.{ARCH_RPM}"
    lead = (
        b"\xed\xab\xee\xdb"
        b"\x03\x00"
        + struct.pack(">H", 0)
        + struct.pack(">H", 1)
        + (full_name.encode("ascii") + b"\x00").ljust(66, b"\x00")
        + struct.pack(">H", 1)
        + struct.pack(">H", 5)
        + b"\x00" * 16
    )

    rpm_data = lead + sig_hdr_bytes + main_hdr_bytes + compressed_payload
    rpm_path.write_bytes(rpm_data)

    # rpmfile ile doğrula
    try:
        import rpmfile
        with rpmfile.open(str(rpm_path)) as rpm:
            pkg_name = rpm.headers.get("name")
            pkg_ver = rpm.headers.get("version")
            member_count = len(rpm.getmembers())
        print(f"  [✓] RPM Doğrulandı: {pkg_name.decode('utf-8')}-{pkg_ver.decode('utf-8')} ({member_count} dosya)")
    except Exception as e:
        print(f"  [!] rpmfile uyarısı: {e}")

    size_mb = rpm_path.stat().st_size / (1024 * 1024)
    sha256 = calculate_sha256(rpm_path)
    print(f"  [+] Fedora RPM Hazır    : {rpm_path.name} ({size_mb:.2f} MB)")
    print(f"  [+] SHA-256 Hash        : {sha256}")
    return rpm_path


# ==============================================================================
# 3. FEDORA KURULUM VE KAYNAK ARŞİVLERİ
# ==============================================================================

def create_fedora_archives() -> tuple[Path, Path]:
    print("\n" + "=" * 60)
    print("📦 3. FEDORA ÇEVRİMDIŞI KURULUM VE KAYNAK ARŞİVLERİ OLUŞTURULUYOR")
    print("=" * 60)

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
Categories=Office;Finance;Business;\nStartupNotify=true
Keywords=oto;yedek;parca;stok;satis;muhasebe;\nEOF
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
```bash
sudo ./install.sh
```

## Başlatma
```bash
otoyedekparca
```

## Kaldırma
```bash
sudo ./uninstall.sh
```
Kaldırma işlemi müşteri veritabanını (~/.otoyedekparca) korur, asla silmez.
"""

    prefix = f"{PACKAGE_NAME}-{VERSION}"
    app_files = get_clean_app_files()

    with tarfile.open(installer_tar_path, "w:gz") as tar:
        for name, data, mode in [
            (f"{prefix}/install.sh", install_sh.encode("utf-8"), 0o755),
            (f"{prefix}/uninstall.sh", uninstall_sh.encode("utf-8"), 0o755),
            (f"{prefix}/README.md", readme_fedora.encode("utf-8"), 0o644),
        ]:
            ti = tarfile.TarInfo(name=name)
            ti.size = len(data)
            ti.mode = mode
            ti.mtime = int(time.time())
            tar.addfile(ti, io.BytesIO(data))

        spec_path = KOK_DIZIN / "packaging" / "fedora" / "otoyedekparca.spec"
        if spec_path.exists():
            data_spec = spec_path.read_bytes()
            ti = tarfile.TarInfo(name=f"{prefix}/otoyedekparca.spec")
            ti.size = len(data_spec)
            ti.mode = 0o644
            ti.mtime = int(spec_path.stat().st_mtime)
            tar.addfile(ti, io.BytesIO(data_spec))

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
    print(f"  [+] Fedora Kaynak Arşivi : {src_tar_name} ({size_src:.2f} MB)")
    print(f"  [+] SHA-256 Hash         : {sha_src}")

    return installer_tar_path, src_tar_path


def main():
    print("=" * 70)
    print(f"🚀 OTO YEDEK PARÇA OTOMASYONU - LINUX TÜM PAKETLERİN ÜRETİMİ (v{VERSION})")
    print("=" * 70)

    deb_path = create_debian_package()
    rpm_path = create_fedora_rpm_package()
    fedora_inst, fedora_src = create_fedora_archives()

    print("\n" + "=" * 70)
    print("🎉 TÜM LINUX PAKETLERİ (DEB & RPM) BAŞARIYLA ÜRETİLDİ!")
    print("=" * 70)
    print(f"  1. Debian / Ubuntu (.deb)      : {deb_path.name}")
    print(f"  2. Fedora / RHEL (.rpm)        : {rpm_path.name}")
    print(f"  3. Fedora Kurulum Paketi (.tar): {fedora_inst.name}")
    print(f"  4. Fedora RPM Kaynak (.tar.gz) : {fedora_src.name}")
    print(f"  📂 Çıktı Dizini                : {DIST_INSTALLER}")
    print("=" * 70)


if __name__ == "__main__":
    main()
