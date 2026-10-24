# OTO YEDEK PARÇA OTOMASYONU - KULLANIM KILAVUZU (KULLANIM.md)

Bu kılavuz, dükkanda günlük işlerinizi en hızlı şekilde yapabilmeniz için hazırlanmıştır.

---

## 1. Hızlı Parça Arama ve Depo Yönetimi

1. Sol menüden **"Parça & Depo"** sekmesine tıklayınız.
2. Arama kutusuna parça kodunun bir kısmını, adını, barkodunu, OEM numarasını veya markasını yazınız.
3. Sonuçlar siz yazdıkça anında (< 100 milisaniye) listelenir.
4. **Yeni Parça Eklemek İçin:**
   - **"➕ Yeni Ürün Ekle"** butonuna basınız.
   - Parça Kodu, Adı, Fiyatı, KDV Oranı ve Raf Konumunu doldurup **"💾 Kaydet"** butonuna basınız.
5. **Kritik Stok Uyarısı:**
   - Stoğu 5'in altına (veya belirlediğiniz kritik eşiğe) inen parçalar kırmızı renkle vurgulanır ve uyarı verir.
6. **Parça Silme / Pasife Alma:**
   - Sistemde geçmiş siparişlerin bozulmaması için parçalar "sert silinmez", güvenle **pasife alınır**. Pasif parçalar geçmiş raporlarda görünmeye devam eder ancak yeni satışta listelenmez.

---

## 2. Tezgahta Hızlı Satış ve Çok Kalemli Sepet

1. Sol menüden **"Hızlı Satış"** sekmesini açınız (veya F12 kısayolunu kullanınız).
2. **Barkod Okutma:** Barkod okuyucunuzu ürünün barkoduna tuttuğunuzda ürün anında sepete eklenir.
3. **Manuel Ekleme:** Parça kodunu veya adını yazıp Enter tuşuna basınız.
4. Sağ taraftan ödeme yöntemini seçiniz:
   - **Nakit:** Müşteriden elden nakit ödeme alındığında.
   - **Kredi / Banka Kartı:** POS cihazından çekim yapıldığında.
   - **Veresiye (Cari):** Müşteri borca yazdırdığında (Açılır listeden ilgili müşteri seçilmelidir).
5. **"✅ SATIŞI ONAYLA"** butonuna bastığınız anda:
   - Sepetteki tüm ürünler depodan anında düşülür.
   - Stok hareket defterine satış kaydı işlenir.
   - Veresiye ise müşterinin cari hesabına borç otomatik eklenir.

---

## 3. Sipariş İptali ve İade Alma

1. Sol menüden **"Siparişler"** sekmesine giriniz.
2. İptal veya iade edilecek siparişi seçiniz.
3. **"❌ Siparişi İptal Et (Stoğu İade Al)"** butonuna basınız.
4. Sistem tüm ürünleri depoya otomatik iade eder, veresiye ise müşterinin borcunu geri siler.

---

## 4. Cari Hesaplar, Veresiye ve Tahsilat

1. Sol menüden **"Cari Müşteriler"** sekmesini açınız.
2. Müşterilerinizin toplam borç bakiyesini kırmızı renkli olarak görebilirsiniz.
3. **Tahsilat Almak İçin:**
   - Müşteriyi seçip **"💵 Tahsilat Girişi"** butonuna basınız.
   - Alınan tutarı yazıp kaydediniz; müşterinin borcu anında azalır.
4. **Hesap Ekstresi:**
   - **"📜 Hesap Ekstresi"** butonuna basarak müşterinin geçmiş veresiye alışverişlerini ve ödemelerini kronolojik liste halinde görebilirsiniz.

---

## 5. Excel İle Toplu Ürün Yükleme (İçe Aktarma)

1. Sol menüden **"Raporlar"** -> **"Toplu Excel İçe/Dışa Aktar"** sekmesine geliniz.
2. **"Tüm Ürünleri Excel'e Aktar"** diyerek mevcut şablonu bilgisayarınıza kaydediniz.
3. Yeni ürünlerinizi bu şablona yazıp **"Excel'den Toplu Ürün İçe Aktar"** butonu ile tek tıkla binlerce parçayı içeri aktarabilirsiniz.
4. Hatalı olan satırlar atlanır ve hangi satırda ne hatası olduğu size ayrıntılı olarak raporlanır.
