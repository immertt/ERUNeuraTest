"""
TestMethodSelector — MethodSelector sınıfının tüm metotları için kapsamlı test sınıfı.

Kapsam:
  - __init__, select_best_methods, _rank_by_complexity metotları
  - Her metot için Defect / Infection / Failure analizi (Görev 1-4)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""

import pytest
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.selector import MethodSelector


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def make_method(name="foo", cyclomatic=1, cognitive=1, line_count=10):
    """Verilen complexity değerleriyle sahte MethodModel oluşturur."""
    m = MagicMock()
    m.name = name
    m.complexity = MagicMock()
    m.complexity.cyclomatic_complexity = cyclomatic
    m.complexity.cognitive_complexity = cognitive
    m.line_count = line_count
    return m


def make_selector(limit=50) -> MethodSelector:
    return MethodSelector(limit=limit)


# ===========================================================================
# __init__
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     __init__ içinde limit değeri hiç doğrulanmıyor:
#
#         self.limit = limit
#
#     limit=-1 girildiğinde self.limit=-1 olarak atanır.
#     Daha sonra select_best_methods içinde:
#
#         return ranked[:-1]
#
#     Python slice semantiğine göre ranked[:-1], son eleman HARİÇ tüm listeyi
#     döndürür. "En karmaşık -1 metodu seç" anlamsız olmakla birlikte
#     uygulama sessizce yanlış sonuç üretir; hata fırlatmaz.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     limit negatif bir tam sayı (örn. -1, -5) ile MethodSelector oluşturulmalı
#     ve ardından select_best_methods çağrılmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_negative_limit_when_init_should_fail_silently_returning_wrong_slice
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestInit:

    def test_given_negative_limit_when_init_should_fail_silently_returning_wrong_slice(self):
        """
        GIVEN: limit=-1 ile MethodSelector oluşturuluyor
        WHEN : select_best_methods çağrılır
        THEN : ValueError fırlatılmalı VEYA boş liste dönmeli (0 metot seçilmeli)
               Orijinal kodda ranked[:-1] → son eleman hariç tümü döner → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        selector = MethodSelector(limit=-1)
        methods = [make_method(f"m{i}", cyclomatic=i) for i in range(1, 6)]

        result = selector.select_best_methods(methods)

        # Beklenen: ValueError (init'te) ya da boş liste (0 metot seçilmeli)
        # Orijinal: son 1 eleman hariç tüm liste (4 eleman) döner
        assert len(result) == 0, (
            f"limit=-1 için 0 metot bekleniyor ama {len(result)} döndü. "
            f"ranked[:-1] yanlış slice üretiyor — KUSUR aktif."
        )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: limit=None → ranked[:None] → tüm liste sessizce döner
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     limit=None geçildiğinde Python'da None tipinin truthy olması nedeniyle
    #     self.limit = None olarak atanır. Daha sonra ranked[:None] tüm listeyi
    #     döndürür — limit sanki sonsuzmuş gibi davranır. "Limit yok" ile
    #     "limit=None hatalı girdi" ayırt edilemez.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     limit=None ile oluşturulan selector, 100 metot içeren bir listeye
    #     uygulandığında 50 değil 100 metot döndürmelidir (orijinal davranış).
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_none_limit_when_select_should_fail_returning_all_methods(self):
        """
        GIVEN: limit=None ile MethodSelector oluşturuluyor, 10 metot var
        WHEN : select_best_methods çağrılır
        THEN : TypeError veya ValueError fırlatılmalı (None geçersiz limit)
               Orijinal kodda ranked[:None] → 10 metot döner (sınırsız) → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        selector = MethodSelector(limit=None)
        methods = [make_method(f"m{i}") for i in range(10)]

        with pytest.raises((TypeError, ValueError)):
            selector.select_best_methods(methods)

        # Orijinal kodda exception fırlatılmaz, 10 metot döner.
        # Bu test orijinal kodla BAŞARISIZ olur (exception bekleniyor ama gelmiyor).

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. limit pozitif bir tam sayıysa (ör. 50) self.limit=50 doğru
    #     atanır. Ne negatif slice ne de None slice devreye girer.
    #
    # (b) Test: geçerli pozitif limit → doğru atama

    def test_given_positive_limit_when_init_should_not_trigger_slice_defect(self):
        """
        GIVEN: limit=10 (geçerli pozitif tam sayı)
        WHEN : MethodSelector oluşturulur
        THEN : self.limit=10 doğru atanır, slice kusurları tetiklenmez

        [GÖREV 2b — negatif/None slice kusurları tetiklenmez]
        """
        selector = MethodSelector(limit=10)
        assert selector.limit == 10

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. limit=-1 atandı (kusur çalıştı) ama select_best_methods
    #     henüz çağrılmadıysa yanlış slice gerçekleşmez → durum bozulmaz.
    #     Kusur sadece __init__'te gizli, henüz aktif değil.
    #
    # (b) Test: limit=-1 atandı ama select çağrılmadan limit değeri kontrol edilir

    def test_given_negative_limit_when_only_attribute_read_no_infection_yet(self):
        """
        GIVEN: limit=-1 ile selector oluşturuldu
        WHEN : select_best_methods çağrılmadan sadece self.limit okunuyor
        THEN : self.limit=-1 görünür ama slice henüz gerçekleşmedi, infection yok

        [GÖREV 3b — kusur (yanlış atama) çalıştı, ama slice infection'ı henüz yok]
        """
        selector = MethodSelector(limit=-1)

        # Kusur: limit=-1 atandı. Ama select çağrılmadı → yanlış sonuç üretilmedi.
        assert selector.limit == -1  # Atama gerçekleşti, ancak henüz zararlı değil

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. limit=-1 ile 5 metot seçildiğinde ranked[:-1] = 4 metot döner
    #     (infection). Ama test yalnızca "sonuç boş değil mi?" kontrol ederse
    #     yanlış sayıyı görmez → failure yok.
    #
    # (b) Test: sadece len > 0 kontrol et

    def test_given_negative_limit_when_only_nonempty_result_checked_infection_hidden(self):
        """
        GIVEN: limit=-1 ile selector, 5 metot var (infection: 4 metot döner)
        WHEN : Yalnızca sonuç listesinin boş olmadığı kontrol edilir
        THEN : Test geçer — yanlış sayı görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        selector = MethodSelector(limit=-1)
        methods = [make_method(f"m{i}", cyclomatic=i) for i in range(1, 6)]
        result = selector.select_best_methods(methods)

        # Yüzeysel kontrol → infection gizleniyor
        assert len(result) >= 0  # Her zaman geçer; yanlış 4 eleman görünmüyor


# ===========================================================================
# SINIR DEĞER TESTLERİ — __init__
# ===========================================================================

class TestInitBoundaryValues:

    def test_given_default_limit_when_init_should_be_50(self):
        """
        GIVEN: limit parametresi verilmeden MethodSelector oluşturuluyor
        WHEN : __init__ çağrılır
        THEN : self.limit varsayılan olarak 50 olur
        """
        selector = MethodSelector()
        assert selector.limit == 50

    def test_given_limit_1_when_init_should_store_correctly(self):
        """
        GIVEN: limit=1 (minimum anlamlı pozitif değer)
        WHEN : __init__ çağrılır
        THEN : self.limit=1 olarak atanır
        """
        assert MethodSelector(limit=1).limit == 1

    def test_given_limit_0_when_select_should_return_empty_list(self):
        """
        GIVEN: limit=0
        WHEN : select_best_methods çağrılır
        THEN : Boş liste döner (ranked[:0] = [])

        Not: limit=0 Python slice'ta geçerlidir ve boş döndürür.
        Bu davranış belgelenmeli; sessiz başarısızlık riski var.
        """
        selector = MethodSelector(limit=0)
        methods = [make_method(f"m{i}") for i in range(5)]
        result = selector.select_best_methods(methods)
        assert result == []

    def test_given_very_large_limit_when_init_should_store_correctly(self):
        """
        GIVEN: limit=1_000_000 (çok büyük değer)
        WHEN : __init__ çağrılır
        THEN : self.limit doğru atanır
        """
        assert MethodSelector(limit=1_000_000).limit == 1_000_000

    def test_given_limit_equals_method_count_when_select_should_return_all(self):
        """
        GIVEN: limit tam metot sayısına eşit (limit=5, 5 metot var)
        WHEN : select_best_methods çağrılır
        THEN : Tüm metotlar döner
        """
        selector = MethodSelector(limit=5)
        methods = [make_method(f"m{i}") for i in range(5)]
        result = selector.select_best_methods(methods)
        assert len(result) == 5


# ===========================================================================
# select_best_methods
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     select_best_methods içinde:
#
#         ranked = self._rank_by_complexity(methods)
#
#     methods=None geçilirse _rank_by_complexity içindeki sorted(None, ...)
#     çağrısı TypeError fırlatır. Bu exception hiç yakalanmıyor → dışarıya sızar.
#     Doğru davranış: None girdi için ya erken return [] ya da ValueError.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     methods=None olmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_none_methods_when_select_should_fail_raising_type_error
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestSelectBestMethods:

    def test_given_none_methods_when_select_should_fail_raising_type_error(self):
        """
        GIVEN: methods=None
        WHEN : select_best_methods çağrılır
        THEN : Exception dışarıya sızmamalı; boş liste veya ValueError dönmeli
               Orijinal kodda sorted(None, ...) → TypeError dışarıya sızıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        selector = make_selector()

        try:
            result = selector.select_best_methods(None)
            # Buraya gelinirse None sessizce boş listeye çevrildi → kabul edilebilir düzeltme
            assert result == [], f"None için boş liste bekleniyor, {result} döndü"
        except TypeError:
            pytest.fail(
                "methods=None için TypeError dışarıya sızdı — "
                "select_best_methods None'ı yakalamıyor: KUSUR aktif"
            )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: complexity=None olan metot → AttributeError sızıyor
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     select_best_methods → _rank_by_complexity içindeki lambda:
    #
    #         key=lambda m: (
    #             m.complexity.cyclomatic_complexity + m.complexity.cognitive_complexity,
    #             m.line_count,
    #         )
    #
    #     m.complexity=None olan bir metot gelirse None.cyclomatic_complexity →
    #     AttributeError fırlatır. Tüm sıralama çöker, hiçbir metot dönmez.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     methods listesinde complexity=None olan en az bir MethodModel olmalı.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_method_with_none_complexity_when_select_should_fail_with_attribute_error(self):
        """
        GIVEN: complexity=None olan metot methods listesinde yer alıyor
        WHEN : select_best_methods çağrılır
        THEN : AttributeError dışarıya sızmamalı; hatalı metot atlanmalı veya
               ValueError ile bildirilmeli
               Orijinal kodda None.cyclomatic_complexity → AttributeError sızıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        selector = make_selector()

        bad_method = MagicMock()
        bad_method.name = "broken"
        bad_method.complexity = None  # complexity hesaplanmamış
        bad_method.line_count = 5

        good_method = make_method("good", cyclomatic=3, cognitive=2)

        try:
            result = selector.select_best_methods([bad_method, good_method])
            # Düzeltilmiş kod: bad_method atlanır, good_method döner
            assert "good" in [m.name for m in result], (
                "complexity=None olan metot atlanmalı, good_method sonuçta olmalı"
            )
        except AttributeError:
            pytest.fail(
                "complexity=None için AttributeError dışarıya sızdı — KUSUR aktif. "
                "Tüm sıralama çöktü."
            )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. methods=[] (boş liste) geçilirse sorted([]) hata fırlatmaz,
    #     [][:50] boş döner. None girdi kusuru ve complexity=None kusuru tetiklenmez.
    #
    # (b) Test: boş liste → hiçbir kusur tetiklenmez

    def test_given_empty_methods_when_select_should_not_trigger_any_defect(self):
        """
        GIVEN: methods=[] (boş liste)
        WHEN : select_best_methods çağrılır
        THEN : Boş liste döner, None/AttributeError kusurları tetiklenmez

        [GÖREV 2b — tüm kusurlar tetiklenmez]
        """
        selector = make_selector()
        result = selector.select_best_methods([])
        assert result == []

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. methods dolu, tüm complexity değerleri geçerli → sorted başarılı,
    #     slice doğru → durum bozulmaz. Kusurlu path (None/AttributeError için
    #     guard yok) çalıştı ama bu kez input temiz olduğundan infection yok.
    #
    # (b) Test: geçerli metotlar → normal akış

    def test_given_valid_methods_when_select_should_not_infect(self):
        """
        GIVEN: Tüm complexity değerleri geçerli, methods dolu
        WHEN : select_best_methods çağrılır
        THEN : Sıralama başarılı, doğru metotlar döner, durum bozulmaz

        [GÖREV 3b — None/AttributeError path'leri çalışmaz, infection yok]
        """
        selector = make_selector(limit=3)
        methods = [
            make_method("a", cyclomatic=5, cognitive=3),
            make_method("b", cyclomatic=2, cognitive=1),
            make_method("c", cyclomatic=8, cognitive=4),
            make_method("d", cyclomatic=1, cognitive=1),
        ]
        result = selector.select_best_methods(methods)
        assert len(result) == 3
        assert result[0].name == "c"  # en yüksek toplam: 12

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. complexity=None olan metot var (AttributeError sızıyor = infection).
    #     Ama test "exception fırlatıldı mı?" sormak yerine try/except içinde
    #     sonucu hiç kontrol etmeden geçerse infection görünmez.
    #
    # (b) Test: exception varlığını değil, yalnızca "hata olmadı" varsay

    def test_given_none_complexity_when_exception_silently_swallowed_infection_hidden(self):
        """
        GIVEN: complexity=None olan metot (infection: AttributeError sızıyor)
        WHEN : Test exception'ı yakalar ama sonucu kontrol etmez
        THEN : Test geçer — AttributeError'ın sızdığı görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        selector = make_selector()
        bad_method = MagicMock()
        bad_method.complexity = None
        bad_method.line_count = 5

        try:
            selector.select_best_methods([bad_method])
        except (AttributeError, TypeError):
            pass  # Yüzeysel: exception yakalandı ama ne olduğu kontrol edilmiyor

        # Infection gizli: good_method kaybedildiği test edilmedi


# ===========================================================================
# SINIR DEĞER TESTLERİ — select_best_methods
# ===========================================================================

class TestSelectBestMethodsBoundaryValues:

    def test_given_empty_list_when_select_should_return_empty_list(self):
        """
        GIVEN: Boş methods listesi
        WHEN : select_best_methods çağrılır
        THEN : Boş liste döner, exception fırlatılmaz
        """
        assert make_selector().select_best_methods([]) == []

    def test_given_single_method_when_select_should_return_it(self):
        """
        GIVEN: Tek elemanlı methods listesi
        WHEN : select_best_methods çağrılır
        THEN : O tek metot döner
        """
        m = make_method("only")
        result = make_selector().select_best_methods([m])
        assert len(result) == 1
        assert result[0].name == "only"

    def test_given_limit_greater_than_method_count_when_select_should_return_all(self):
        """
        GIVEN: limit=100, ama yalnızca 3 metot var
        WHEN : select_best_methods çağrılır
        THEN : 3 metotun tümü döner (Python slice tasarımı gereği)
        """
        selector = make_selector(limit=100)
        methods = [make_method(f"m{i}") for i in range(3)]
        result = selector.select_best_methods(methods)
        assert len(result) == 3

    def test_given_limit_less_than_method_count_when_select_should_return_limit_count(self):
        """
        GIVEN: limit=2, 5 metot var
        WHEN : select_best_methods çağrılır
        THEN : Tam 2 metot döner
        """
        selector = make_selector(limit=2)
        methods = [make_method(f"m{i}", cyclomatic=i) for i in range(1, 6)]
        result = selector.select_best_methods(methods)
        assert len(result) == 2

    def test_given_limit_1_when_select_should_return_highest_complexity_method(self):
        """
        GIVEN: limit=1, farklı complexity'li metotlar
        WHEN : select_best_methods çağrılır
        THEN : En yüksek toplam complexity'li tek metot döner
        """
        selector = make_selector(limit=1)
        methods = [
            make_method("low",  cyclomatic=1, cognitive=1),
            make_method("high", cyclomatic=9, cognitive=8),
            make_method("mid",  cyclomatic=4, cognitive=3),
        ]
        result = selector.select_best_methods(methods)
        assert len(result) == 1
        assert result[0].name == "high"

    def test_given_methods_when_select_should_return_list_type(self):
        """
        GIVEN: Geçerli methods listesi
        WHEN : select_best_methods çağrılır
        THEN : Dönüş değeri her zaman list tipindedir
        """
        result = make_selector().select_best_methods([make_method()])
        assert isinstance(result, list)

    def test_given_methods_when_select_should_return_subset_of_input(self):
        """
        GIVEN: 5 metot, limit=3
        WHEN : select_best_methods çağrılır
        THEN : Dönen metotların hepsi input listesinde yer alır
        """
        selector = make_selector(limit=3)
        methods = [make_method(f"m{i}", cyclomatic=i) for i in range(1, 6)]
        result = selector.select_best_methods(methods)
        for m in result:
            assert m in methods

    def test_given_methods_when_select_should_not_modify_original_list(self):
        """
        GIVEN: methods listesi
        WHEN : select_best_methods çağrılır
        THEN : Orijinal liste değiştirilmez (sorted yeni liste üretir)
        """
        selector = make_selector(limit=2)
        methods = [
            make_method("a", cyclomatic=3),
            make_method("b", cyclomatic=5),
            make_method("c", cyclomatic=1),
        ]
        original_order = [m.name for m in methods]
        selector.select_best_methods(methods)
        assert [m.name for m in methods] == original_order


# ===========================================================================
# _rank_by_complexity
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     _rank_by_complexity içindeki sıralama anahtarı:
#
#         key=lambda m: (
#             m.complexity.cyclomatic_complexity + m.complexity.cognitive_complexity,
#             m.line_count,
#         )
#
#     m.complexity=None olan bir metot geldiğinde None.cyclomatic_complexity →
#     AttributeError fırlatır. Tüm sorted() çağrısı çöker, hiçbir metot dönemez.
#     Kısmi hata toleransı yok: tek bozuk metot tüm sıralamayı engelliyor.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     Listedeki herhangi bir metodun complexity attribute'u None olmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_method_with_none_complexity_when_ranking_should_fail_with_attribute_error
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestRankByComplexity:

    def test_given_method_with_none_complexity_when_ranking_should_fail_with_attribute_error(self):
        """
        GIVEN: complexity=None olan metot sıralanmak isteniyor
        WHEN : _rank_by_complexity çağrılır
        THEN : AttributeError dışarıya sızmamalı; hatalı metot atlanmalı/sona konmalı
               Orijinal kodda None.cyclomatic_complexity → AttributeError sızıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        selector = make_selector()

        broken = MagicMock()
        broken.name = "broken"
        broken.complexity = None
        broken.line_count = 5

        good = make_method("good", cyclomatic=3, cognitive=2)

        try:
            result = selector._rank_by_complexity([broken, good])
            # Düzeltilmiş: broken atlandı veya sona kondu, good var
            good_names = [m.name for m in result]
            assert "good" in good_names, "good metot sonuçta olmalı"
        except AttributeError:
            pytest.fail(
                "complexity=None için AttributeError _rank_by_complexity'den sızdı — KUSUR aktif."
            )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: eşit toplam complexity'de line_count kriteri çalışıyor mu?
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     Sıralama anahtarı (toplam_complexity, line_count) ve reverse=True.
    #     Eşit toplam complexity'de büyük line_count önce gelmeli.
    #     Ama key tuple'ında line_count ikincil kriter olarak doğru sırada mı?
    #     reverse=True tüm tuple'a uygulanıyor: hem toplam hem line_count
    #     büyükten küçüğe sıralanır. Bu DOĞRU.
    #
    #     KUSUR: Aynı toplam complexity, farklı bileşen dağılımı.
    #     cyclomatic=10, cognitive=0 ile cyclomatic=5, cognitive=5 eşit toplam.
    #     Eğer cognitive daha önemli olması gerekiyorsa bu sıralama yanlış.
    #     Docstring bunu belirtmiyor; sadece "toplam skor" diyor. Bu bir
    #     EKSIK SPEC KUSURU — sıralamanın toplamı mı yoksa ağırlıklı skoru mu
    #     kullandığını açıklamıyor.
    #
    # Test: eşit toplam ama farklı dağılım → line_count belirleyici olmalı

    def test_given_equal_total_complexity_different_distribution_when_ranking_line_count_decides(self):
        """
        GIVEN: İki metot eşit toplam complexity'ye sahip (8+2=10 vs 5+5=10)
               ama farklı line_count'a sahip
        WHEN : _rank_by_complexity çağrılır
        THEN : Büyük line_count'lu metot önce gelir (ikincil kriter)

        [GÖREV 1c — KUSUR 2 — line_count ikincil kriter doğrulaması]
        """
        selector = make_selector()

        m1 = make_method("high_cyclomatic", cyclomatic=8, cognitive=2, line_count=5)
        m2 = make_method("balanced",        cyclomatic=5, cognitive=5, line_count=20)

        result = selector._rank_by_complexity([m1, m2])

        # Toplam eşit (10), line_count belirleyici: 20 > 5 → m2 önce
        assert result[0].name == "balanced", (
            f"Eşit toplam complexity'de line_count=20 olan 'balanced' önce gelmeli. "
            f"Dönen sıra: {[m.name for m in result]}"
        )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. methods=[] ise sorted([]) hemen boş döner, lambda hiç
    #     çağrılmaz → None.complexity erişimi olmaz → kusur tetiklenmez.
    #
    # (b) Test: boş liste → lambda çağrılmaz

    def test_given_empty_list_when_ranking_should_not_trigger_complexity_defect(self):
        """
        GIVEN: Boş methods listesi
        WHEN : _rank_by_complexity çağrılır
        THEN : Lambda hiç çağrılmaz, AttributeError kusuru tetiklenmez, boş liste döner

        [GÖREV 2b — complexity=None kusuru tetiklenmez]
        """
        selector = make_selector()
        result = selector._rank_by_complexity([])
        assert result == []

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Tüm metotların complexity değerleri geçerliyse lambda başarılı
    #     çalışır, AttributeError riski sıfır. Kusurlu guard yok ama girdi temiz.
    #
    # (b) Test: geçerli complexity → normal sıralama

    def test_given_valid_complexity_methods_when_ranking_should_not_infect(self):
        """
        GIVEN: Tüm metotlarda complexity geçerli
        WHEN : _rank_by_complexity çağrılır
        THEN : Sıralama başarıyla tamamlanır, durum bozulmaz

        [GÖREV 3b — AttributeError path hiç girilmez, infection yok]
        """
        selector = make_selector()
        methods = [
            make_method("a", cyclomatic=3, cognitive=2),
            make_method("b", cyclomatic=7, cognitive=5),
            make_method("c", cyclomatic=1, cognitive=1),
        ]
        result = selector._rank_by_complexity(methods)
        assert result[0].name == "b"  # 12 → en yüksek

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. complexity=None → AttributeError fırlatıldı (infection: sıralama çöktü).
    #     Ama test except ile exception'ı yutup sadece "exception geldi" teyit
    #     ederse sıralama sonucunun eksik olduğunu görmez → failure yok.
    #
    # (b) Test: exception'ı yakala ama sıralama sonucunu kontrol etme

    def test_given_none_complexity_when_exception_swallowed_infection_hidden(self):
        """
        GIVEN: complexity=None → AttributeError sızıyor (tüm sıralama çöktü = infection)
        WHEN : Test exception'ı sessizce yutar, sonucu kontrol etmez
        THEN : Test geçer — sıralama çöktüğü, diğer metotların kaybolduğu görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        selector = make_selector()
        broken = MagicMock()
        broken.complexity = None
        broken.line_count = 5

        good = make_method("good", cyclomatic=5)

        try:
            selector._rank_by_complexity([broken, good])
        except AttributeError:
            pass  # Yüzeysel: exception geldi, ama good'un kaybolduğu kontrol edilmedi


# ===========================================================================
# SINIR DEĞER TESTLERİ — _rank_by_complexity
# ===========================================================================

class TestRankByComplexityBoundaryValues:

    def test_given_empty_list_when_ranking_should_return_empty_list(self):
        """
        GIVEN: Boş liste
        WHEN : _rank_by_complexity çağrılır
        THEN : Boş liste döner
        """
        assert make_selector()._rank_by_complexity([]) == []

    def test_given_single_method_when_ranking_should_return_it_unchanged(self):
        """
        GIVEN: Tek elemanlı liste
        WHEN : _rank_by_complexity çağrılır
        THEN : Aynı tek eleman döner
        """
        m = make_method("only", cyclomatic=5, cognitive=3)
        result = make_selector()._rank_by_complexity([m])
        assert len(result) == 1
        assert result[0].name == "only"

    def test_given_descending_complexity_when_ranking_should_preserve_order(self):
        """
        GIVEN: Metotlar zaten büyükten küçüğe sıralı
        WHEN : _rank_by_complexity çağrılır
        THEN : Sıra değişmez
        """
        selector = make_selector()
        methods = [
            make_method("first",  cyclomatic=10, cognitive=5),
            make_method("second", cyclomatic=5,  cognitive=3),
            make_method("third",  cyclomatic=1,  cognitive=1),
        ]
        result = selector._rank_by_complexity(methods)
        assert [m.name for m in result] == ["first", "second", "third"]

    def test_given_ascending_complexity_when_ranking_should_reverse_order(self):
        """
        GIVEN: Metotlar küçükten büyüğe sıralı
        WHEN : _rank_by_complexity çağrılır
        THEN : Sıra tersine döner
        """
        selector = make_selector()
        methods = [
            make_method("low",  cyclomatic=1, cognitive=1),
            make_method("mid",  cyclomatic=4, cognitive=3),
            make_method("high", cyclomatic=9, cognitive=7),
        ]
        result = selector._rank_by_complexity(methods)
        assert result[0].name == "high"
        assert result[-1].name == "low"

    def test_given_all_equal_complexity_when_ranking_should_use_line_count_as_tiebreaker(self):
        """
        GIVEN: Tüm metotlar eşit toplam complexity'ye sahip, farklı line_count
        WHEN : _rank_by_complexity çağrılır
        THEN : Büyük line_count önce gelir
        """
        selector = make_selector()
        methods = [
            make_method("small", cyclomatic=5, cognitive=5, line_count=3),
            make_method("large", cyclomatic=5, cognitive=5, line_count=50),
            make_method("mid",   cyclomatic=5, cognitive=5, line_count=20),
        ]
        result = selector._rank_by_complexity(methods)
        assert result[0].name == "large"
        assert result[-1].name == "small"

    def test_given_all_equal_complexity_and_line_count_when_ranking_should_be_stable(self):
        """
        GIVEN: Tüm metotlar tamamen eşit key'e sahip
        WHEN : _rank_by_complexity çağrılır
        THEN : Orijinal sıra korunur (Python sorted() stable sort garantisi)
        """
        selector = make_selector()
        methods = [make_method(f"m{i}", cyclomatic=5, cognitive=5, line_count=10)
                   for i in range(4)]
        result = selector._rank_by_complexity(methods)
        assert [m.name for m in result] == [m.name for m in methods]

    def test_given_methods_with_zero_complexity_when_ranking_should_place_last(self):
        """
        GIVEN: Bazı metotların complexity'si 0 (cyclomatic=0, cognitive=0)
        WHEN : _rank_by_complexity çağrılır
        THEN : 0 complexity'li metotlar listenin sonuna düşer
        """
        selector = make_selector()
        methods = [
            make_method("zero", cyclomatic=0, cognitive=0, line_count=5),
            make_method("high", cyclomatic=8, cognitive=4, line_count=5),
        ]
        result = selector._rank_by_complexity(methods)
        assert result[0].name == "high"
        assert result[-1].name == "zero"

    def test_given_methods_with_high_cognitive_low_cyclomatic_when_ranking_uses_sum(self):
        """
        GIVEN: Bir metot yüksek cognitive, düşük cyclomatic; diğeri tam tersi
        WHEN : _rank_by_complexity çağrılır
        THEN : Toplam skor belirleyicidir; bileşen dağılımı değil
        """
        selector = make_selector()
        methods = [
            make_method("high_cog",   cyclomatic=1, cognitive=15),  # toplam=16
            make_method("high_cyclo", cyclomatic=12, cognitive=2),  # toplam=14
        ]
        result = selector._rank_by_complexity(methods)
        assert result[0].name == "high_cog"  # toplam 16 > 14

    def test_given_ranking_when_called_should_not_modify_original_list(self):
        """
        GIVEN: methods listesi
        WHEN : _rank_by_complexity çağrılır
        THEN : Orijinal liste değiştirilmez (sorted() yeni liste döndürür)
        """
        selector = make_selector()
        methods = [
            make_method("a", cyclomatic=3),
            make_method("b", cyclomatic=7),
            make_method("c", cyclomatic=1),
        ]
        original_names = [m.name for m in methods]
        selector._rank_by_complexity(methods)
        assert [m.name for m in methods] == original_names

    def test_given_ranking_when_called_should_return_list_type(self):
        """
        GIVEN: Geçerli methods listesi
        WHEN : _rank_by_complexity çağrılır
        THEN : Dönüş değeri list tipindedir
        """
        result = make_selector()._rank_by_complexity([make_method()])
        assert isinstance(result, list)

    def test_given_ranking_result_should_contain_all_input_methods(self):
        """
        GIVEN: 5 metotlu liste
        WHEN : _rank_by_complexity çağrılır
        THEN : Sonuçta tam 5 eleman var (hiçbiri kaybolmadı)
        """
        selector = make_selector()
        methods = [make_method(f"m{i}", cyclomatic=i) for i in range(1, 6)]
        result = selector._rank_by_complexity(methods)
        assert len(result) == 5

    def test_given_two_methods_when_ranking_higher_complexity_should_come_first(self):
        """
        GIVEN: İki metot, biri diğerinden açıkça daha karmaşık
        WHEN : _rank_by_complexity çağrılır
        THEN : Yüksek complexity'li metot ilk sıraya gelir
        """
        selector = make_selector()
        methods = [
            make_method("simple",  cyclomatic=1, cognitive=1),
            make_method("complex", cyclomatic=9, cognitive=8),
        ]
        result = selector._rank_by_complexity(methods)
        assert result[0].name == "complex"
        assert result[1].name == "simple"

    def test_given_large_input_when_ranking_should_return_all_sorted(self):
        """
        GIVEN: 200 metot, rastgele karmaşıklık değerleri
        WHEN : _rank_by_complexity çağrılır
        THEN : 200 eleman döner ve sıralama doğrudur (her eleman bir öncekinden az karmaşık)
        """
        selector = make_selector()
        import random
        random.seed(42)
        methods = [
            make_method(f"m{i}", cyclomatic=random.randint(1, 20),
                        cognitive=random.randint(0, 15))
            for i in range(200)
        ]
        result = selector._rank_by_complexity(methods)
        assert len(result) == 200
        for i in range(len(result) - 1):
            score_curr = (result[i].complexity.cyclomatic_complexity +
                          result[i].complexity.cognitive_complexity)
            score_next = (result[i+1].complexity.cyclomatic_complexity +
                          result[i+1].complexity.cognitive_complexity)
            assert score_curr >= score_next, (
                f"Sıralama bozuk: indeks {i} ({score_curr}) < indeks {i+1} ({score_next})"
            )

    def test_given_line_count_equal_zero_when_ranking_should_not_crash(self):
        """
        GIVEN: line_count=0 olan metot
        WHEN : _rank_by_complexity çağrılır
        THEN : Exception fırlatılmaz; 0 line_count geçerli bir değer olarak işlenir
        """
        selector = make_selector()
        methods = [
            make_method("zero_lines", cyclomatic=5, cognitive=3, line_count=0),
            make_method("normal",     cyclomatic=5, cognitive=3, line_count=10),
        ]
        result = selector._rank_by_complexity(methods)
        # 0 line_count crash olmamalı, normal > 0 olduğundan normal önce gelir
        assert result[0].name == "normal"
        assert len(result) == 2