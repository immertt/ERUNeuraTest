Research & Strategy: ChatUniTest and LLM Test Generation Papers (#32)
Bu çalışma, LLM tabanlı birim test üretiminde kullanılan akademik ve endüstriyel stratejilerin teknik derinliğini incelemeyi, literatürdeki yaklaşımları karşılaştırmayı ve en etkili hibrit modelin seçim sürecini deneysel verilerle gerekçelendirmeyi amaçlamaktadır.
1. Literatürde Uygulanan Stratejiler
Akademik makaleler (ChatUniTest, TESTPILOT, Test4Py, RUG vb.), LLM'lerin birim testi üretimindeki zayıflıklarını gidermek için şu temel stratejileri uygulamaktadır:
A. Kademeli ve Uyarlanabilir Bağlam Yönetimi (Adaptive Prompting)
•	Aşamalı Bilgi Ekleme (TESTPILOT): Başlangıçta sadece imza verilir; başarısızlık durumunda adım adım gövde, dokümantasyon ve kullanım örnekleri (usage snippets) eklenir.
•	Uyarlanabilir Odak Bağlamı (Adaptive Focal Context - ChatUniTest): Token sınırlarını aşmamak için bağlam dinamik yönetilir; en az ilişkili bilgiler (gürültü) akıllıca çıkarılır.
•	Aşağıdan Yukarıya İnşa (Bottom-Up - RUG): Bağımlı alt problemlerden yukarıya doğru hiyerarşik bir bağlam inşa edilir.
B. Gelişmiş İstem Mühendisliği ve Akıl Yürütme Modelleri
•	Düşünce Zinciri (Chain-of-Thought - CoT): LLM’e doğrudan test üretimi yaptırmak yerine; önce kodu analiz etmesi ve adım adım akıl yürütmesi sağlanır.
•	Düşünce Ağacı (Tree-of-Thought - ToT): Üç farklı sanal "test uzmanı" ajanı arasındaki tartışma ile en kaliteli test paketi birleştirilir.
o	Kritik Not: Tree-of-Thought (ToT) yaklaşımı bu deneysel çalışmada doğrudan uygulanmamıştır. Bunun nedeni, tek fonksiyonlu birim test üretimi senaryolarında fazla hesaplama maliyeti oluşturması ve CoT + context yapısına göre gereksiz derecede karmaşık olmasıdır.
C. Program Analizi ile Anlamsal Tip Çıkarımı (Test4Py)
•	Davranış Odaklı Parametre Çıkarımı (BGPI): Python gibi dinamik dillerde halüsinasyonu engellemek için kodun Call Graph'ı üzerinden parametrelerin fonksiyon içindeki davranışları analiz edilir.
2. Stratejik Değerlendirme ve Seçim Kararı
Seçim Kararı: Bu çalışma kapsamında en uygun yaklaşım olarak “Chain-of-Thought + Adaptive Context + Repair Döngüsü” hibrit modeli seçilmiştir.
CoT, modelin test üretmeden önce fonksiyonun davranışını açık bir analiz adımı ile modellemesini sağlar. Adaptive Context, gereksiz veya düşük ilişkili bilgilerin filtrelenmesiyle token verimliliğini artırır. Repair döngüsü ise üretim sonrası derleme ve mantık hatalarını geri besleme ile düzeltir. Bu üçlü yapı birlikte hem üretim aşamasında çeşitliliği hem de doğrulama aşamasında güvenilirliği artırdığı için tek başına ToT veya sadece Meta filtreleme yaklaşımına göre daha dengeli bir çözümdür.
3. Deneysel Uygulama ve Kıyaslama (Branch Coverage Analizi)
Strateji değişikliğinin etkisini ölçmek için mantıksal dallanma içeren discount fonksiyonu kullanılmıştır.

```python
def discount(price, is_student):
    return price * 0.9 if is_student else price

Uygulama A: Basit Prompt (Sadece "Test Üret" Komutu)
•	Baseline Açıklaması: Bu temel senaryoda LLM’e herhangi bir akıl yürütme veya bağlam desteği verilmemiştir. Model yalnızca fonksiyonun ana çalışma yoluna (happy path) odaklanarak minimal bir test üretmiştir.
•	Eksik: is_student=False durumu ve sınır değerler (price=0) kapsanmaz.
Uygulama B: Hibrit Strateji (Seçilen Yöntem: CoT + Context)
•	Analiz Adımı (CoT): LLM önce fonksiyonun iki farklı dalı (branch) olduğunu ve price değişkeninin sayısal kısıtlarını analiz eder.
•	Üretilen Testler:
1.	test_student_discount (True durumu)
2.	test_regular_price (False durumu)
3.	test_zero_price (Edge case / Sınır değer)
4.	test_small_positive_price (Örn: price = 0.01)
Metrik	Basit Prompt	Hibrit Strateji (Seçilen)
Üretilen Test Sayısı	1	4
Dal Kapsamı (Branch Coverage)	yaklaşık %50	yaklaşık %90 ve üzeri (branch coverage artışı gözlemlendi)
Edge Case Keşfi	Yok	Gözlemlendi (0 ve küçük pozitif değerler üzerinden)
Analiz/Planlama	Yok	Var

4. Genel Değerlendirme ve Uygulama Tavsiyesi
Bu çalışma göstermektedir ki LLM tabanlı test üretiminde yalnızca model gücü yeterli değildir. Yapılandırılmış bağlam sağlanması, dal kapsamını (branch coverage) ve köşe durum (edge case) tespit başarısını belirgin şekilde artırmaktadır. Bu nedenle prompt mühendisliği, test üretim kalitesinde kritik bir rol oynamaktadır. Araştırma ve analiz sonucunda kurulan "Araştırma → Analiz → Seçim" zinciri şu prensiplere dayanmaktadır:
1.	Bağlam Yönetimi: Halüsinasyonu azaltmak için usage snippets ve bağlamsal tip bilgileri kritik rol oynar.
2.	Akıl Yürütme: CoT ile modelin önce "mantıksal harita" çıkarması sağlanmalıdır.
3.	Onarım (Repair): Başarısız testlerde terminal hatasıyla modele geri dönülmelidir.
4.	Kalite Filtresi: Meta’nın endüstriyel doğrulama standartlarına benzer şekilde, sadece kapsamı artıran ve derlenen testler kabul edilmelidir.

5. Mevcut Testler Üzerinde Strateji Uygulaması (Rewriting Analysis)
Bu bölümde, daha önce üretilmiş basit birim testlerin (baseline) LLM tabanlı stratejiler (CoT + Adaptive Context) ile nasıl genişletildiği gösterilmiştir.
A. Önceki Basit Test (Baseline – Stratejisiz Üretim)

```python
def test_basic():
    assert is_even(4) == True
Analiz:
•	Sadece tek giriş değeri (4) 
•	Sadece “happy path” doğrulaması 
•	Fonksiyon davranışının tamamını temsil etmiyor 
•	Negatif, sıfır ve tek sayı durumları yok 
•	Branch coverage düşük 
B. Strateji Uygulandıktan Sonra (CoT + Context Rewriting)
Strateji uygulandığında LLM önce fonksiyonun davranışını analiz etmiş, ardından eksik dalları tamamlamıştır.

def test_even_number():
    assert is_even(4) == True

def test_odd_number():
    assert is_even(3) == False

def test_zero():
    assert is_even(0) == True

def test_negative_number():
    assert is_even(-2) == True
    
C. Stratejik Dönüşümün Etkisi (Before → After)
Özellik	Baseline Test	Strateji Sonrası
Test Sayısı	1	4
Senaryo Kapsamı	Tek durum	Çoklu durum
Edge Case	Yok	Var
Negatif Sayılar	Yok	Var
Sıfır Durumu	Yok	Var
Branch Coverage	Düşük	Yüksek

D. Gözlemlenen Temel Dönüşüm
Bu uygulama göstermektedir ki:
•	LLM yalnızca “test yaz” şeklinde yönlendirildiğinde yüzeysel test üretmektedir. 
•	Ancak CoT + Context kullanıldığında model: 
o	fonksiyonun karar noktalarını analiz eder 
o	eksik branch’leri tespit eder 
o	test setini yeniden yapılandırır (test rewriting) 
Bu durum, LLM’in sadece “üretici” değil aynı zamanda mevcut testleri genişleten (test augmenter) olarak kullanılabileceğini göstermektedir.
E. Sonuç (Genişletilmiş)
LLM tabanlı test üretiminde en kritik kazanım, yeni test üretmekten ziyade mevcut testleri stratejik olarak genişletebilme kapasitesidir.
Bu nedenle en etkili yaklaşım:
“Generate → Analyze → Rewrite → Expand”
pipeline’ıdır.
