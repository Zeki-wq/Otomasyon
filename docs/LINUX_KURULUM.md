# Linux Kurulum ve Kullanım Kılavuzu (Debian & Fedora)

Bu kılavuz, **Oto Yedek Parça Otomasyonu v1.0.0** masaüstü uygulamasının Debian tabanlı (Debian, Ubuntu, Linux Mint, Pop!_OS) ve Red Hat / Fedora tabanlı (Fedora, RHEL, CentOS Stream, Rocky Linux, AlmaLinux) işletim sistemlerine kurulumunu, başlatılmasını ve güvenli kaldırılmasını açıklar.

---

## 1. Paket Formatları ve Dosyalar

Tüm kurulum dosyaları GitHub Release sayfasından veya yerel derleme çıktısından temin edilebilir:

| Dağıtım Ailesi | Paket Dosyası | Açıklama |
| :--- | :--- | :--- |
| **Debian / Ubuntu** | `otoyedekparca_1.0.0_all.deb` | Standart Debian binary paketi (`apt` / `dpkg` uyumlu) |
| **Fedora / RHEL** | `otoyedekparca-1.0.0-fedora-installer.tar.gz` | Otomatik `install.sh` ve `uninstall.sh` içeren Fedora paketi |
| **Fedora RPM Kaynak**| `otoyedekparca-1.0.0.tar.gz` + `otoyedekparca.spec` | `rpmbuild` ile doğrudan kurumsal `.rpm` üretmek için |
| **Windows** | `OtoYedekParca_Setup_v1.0.0.exe` | Windows 10/11 64-bit Inno Setup kurulum sihirbazı |

---

## 2. Debian / Ubuntu / Linux Mint Kurulumu

### Adım 1: .deb Paketini İndirin
GitHub Release'den `otoyedekparca_1.0.0_all.deb` dosyasını indirin.

### Adım 2: Paketi Kurun
Bağımlılıkları otomatik çözümlemesi için `apt` ile kurmanız önerilir:

```bash
# Önerilen yöntem (bağımlılıkları otomatik indirir):
sudo apt update
sudo apt install ./otoyedekparca_1.0.0_all.deb

# Alternatif dpkg yöntemi:
sudo dpkg -i otoyedekparca_1.0.0_all.deb
sudo apt-get install -f -y
```

### Adım 3: Çalıştırın
- **Terminalden:**
  ```bash
  otoyedekparca
  ```
- **Masaüstünden:**
  Uygulama Menüsü -> **Ofis / Ticari** -> **Oto Yedek Parça Otomasyonu**

### Debian / Ubuntu'dan Kaldırma
```bash
sudo apt remove otoyedekparca
```
> **Önemli:** Kaldırma işlemi müşteri veritabanınızı (`~/.otoyedekparca`) **asla silmez**. Verileriniz güvende kalır.

---

## 3. Fedora / RHEL / CentOS Kurulumu

### Yöntem A: Hızlı Kurulum Betiği (Önerilen)

1. `otoyedekparca-1.0.0-fedora-installer.tar.gz` arşivini indirin ve açın:
   ```bash
   tar -xzf otoyedekparca-1.0.0-fedora-installer.tar.gz
   cd otoyedekparca-1.0.0
   ```

2. Kurulum betiğini yönetici yetkisiyle çalıştırın:
   ```bash
   sudo ./install.sh
   ```
   *Bu betik `dnf` üzerinden `python3-pyside6`, `python3-openpyxl` ve `python3-reportlab` paketlerini kurar, masaüstü kısayolunu ve sistem simgesini hazırlar.*

3. Programı başlatın:
   ```bash
   otoyedekparca
   ```

### Yöntem B: Kurumsal RPM Paketi Derleme (`rpmbuild`)

Eğer şirketinizde veya sunucularınızda doğrudan `.rpm` dağıtımı yapmak isterseniz:

1. Gerekli RPM geliştirici araçlarını yükleyin:
   ```bash
   sudo dnf install -y rpm-build rpmdevtools desktop-file-utils
   rpmdev-setuptree
   ```

2. Kaynak arşivi ve spec dosyasını kopyalayın:
   ```bash
   cp otoyedekparca-1.0.0.tar.gz ~/rpmbuild/SOURCES/
   cp otoyedekparca.spec ~/rpmbuild/SPECS/
   ```

3. RPM paketini derleyin:
   ```bash
   rpmbuild -ba ~/rpmbuild/SPECS/otoyedekparca.spec
   ```
   *Üretilen RPM paketi `~/rpmbuild/RPMS/noarch/otoyedekparca-1.0.0-1.fc*.noarch.rpm` konumunda hazır olur.*

4. RPM ile kurun:
   ```bash
   sudo dnf install ~/rpmbuild/RPMS/noarch/otoyedekparca-1.0.0-1.*.noarch.rpm
   ```

### Fedora'dan Kaldırma
- Yöntem A ile kurulduysa:
  ```bash
  sudo ./uninstall.sh
  ```
- RPM ile kurulduysa:
  ```bash
  sudo dnf remove otoyedekparca
  ```
> **Önemli:** Kaldırma işlemi müşteri veritabanınızı (`~/.otoyedekparca`) **silmez**.

---

## 4. Linux Veri Depolama ve Güvenlik Yalıtımı

Linux üzerinde uygulama, kullanıcı izinleri ve veri güvenliği için katı standartlara uyar:

1. **Uygulama İkili Dosyaları:**
   - `/opt/otoyedekparca/`: Yalnızca salt okunur uygulama kodları ve lisanslar.
   - `/usr/bin/otoyedekparca`: Global çalıştırılabilir sembolik bağlantı / wrapper.
   - `/usr/share/applications/otoyedekparca.desktop`: XDG standart masaüstü girişi.
   - `/usr/share/pixmaps/otoyedekparca.png`: 256x256 yüksek çözünürlüklü simge.

2. **Kullanıcı Verileri (Her kullanıcının kendi ev dizininde yalıtılmıştır):**
   - **Veritabanı:** `~/.otoyedekparca/otoyedekparca.db`
   - **Yedekler:** `~/.otoyedekparca/backups/`
   - **Loglar:** `~/.otoyedekparca/logs/`
   - **Rapor Çıktıları:** `~/.otoyedekparca/exports/`

3. **Veri Koruma Garantisi:**
   - Yeniden kurulum, sürüm yükseltme veya paket güncelleme işlemlerinde `~/.otoyedekparca` klasörü **asla silinmez, üzerine yazılmaz veya sıfırlanmaz**.
   - Uygulama ilk açıldığında otomatik olarak temiz veritabanı şemasını oluşturur ve ilk yönetici hesabı oluşturma sihirbazını başlatır.
