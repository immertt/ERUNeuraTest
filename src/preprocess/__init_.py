"""
Preprocess Modülü - Benchmark projelerini analiz ederek her projeden 50 metot seçer.

Pipeline: Scanner → Analyzer → ComplexityCalculator → Selector → Exporter
Çıktı: output/selected_methods/<proje_adı>_methods.json
"""