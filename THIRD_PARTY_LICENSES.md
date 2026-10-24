# Üçüncü Taraf Yazılım Lisans Bildirimi (Third Party Licenses)

> [!WARNING]
> **HUKUKİ UYARI:** İşbu belge bir yazılım mühendisliği lisans denetim özetidir ve hukuki tavsiye niteliği taşımaz. Ticari dağıtım ve kurumsal satış öncesinde **şirket avukatına doğrulatılmalıdır**.

Bu doküman, **Oto Yedek Parça Otomasyonu** masaüstü uygulamasının çalışma zamanı (runtime) ve paketleme sürecinde kullanılan üçüncü taraf kütüphaneleri, sürümlerini ve lisanslarını listeler.

---

## 1. Çalışma Zamanı (Runtime) Bağımlılıkları ve Lisans Tablosu

Aşağıdaki kütüphaneler uygulamanın son kullanıcıya teslim edilen dağıtım paketinde (`dist/OtoYedekParca`) yer alır:

| Kütüphane / Bileşen | Dağıtılan Sürüm | Lisans Türü | Ticari Dağıtıma Uygunluk Durumu |
| :--- | :--- | :--- | :--- |
| **PySide6** | 6.12.0 | LGPLv3 (GNU Lesser General Public License v3) | ✅ UYGUN (LGPL şartlarına uyulduğunda) |
| **PySide6_Essentials** | 6.12.0 | LGPLv3 | ✅ UYGUN |
| **PySide6_Addons** | 6.12.0 | LGPLv3 | ✅ UYGUN |
| **shiboken6** | 6.12.0 | LGPLv3 | ✅ UYGUN |
| **openpyxl** | 3.1.5 | MIT License | ✅ UYGUN (Kısıtlamasız Ticari Kullanım) |
| **et_xmlfile** | 2.0.0 | MIT License | ✅ UYGUN (Kısıtlamasız Ticari Kullanım) |
| **reportlab** | 5.1.0 | BSD License | ✅ UYGUN (Telif bildirimi korunarak) |
| **pillow** | 12.0.0 | MIT-CMU License | ✅ UYGUN (Kısıtlamasız Ticari Kullanım) |
| **Python Runtime** | 3.12.6 | PSF License (Python Software Foundation) | ✅ UYGUN (Ticari Dağıtıma İzinli) |
| **SQLite** | 3.45+ | Public Domain | ✅ UYGUN (Hiçbir Telif Kısıtı Yoktur) |

---

## 2. Geliştirme ve Derleme (Build & Test) Araçları

Aşağıdaki araçlar yalnızca geliştirme ve derleme ortamında kullanılır, son kullanıcı çalıştırılabilir kodunun içine entegre edilmez:

| Araç | Sürüm | Lisans | Açıklama |
| :--- | :--- | :--- | :--- |
| **PyInstaller** | 6.22.3 | GPLv2 with Special Exception | PyInstaller özel istisnası (bootloader exception), derlenen tescilli/ticari yazılımların kaynak kodunun açılmasını zorunlu kılmaz. |
| **pytest** | 9.1.1 | MIT License | Test çatısı |
| **pytest-qt** | 4.5.0 | MIT License | Qt test eklentisi |
| **pytest-timeout** | 2.4.0 | MIT License | Test zaman aşımı denetimi |
| **ruff** | 0.17.2 | MIT License | Kod stili ve linter |
| **pip-licenses** | 5.5.5 | MIT License | Lisans denetim aracı |

---

## 3. GPL / AGPL Taraması ve Uygunluk Kararı

- Dağıtım paketinde ve `requirements.txt` dosyasında **katı GPL (GNU GPL) veya AGPL (Affero GPL) lisanslı hiçbir çalışma zamanı bağımlılığı BULUNMAMAKTADIR**.
- Eski sistemdeki `PyQt5` (GPLv3) tamamen kaldırılmış ve yerine LGPLv3 lisanslı `PySide6` (The Qt Company resmi Python bağlayıcısı) geçirilmiştir.
- Bu sayede uygulamanın kendi özgün kaynak kodlarını (fikri mülkiyetini) açma zorunluluğu doğmaz.

---

## 4. PySide6 (LGPLv3) Ticari Dağıtım Şartları ve Uyumluluk

PySide6, LGPLv3 lisansı altında tescilli ticari yazılımlarda serbestçe kullanılabilir; ancak aşağıdaki 4 yasal şartın eksiksiz sağlanması zorunludur:

1. **Dinamik Bağlama (Dynamic Linking):**
   - PySide6 ve Qt paylaşımlı kütüphaneleri (`.dll` dosyaları) uygulamaya statik olarak gömülmemiştir (statically linked değildir).
   - PyInstaller paketi `--onedir` modunda derlenmiş olup, tüm Qt kütüphaneleri (`Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll`, `shiboken6.abi3.dll` vb.) `_internal/PySide6/` klasörü altında ayrı dinamik DLL dosyaları olarak yer almaktadır.
   - Kullanıcı, bu DLL dosyalarını Qt'nin uyumlu başka bir sürümüyle değiştirip uygulamayı çalıştırabilme teknik imkanına sahiptir.

2. **Lisans Metninin Bulundurulması:**
   - Kurulum paketinde ve dağıtım dizininde LGPLv3 ve GPLv3 metinleri (`LGPLv3.txt`, `GPLv3.txt`) kullanıcıya sunulmalıdır.
   - Uygulamanın "Hakkında" penceresinde PySide6 ve Qt kullanımı açıkça beyan edilmeli ve LGPLv3 lisansına atıfta bulunulmalıdır.

3. **Kaynak Koduna Erişim Bilgisi:**
   - Uygulama, Qt ve PySide6 kütüphanelerinin kaynak kodlarında herhangi bir değişiklik yapmamıştır (resmi PyPI binary dağıtımı kullanılmıştır).
   - Kullanıcıların PySide6 ve Qt kaynak kodlarına erişebilmesi için resmi indirme bağlantıları (https://code.qt.io/cgit/pyside/pyside-setup.git ve https://download.qt.io/) dokümantasyonda ve Hakkında penceresinde sağlanmalıdır.

4. **Tersine Mühendislik (Reverse Engineering) İzni:**
   - LGPLv3 Madde 4d uyarınca, uygulamanın yalnızca Qt kütüphaneleriyle etkileşime giren kısımlarında hata ayıklama (debugging) amacıyla tersine mühendisliğe müsaade edildiği kullanıcı sözleşmesinde (EULA) belirtilmelidir.

---

> [!NOTE]
> **Avukata Doğrulatılmalıdır:** Bu dokümanda listelenen maddeler LGPLv3 ve açık kaynak lisans uyumluluğu için uluslararası standart kabul edilen yönergelerdir. Satış öncesi hukuk danışmanınız tarafından incelenmesi tavsiye edilir.
