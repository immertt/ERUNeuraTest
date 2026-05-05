"""
Gerçek Dünya Projeleri (Real-World) ve Performans E2E Testleri.

Bu dosyada sistemin açık kaynaklı, devasa ve standart dışı (kirli) kod içeren 
gerçek projelere nasıl dayandığı test edilir.
KOD YAZILMAMIŞTIR.

Kesin Test Edilmesi Gereken Senaryolar:
---------------------------------------
1. Devasa Kod Tabanı (Stress Test):
   - GIVEN: İçerisinde 10.000+ satır kod barındıran gerçek bir repo (Örn: Requests, Flask kopyası).
   - WHEN : Sistem bu repo üzerinde çalıştırılır.
   - THEN : Sistem RAM'i (memory leak) tüketmeden, makul bir süre içerisinde (örn: max 1 dakika) 
            süreci tamamlamalı ve en iyi/karmaşık 50 metodu başarıyla ayıklayabilmelidir.

2. Kirli ve Standart Dışı Kodlara Dayanıklılık (Robustness):
   - GIVEN: İçinde Unicode hataları, Syntax error'lar ve sonsuz özyinelemeli (recursive) 
            bozuk dosyalar bulunan bir proje dizini.
   - WHEN : Sistem ana tetikleyici ile çalıştırılır.
   - THEN : Bozuk dosyalar sistemi durdurmamalı, sadece hatalı dosyalar atlanarak 
            sağlam dosyalardan json çıktısı üretilmeye devam edilmelidir.
"""
