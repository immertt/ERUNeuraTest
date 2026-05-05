"""
Çıktı (Output) ve Şema (Schema) Doğrulama E2E Testleri.

Bu dosyada, sistem çalışmasını bitirdikten sonra diske yazılan JSON verilerinin, 
Yapay Zeka (AI) modelleme ekibinin beklediği formatla (schema) birebir 
uyuşup uyuşmadığı test edilir.
KOD YAZILMAMIŞTIR.

Kesin Test Edilmesi Gereken Senaryolar:
---------------------------------------
1. Şema (Schema) Uyumluluğu:
   - GIVEN: Sistem çalıştırılmış ve 'benchmark_outputs/ornek_proje.json' dosyası üretilmiş.
   - WHEN : Bu dosya diske yazıldıktan hemen sonra test tarafından okunur.
   - THEN : Dosyanın içindeki JSON verisi, projenin resmi JSON Şeması'na (Pydantic 
            veya JSON Schema) harfi harfine uymalıdır. Eksik key veya yanlış veri tipi olmamalıdır.

2. Veri Mantığı ve İçerik Kontrolü:
   - GIVEN: Geçerli kodlardan üretilmiş JSON dosyası.
   - WHEN : JSON içeriği parse edilerek incelenir.
   - THEN : JSON içindeki metotların 'complexity' değerleri mantıklı (sıfırdan büyük) 
            olmalı ve kod satır sayıları (line_count) ile 'body' (gövde) satırları tutarlı olmalıdır.
"""
