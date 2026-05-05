"""
Dosya Sistemi (I/O) ve İşletim Sistemi Uyum Entegrasyon Testleri.

Bu dosyada, kodun diske okuma ve yazma işlemlerinde işletim sisteminin 
(Windows/Linux) verdiği gerçek tepkiler test edilecektir. KOD YAZILMAMIŞTIR.

Test Edilecek Senaryolar (Kavramsal Olarak):
-------------------------------------------
1. İzin Hatalarının (PermissionError) Gerçek Simülasyonu:
   - GIVEN: İşletim sisteminde okuma/yazma izni olmayan bir klasör oluşturulur.
   - WHEN : Scanner bu klasörü taramaya veya Exporter bu klasöre JSON yazmaya çalışır.
   - THEN : Kodun bu durumu sessizce (çökmeden) atlatıp atlatmadığı, logların 
            doğru düşüp düşmediği gerçek disk operasyonuyla teyit edilir.

2. İstenmeyen Dizinlerin Filtrelenmesi (__pycache__ vb.):
   - GIVEN: Diskte gerçek bir __pycache__ dizini ve içine derlenmiş .pyc veya .py dosyası konur.
   - WHEN : Scanner.run() çağrılır.
   - THEN : Sistem bu dosyaları fiziksel olarak okumamalı (es geçmeli).

3. Eksik Çıktı (Output) Dizininin Kendiliğinden Oluşması:
   - GIVEN: Disk üzerinde "benchmark_outputs" klasörü fiziksel olarak silinir.
   - WHEN : Exporter.export() ilk kez çalışır.
   - THEN : Sistem çökmemeli; "benchmark_outputs" klasörünü işletim sistemine 
            kendi kendine (mkdir(parents=True)) başarıyla oluşturmalıdır.
"""
