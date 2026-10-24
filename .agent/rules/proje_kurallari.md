# OTO YEDEK PARÇA OTOMASYONU - PROJE KURALLARI

Bu kurallar bu projede geliştirme yapan tüm yapay zeka ajanları ve geliştiriciler için bağlayıcıdır:

1. **Para her zaman kuruş:** Tüm parasal değerler veritabanında ve bellek içinde tamsayı kuruş (INTEGER) olarak saklanır. Kuruş <-> TL dönüşümleri ve KDV hesaplamaları yalnızca `app/domain/money.py` üzerinden yapılır.
2. **UI'da SQL yok, serviste Qt yok:** Kullanıcı arayüzü kodları doğrudan SQL sorgusu çalıştıramaz. Tüm veritabanı işlemleri `app/services/` altındaki servisler tarafından yürütülür. Servisler ise hiçbir PyQt5 bileşenini import edemez.
3. **Şema değişikliği yeni migrasyondur:** Veritabanı şemasında yapılacak herhangi bir değişiklik doğrudan veritabanında değil, `app/db/migrations/` altında sıralı numaralandırılmış bir `.sql` dosyası olarak yazılmalı ve `PRAGMA user_version` artırılmalıdır.
4. **Her hata için önce test:** Düzeltilecek her hata (özellikle Bölüm 3'teki B1-B8 hataları) için önce hatayı yeniden üreten ve başarısız olan bir test yazılmalıdır; ardından düzeltme yapılıp testin geçtiği doğrulanmalıdır.
5. **Kullanıcı metinleri Türkçe:** Kullanıcıya görünen tüm etiketler, butonlar, hata bildirimleri, durum mesajları ve belgeler anlaşılır Türkçe olmalıdır. Kod tanımlayıcıları tutarlı ASCII olmalıdır (`urun`, `siparis`, `musteri` vb.).
6. **İşlem atomikliği (Transaction):** Tüm veritabanı yazma işlemleri tek bir transaction içinde yürütülmelidir. Hata oluştuğunda hiçbir kısmi yazma kalmamalı, tam geri alma (rollback) yapılmalıdır.
7. **Veri kaybı sıfır tolerans:** Orijinal veritabanındaki hiçbir kayıt silinmeyecek, migrasyon ile eksiksiz yeni şemaya taşınacaktır.
