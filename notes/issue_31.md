# 31 - Research Report: LLM-based Unit Test Generation & Software Quality Metrics
1. LLM'lere Sağlanması Gereken Zenginleştirilmiş Bağlam (Context)
Büyük dil modellerinin (LLM) derlenebilir, anlamsal olarak doğru ve yüksek kapsamlı birim testleri üretebilmesi için sadece fonksiyon adını vermek yeterli değildir. Literatürdeki TESTPILOT, Test4Py, RUG ve ChatUniTest sistemlerine göre şu zenginleştirilmiş bağlam bilgileri (context) sağlanmalıdır:
A. Temel Kod ve Yapı Bilgileri
•	Metot İmzası ve Gövdesi: Test edilecek metodun (focal method) tam kaynak kodu ve parametre listesi.
•	Focal Class Bağlamı: Metodun ait olduğu ana sınıfın içindeki diğer metotlar, sınıf alanları (fields) ve yapıcı metotlar (constructors). Bu, modelin nesne durumunu anlamasını sağlar.
•	Modül Konumları (Module Location): LLM'in üretilen test koduna doğru içe aktarma (import) ifadelerini yazabilmesi için ilgili sınıfların dosya/modül yolları.
B. Dokümantasyon ve Semantik Veriler
•	Kullanım Örnekleri (Usage Snippets): Modelin API'yi nasıl kullanacağını anlaması için proje dokümantasyonundan veya diğer modüllerden çıkarılmış gerçek kod örnekleri.
•	Dokümantasyon Yorumları: Javadoc/Pydoc benzeri, metodun ne işe yaradığını açıklayan yorum satırları (doc comments).
•	Semantik Özetler ve Çağrı Grafiği (Call Graph): Fonksiyonun proje içinde nerelerden çağrıldığı (caller) ve neleri çağırdığı (callee). Bu, parametrelerin anlamsal amacını (örn. bir tamsayının sadece sayı değil, bir veritabanı ID'si olduğu) kavramayı sağlar.
C. Bağımlılık ve Tip Çözümleme
•	Bağımlılık İmzaları: Metodun kullandığı parametrelerin tipleri, bu tiplerin yapıcı (constructor) imzaları ve arayüz/trait tanımları.
•	İç Tipler: Gerekli iç tiplerin (inner types) ve fonksiyonun çağırdığı diğer bağımlı sınıfların imzaları.
2. Test Üretiminde Karşılaştırmalı Senaryo Analizi
E-ticaret sistemindeki indirimi_uygula(sepet, kullanici) fonksiyonu üzerinden yapılan simülasyon sonuçları:
Durum 1: Temel İstem (Sadece "Test Üret" Komutu)
•	İçe Aktarma Sorunları: Modül yolu bilinmediği için ModuleNotFoundError riski yüksektir.
•	Mocking Hataları: LLM, nesne yapılarını bilmediği için MockSepet gibi sahte sınıflar uydurur. Bu durum gerçek projede AttributeError veya TypeError ile sonuçlanır.
•	Anlamsal Zayıflık: Model genellikle en bariz tek bir "mutlu yolu" (happy path) test eder; iş mantığını sığ bir şekilde ölçer.

```python
import unittest
from main import indirimi_uygula

class TestIndirimiUygula(unittest.TestCase):
    def test_basic(self):
        class MockSepet:
            def toplam_tutar(self):
                return 100

        class MockKullanici:
            def premium_mu(self):
                return True

        self.assertEqual(indirimi_uygula(MockSepet(), MockKullanici()), 80)

•  Mock object kullanımı 
•  gerçek dependency yok 
•  tek test case 
•  sınırlı coverage

Durum 2: Zenginleştirilmiş İstem (Literatür Yöntemi)
•	Gerçek Nesne Başlatımı: Sağlanan constructor bilgileri ve kullanım örnekleri ile gerçek nesneler (Sepet, Kullanici) başlatılır.
•	Dal Kapsamı (Branch Coverage): Fonksiyonel özet sayesinde "Premium" ve "Standart" kullanıcı ayrımı fark edilir, tüm if-else yolları test edilir.
•	Yüksek Değerli Doğrulama (Non-trivial Assertion): Kullanım senaryosuna sadık kalarak, anlamlı hata mesajları içeren çok daha güvenilir doğrulamalar kurgulanır.


```python
import unittest
from e_ticaret.siparis import indirimi_uygula
from e_ticaret.modeller import Sepet, Urun
from e_ticaret.kullanici import Kullanici

class TestIndirimiUygula(unittest.TestCase):

    def test_premium_kullanici(self):
        sepet = Sepet([Urun("Laptop", 1000)])
        user = Kullanici("Ahmet", "Premium")

        self.assertEqual(indirimi_uygula(sepet, user), 800)

    def test_standart_kullanici(self):
        sepet = Sepet([Urun("Mouse", 100)])
        user = Kullanici("Mehmet", "Standart")

        self.assertEqual(indirimi_uygula(sepet, user), 100)

•  gerçek object instantiation 
•  doğru import resolution 
•  branch coverage artışı 
•  semantic assertion


3. Kapsam (Coverage) ve Kalite Metrikleri
Kapsam, testlerin kodu ne kadar tetiklediğini ölçen temel bir kavram ve hesaplanabilir bir anlambilim göstergesidir (proxy).
A. Temel Kapsam Metrikleri
•	Satır/İfade Kapsamı (Line/Statement Coverage): Kaynak koddaki yürütülebilir ifadelerin yüzde kaçının tetiklendiğini ölçer.
•	Dal Kapsamı (Branch Coverage): Karar noktalarının (if-else, döngüler) her iki durumunun da test edilme oranıdır. Hata fırlatma durumları veya istisnaların test edilmesini gerektirdiği için ulaşılması en zor metriktir.
•	Fonksiyon/Kod Bölgesi Kapsamı: Fonksiyonların veya özel sınırlandırılmış bölgelerin (region) en az bir kez çağrılıp çağrılmadığına odaklanır.
B. Kalite ve Başarı Metrikleri
•	Mutasyon Skoru (Mutation Score): Kodda yapılan yapay hataların (mutantlar) test paketi tarafından tespit edilme oranıdır. Salt kod kapsamına kıyasla testin hata yakalama gücünü gösteren daha güvenilir bir metriktir.
•	Derlenme ve Geçme Oranı (Compilation & Pass Rate): Üretilen testin sözdizimsel doğruluğu ve çökmeye neden olmadan testi başarıyla tamamlaması ölçülür.
•	Hata Tespit Etme Oranı (Bug Detection Rate): Üretilen birim testlerin yazılımdaki gerçek dünyada var olan hataları fiilen bulma yeteneği.
4. İleri Düzey Stratejiler ve Endüstriyel Standartlar
Uyarlanabilir Bağlam Yönetimi (Adaptive Focal Context)
Tüm bilgileri tek bir istemde yığmak token sınırlarını aşabilir ve modelin odak noktasını kaybetmesine (noise) yol açabilir.
•	Dinamik Seçim: Bilgilerin, token limitleri dâhilinde en az önemliden başlayarak elendiği bir strateji izlenmelidir.
•	Bottom-Up İnşa: Karmaşık tiplerin çözümlenmesi için problemi alt problemlere bölüp, bağımlılıklardan yukarıya doğru bağlam inşa edilmelidir.
İyileştirme Garantili Filtreleme (Meta Standartları)
Üretilen bir testi kod tabanına kabul etmeden önce 3 temel şart aranır:
1.	Derlenebilirlik (Builds): Mevcut altyapıda sorunsuz derleniyor mu?
2.	Güvenilirlik (Passes): Aynı test peş peşe (örn. 5 kez) çalıştırıldığında her seferinde başarılı olup flaky (kararsız) olmadığını kanıtlamalıdır.
3.	Kapsam Artışı (Improves Coverage): Bu yeni test, mevcut testlerin kapsamadığı yeni bir satırı veya dalı kapsıyor mu? Eğer sadece eski testleri tekrar ediyorsa elenir.
