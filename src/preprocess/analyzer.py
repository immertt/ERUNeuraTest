"""
AST tabanlı kod analiz modülü.

Python kaynak kodunu ast modülü ile parse eder, sınıf içi metotları
ve bağımsız fonksiyonları tespit ederek MethodModel nesnelerine dönüştürür.
Her metot için imza, gövde, parametreler, bağımlılıklar ve dekoratörler çıkarılır.
"""