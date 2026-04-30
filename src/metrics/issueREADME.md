Test Kapsamları (Coverages)

1. Satır Kapsamı (Line Coverage)
Yazdığımız testler çalışırken, kaynak koddaki toplam satırların yüzde kaçının üzerinden geçildiğini ölçer.
Projenin test edilmemiş "kör noktalarını" bulmanın en hızlı ve en ucuz yoludur. Bir satır hiç çalıştırılmamışsa, o satırdaki bir hatanın testler tarafından yakalanma ihtimali sıfırdır.
Kod izleyiciler (örneğin Python'da coverage.py), kod çalışırken arka planda hangi satırların belleğe yüklendiğini işaretler. 
Formül: (Çalıştırılan Satır / Toplam Çalıştırılabilir Satır) * 100.

2. Dal Kapsamı (Branch Coverage)
Kodda bulunan karar yapılarının (if, elif, else, while, catch) tüm olası yollarının (True ve False durumları) test edilip edilmediğini ölçer.
Yüzde 100 satır kapsamı, kodun tamamen güvenli olduğu anlamına gelmez. Gizli mantıksal hataları (edge cases) yakalamak için dallara girmeyen senaryoları da test etmeniz gerekir.

3. Satır Kapsamı (Line Coverage) ve Dal Kapsamı (Branch Coverage) örnek

# islem.py
def sum(a, b):
    result = a + b        # 1. Satır
    if result < 0:        # 2. Satır (Karar noktası)
        result = 0        # 3. Satır
    return result         # 4. Satır

Şimdi bu koda sadece şu testi yazılır:

# test_islem.py
def test_sum():
    # -2 ile -3'ü toplarsak -5 eder. Fonksiyon bunu 0 yapmalı.
    assert sum(-2, -3) == 0

Bu test çalıştığında metrikler :

Satır Kapsamı (Line Coverage): %100
Çünkü kod çalışırken Python sırasıyla 1, 2, 3 ve 4. satırların üzerinden geçti. Hiçbir satır atlanmadı. Görünüşe göre her şey mükemmel.

Dal Kapsamı (Branch Coverage): %50
Çünkü if sonuc < 0 ifadesi bir yol ayrımıdır. Bizim testimizde sonuç -5 çıktığı için if koşulu True (Doğru) oldu ve içeri girildi. Ancak if koşulunun False (Yanlış) olduğu durumu, yani sonucun 0'dan büyük olduğu normal bir toplama işlemini (örn: guvenli_topla(2, 3)) hiç test etmedik.Herhangi biri kodu yanlışlıkla return 0 olarak bozsaydı pozitif sayılar da hep 0 dönecekti ama biz bunu test etmediğimiz için fark etmeyecektik bu yüzden tehlikelidir.

Akademik literatürde ve endüstri standardı araçlarda (örn. SonarQube, Codecov, Coveralls) metrik seçimleri genellikle hız ve etkililik dengesine (trade-off) göre yapılır.

Sektör Standardı (Araçlar): CI/CD süreçlerinde (Sürekli Entegrasyon) genellikle Satır ve Dal Kapsamı (Line + Branch Coverage) kullanılır. Çünkü coverage.py veya Java'daki JaCoCo gibi araçlar bu metrikleri milisaniyeler içinde hesaplayabilir. Kaynak tüketimleri çok düşüktür.

Akademik Literatür (Makaleler): Yazılım mühendisliği araştırmalarında testlerin kalitesini kanıtlamak için her zaman Mutasyon Skoru (Mutation Score) "altın standart" olarak kabul edilir. Araştırmacılar, "Benim önerdiğim yapay zeka algoritması daha iyi test yazıyor" diyebilmek için yapay zekanın yazdığı testlerin kaç tane mutantı öldürdüğüne bakarlar. Çünkü yüksek satır kapsamı, testin içinde assert (doğrulama) olduğu anlamına gelmez. Sadece kodun o satırından geçildiğini garanti eder.

4. Mutasyon Testi (Mutation Testing)

Satır ve dal kapsamı kodunuzu değerlendirirken, Mutasyon Testi yazdığımız testlerin kalitesini değerlendirir.Eğer testlerimiz gerçekten iyiyse, koddaki bir mantığı kasıtlı olarak bozduğumda testlerim bu bozulmayı fark edip "başarısız" (FAIL) olmalıdır.

Mutant: Kaynak kodun kasıtlı olarak küçük bir değişikliğe uğratılmış (bozulmuş) kopyasıdır. (Örneğin a + b işleminin a - b yapılması).

Killed: Testleriniz mutant kod üzerinde çalıştırıldığında hata verirse (FAIL), testiniz değişikliği yakalamış demektir. Mutant öldürülmüştür.

Survived : Testleriniz bozuk koda rağmen başarıyla geçerse (PASS), testiniz kördür. Mutant hayatta kalmıştır. Bu kötü bir şeydir, o bölgeye daha iyi bir assert yazmamız gerekir.

5. Mutasyon Testi (Mutation Testing) örnek
def is_adult(age):
    return age >= 18

mutmut aracı arka planda kodunuzun AST'sini (Abstract Syntax Tree) alır ve şu mutantları üretir:

Mutant 1: return age > 18 (>= işareti > yapıldı)

Mutant 2: return age <= 18

Mutant 3: return age >= 19

Eğer  sadece test_is_adult(25) (sonuç True) ve test_is_adult(10) (sonuç False) yazdıysanız, Mutant 1 hayatta kalacaktır. Çünkü 25, 18'den de büyüktür, test bu ince hatayı yakalayamaz. Mutant 1'i öldürmek için sınır değer testi (Boundary Value Analysis) olan test_is_adult(18) yazılması gerektiğini anlardık.