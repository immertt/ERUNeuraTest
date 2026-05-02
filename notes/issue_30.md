# 30 - Research on Unit Testing Frameworks and LLM-based Test Generation

1. Unit Testing Frameworks in Python
Python ekosisteminde birim test yazımı için iki temel yapı bulunmaktadır:

1.1. unittest (Standard Library)
Python’un standart kütüphanesinde bulunan, xUnit mimarisine dayanan klasik bir frameworktür. Testler class yapısı içinde yazılır ve unittest.TestCase sınıfından miras alınır.

```python
import unittest

def add(a, b):
    return a + b

class TestAdd(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()

1.2. pytest (Modern & Functional)
Modern projelerde daha sık tercih edilen, fonksiyon tabanlı ve daha az "boilerplate" kod gerektiren bir frameworktür.

def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
    
2. Best Practices: İyi Bir Unit Test Nasıl Yazılır?
Kaliteli bir birim test, literatürde kabul görmüş AAA (Arrange – Act – Assert) paternini takip etmelidir:

Arrange (Setup/Hazırlık): Test için gerekli giriş verilerinin ve ortamın hazırlanması.

Örnek: nums1 = [1,2]; expected = 3

Act (Execution/Eylem): Test edilen fonksiyonun veya metodun çağrılması.

Örnek: result = add(nums1)

Assert (Oracle/Doğrulama): Beklenen davranışın ve sonucun doğrulanması.

Örnek: assert result == expected

İyi bir test ayrıca; Normal durumları, Edge case (sınır) durumlarını ve Hata (Exception) senaryolarını kapsamalıdır.

3. Literatürde LLM ile Test Üretimi Yaklaşımları
Akademik çalışmalarda LLM tabanlı test üretimi için önerilen temel modeller ve stratejiler:

CoCoEvo: Programlar ve testlerin eş evrimsel (co-evolution) olarak geliştirilmesini önerir.

CasModaTest: Test üretimini iki aşamaya ayırır: Test Prefix (girdi üretimi) ve Test Oracle (assert üretimi).

ChatUniTest: "Generation → Validation → Repair" döngüsünü (üretim, doğrulama ve hata varsa geri bildirimle onarım) kullanır.

HITS: Karmaşık metodları "method slicing" ile küçük parçalara ayırarak daha yüksek coverage (kapsam) elde etmeyi hedefler.

Pynguin: Search-based software testing ve genetik algoritmalar kullanarak test üretimine odaklanır.

4. Gelişmiş İstem Mühendisliği ve Bağlam Yönetimi
LLM'lerin potansiyelinden tam yararlanmak için sadece "test yaz" demek yerine şu stratejiler uygulanmalıdır:

Zengin Bağlam (Adaptive Focal Context): Yalnızca fonksiyonun imzasını değil; kaynak kodunu, dokümantasyon yorumlarını ve bağlı olduğu sınıf yapısını isteme (prompt) dahil edin.

Few-Shot Learning: Modele hedef projedeki mevcut, yüksek kaliteli birim testlerinden örnekler sunarak doğru formatı anlamasını sağlayın.

Chain-of-Thought (CoT): Modelden önce metodun işlevini özetlemesini, ardından test adımlarını planlamasını ve en son kodu yazmasını isteyin.

Tree-of-Thought (ToT): Farklı "sanal test uzmanları" oluşturup, her birinin sınır durumlarını bağımsızca düşünmesini sağlayarak tek bir test sınıfı oluşturun.

5. İteratif Doğrulama ve Onarım (Validation-Repair)
LLM'ler halüsinasyon yapabileceği için bir doğrulama döngüsü kurulmalıdır:

RetryWithError: Üretilen test kodunu çalıştırın. Eğer hata verirse, bu hata mesajını modele geri göndererek kodu düzeltmesini isteyin.

Kural Tabanlı Onarım: Eksik içe aktarma (import) ifadeleri gibi basit hataları kural tabanlı araçlarla düzeltin.

Mutasyon Testi: Testlerin gerçekten hata yakalayıp yakalamadığını görmek için koda yapay hatalar (mutantlar) ekleyin ve testlerin bunları "öldürüp öldürmediğini" kontrol edin.

6. Sonuç ve Kabul Kriterleri (Meta Standartları)
Üretilen bir testin kod tabanına kabul edilmesi için şu 3 şart aranmalıdır:

Derlenebilirlik (Builds): Sorunsuz derleniyor mu?

Güvenilirlik (Passes): Tutarlı bir şekilde (non-flaky) geçiyor mu?

Kapsam Artışı (Improves Coverage): Yeni bir satırı veya dalı kapsıyor mu?