"""
Harici Kütüphane (AST ve Radon) Uyumsuzluğu Entegrasyon Testleri.

Bu dosyada, ASTAnalyzer'ın (yerleşik 'ast' modülünü kullanır) ürettiği kod parçalarının, 
ComplexityCalculator'ın (harici 'radon' kütüphanesini kullanır) beklediği syntax ile 
çakışıp çakışmadığı test edilecektir. KOD YAZILMAMIŞTIR.

Test Edilecek Senaryolar (Kavramsal Olarak):
-------------------------------------------
1. Eksik Girinti (IndentationError) Simülasyonu:
   - GIVEN: Sınıf içinde (class) tanımlanmış ve ekstra girintili iç içe bir metot.
   - WHEN : ASTAnalyzer bu metodu ayrıştırıp (parse) 'body' string'ini çıkarır. 
            Sonra bu 'body' string'i ComplexityCalculator'a gönderilir.
   - THEN : Çıkarılan metin parçası (snippet), radon kütüphanesi tarafından 
            SyntaError veya IndentationError fırlatmadan geçerli bir Python kodu 
            olarak okunabilmeli ve karmaşıklığı hesaplanabilmelidir.

2. Dekorator ve Async/Await Uyumluluğu:
   - GIVEN: "@staticmethod" ile işaretlenmiş "async def" bir fonksiyon.
   - WHEN : Analizörden geçip radon'a aktarılır.
   - THEN : Radon bu modern Python sözdizimlerini (syntax) başarıyla işleyebilmelidir.
"""
