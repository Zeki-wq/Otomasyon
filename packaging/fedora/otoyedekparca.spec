Name:           otoyedekparca
Version:        1.0.0
Release:        1%{?dist}
Summary:        Oto Yedek Parca Satis ve Stok Otomasyonu
License:        Proprietary
URL:            https://github.com/Zeki-wq/Otomasyon
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  desktop-file-utils

Requires:       python3 >= 3.10
Requires:       python3-pyside6
Requires:       python3-openpyxl
Requires:       python3-reportlab
Requires:       hicolor-icon-theme

%description
Oto yedek parça satış ve dükkan yönetimi için geliştirilmiş,
yüksek performanslı ve %100 çevrimdışı çalışabilen masaüstü otomasyon paketi.
PySide6 (Qt 6) tabanlı modern koyu arayüz, barkod & OEM arama,
kasa, veresiye cari takip ve PDF fiş raporlama özellikleri sunar.

%prep
%autosetup -n %{name}-%{version}

%build
# Saf Python uygulaması - C derleme adımı gerektirmez

%install
rm -rf %{buildroot}

# Uygulama dosyaları /opt/otoyedekparca altına kopyalanır
mkdir -p %{buildroot}/opt/%{name}
cp -r app %{buildroot}/opt/%{name}/
cp -r assets %{buildroot}/opt/%{name}/
cp run.py %{buildroot}/opt/%{name}/
cp requirements.txt %{buildroot}/opt/%{name}/
cp LICENSE %{buildroot}/opt/%{name}/
cp THIRD_PARTY_LICENSES.md %{buildroot}/opt/%{name}/

# Çalıştırılabilir wrapper betiği /usr/bin/otoyedekparca
mkdir -p %{buildroot}%{_bindir}
cat << 'EOF' > %{buildroot}%{_bindir}/%{name}
#!/bin/sh
exec /usr/bin/python3 /opt/otoyedekparca/run.py "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

# Masaüstü kısayolu (.desktop)
mkdir -p %{buildroot}%{_datadir}/applications
cat << 'EOF' > %{buildroot}%{_datadir}/applications/%{name}.desktop
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

# Uygulama ikonu
mkdir -p %{buildroot}%{_datadir}/pixmaps
cp assets/otoyedekparca.png %{buildroot}%{_datadir}/pixmaps/%{name}.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop || :

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
which update-desktop-database &>/dev/null && update-desktop-database &>/dev/null || :

%postun
which update-desktop-database &>/dev/null && update-desktop-database &>/dev/null || :

%files
%license LICENSE THIRD_PARTY_LICENSES.md
/opt/%{name}
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/pixmaps/%{name}.png

%changelog
* Sat Oct 24 2026 Zeki <destek@otoyedekparca.local> - 1.0.0-1
- İlk kararlı sürüm (v1.0.0-rc1)
- PySide6 Qt6 desteği, temiz veritabanı yalıtımı ve güvenli fabrika sıfırlaması
