"""
Komut Satırı (CLI) ve Uygulama Başlatma E2E Testleri.

Bu dosyada uygulamanın dış dünyadan (terminalden) nasıl tetiklendiği ve 
sistemin komutlara verdiği genel (kara-kutu) tepkiler test edilir.
KOD YAZILMAMIŞTIR.

Kesin Test Edilmesi Gereken Senaryolar:
---------------------------------------
1. Başarılı Tam Çalışma (Exit Code 0):
   - GIVEN: Geçerli ve okunabilir bir benchmark klasörü mevcut.
   - WHEN : 'python src/main.py' (veya benzeri ana giriş komutu) subprocess ile çağrılır.
   - THEN : Süreç (process) çökmeden tamamlanmalı ve sistem 0 (Success) çıkış kodu döndürmeli.

2. Hatalı Parametre veya Klasör Yokluğu (Exit Code 1+):
   - GIVEN: 'olmayan_klasor' adında geçersiz bir dizin parametresi verilir.
   - WHEN : Ana uygulama başlatılır.
   - THEN : Sistem yığılmadan (stacktrace basmadan) kullanıcıya zarif bir 
            "Klasör bulunamadı" hatası vermeli ve hata kodu (örn: 1) ile sonlanmalı.
"""
