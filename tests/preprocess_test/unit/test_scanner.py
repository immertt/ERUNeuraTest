"""
TestProjectScanner — ProjectScanner sınıfının tüm metotları için kapsamlı test sınıfı.

Kapsam:
  - __init__, run, _process_project, _scan_files metotları
  - Her metot için Defect / Infection / Failure analizi (Görev 1-4)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.scanner import ProjectScanner


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def make_scanner(benchmark_dir=None) -> ProjectScanner:
    """Mock bağımlılıklarla ProjectScanner oluşturur."""
    scanner = ProjectScanner(benchmark_dir=benchmark_dir)
    scanner.complexity_calc = MagicMock()
    scanner.selector = MagicMock()
    scanner.exporter = MagicMock()
    return scanner


def make_mock_method(name="foo", body="def foo(): pass"):
    """Test için sahte MethodModel nesnesi döner."""
    m = MagicMock()
    m.name = name
    m.body = body
    return m


# ===========================================================================
# __init__
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     __init__ içindeki benchmark_dir dönüşümü:
#
#         self.benchmark_dir = Path(benchmark_dir) if benchmark_dir else DEFAULT_BENCHMARK
#
#     int, list, dict gibi geçersiz tipler için `if benchmark_dir` truthy
#     değerlendirmesi geçer ve `Path(benchmark_dir)` çağrılır. Path(),
#     int veya list için TypeError fırlatır ve bu exception dışarıya sızar.
#     Doğru davranış: tip kontrolü yapılmalı ya da try/except ile sarılmalı.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     benchmark_dir parametresi string veya Path olmayan, truthy bir değer
#     (örn. 42, ["/some/path"]) olmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_invalid_type_benchmark_dir_when_init_should_fail_with_type_error
#       [GÖREV 1c — orijinal kodla BAŞARISIZ olmalı]

class TestInit:

    def test_given_invalid_type_benchmark_dir_when_init_should_fail_with_type_error(self):
        """
        GIVEN: int tipinde geçersiz benchmark_dir (örn. 42)
        WHEN : ProjectScanner oluşturulur
        THEN : TypeError dışarı sızmamalı; ValueError ya da TypeError yakalanıp
               açıklayıcı mesajla tekrar fırlatılmalı ya da varsayılan kullanılmalı.
               Orijinal kod Path(42) çağrısıyla TypeError'ı yakalamadan fırlatır → BAŞARISIZ

        [GÖREV 1c — orijinal kodla BAŞARISIZ olması beklenir]
        """
        with pytest.raises((TypeError, ValueError)):
            ProjectScanner(benchmark_dir=42)

        # Orijinal kodda TypeError Path(42)'den sızıyor; üst katmana ulaşıyor.
        # Beklenen davranış: ya yakalanıp anlamlı hata verilmeli ya da
        # geçersiz tipte varsayılana düşmeli. İkisi de bu testi geçirir.

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. benchmark_dir=None geçilirse `if benchmark_dir` False olur,
    #     Path() hiç çağrılmaz → TypeError tetiklenmez.
    #
    # (b) Test: benchmark_dir=None → DEFAULT_BENCHMARK kullanılır

    def test_given_none_benchmark_dir_when_init_should_not_trigger_type_defect(self):
        """
        GIVEN: benchmark_dir=None (varsayılan)
        WHEN : ProjectScanner oluşturulur
        THEN : TypeError tetiklenmez; DEFAULT_BENCHMARK kullanılır

        [GÖREV 2b — geçersiz tip kusuru tetiklenmez]
        """
        scanner = ProjectScanner(benchmark_dir=None)
        assert scanner.benchmark_dir is not None
        assert isinstance(scanner.benchmark_dir, Path)

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. benchmark_dir geçerli bir string ("") verilirse truthy
    #     değerlendirme geçer ama Path("") geçerlidir → TypeError olmaz,
    #     durum bozulmaz.
    #
    # (b) Test: geçerli string → Path dönüşümü başarılı

    def test_given_valid_string_benchmark_dir_when_init_should_not_infect(self):
        """
        GIVEN: Geçerli string benchmark_dir ("/tmp/bench")
        WHEN : ProjectScanner oluşturulur
        THEN : Path dönüşümü başarılı, durum bozulmaz

        [GÖREV 3b — kusur çalışır (Path() çağrılır), infection yok]
        """
        scanner = ProjectScanner(benchmark_dir="/tmp/bench")
        assert scanner.benchmark_dir == Path("/tmp/bench")

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Geçersiz tip (int) verilip TypeError sızıyor (infection: hata
    #     yakalanmadı), ama test yalnızca "scanner oluştu mu?" yerine
    #     "exception fırlatıldı mı?" sormuyorsa infection görünmez.
    #
    # (b) Test: exception varlığını değil scanner attribute'unu sorgula

    def test_given_invalid_type_when_only_attribute_checked_infection_hidden(self):
        """
        GIVEN: int tipinde benchmark_dir → TypeError bekleniyor
        WHEN : Test sadece istisna fırlatılıp fırlatılmadığını değil,
               scanner'ın yanlış bir default path aldığını kontrol etse
        THEN : Test geçer — infection gizlenir (bu test kasıtlı yüzeysel)

        [GÖREV 4b — infection var, failure yok]
        """
        try:
            scanner = ProjectScanner(benchmark_dir=42)
            # Eğer buraya gelindiyse scanner oluştu — ama path yanlış olabilir
            # Yüzeysel kontrol: sadece nesne var mı?
            assert scanner is not None  # Bu geçer ama kusur gizli
        except (TypeError, ValueError):
            # Exception fırlatıldı — bu da geçer (infection var ama test bunu görmüyor)
            pass


# ===========================================================================
# SINIR DEĞER TESTLERİ — __init__
# ===========================================================================

class TestInitBoundaryValues:

    def test_given_none_benchmark_dir_when_init_should_use_default_benchmark(self):
        """
        GIVEN: benchmark_dir=None
        WHEN : ProjectScanner oluşturulur
        THEN : benchmark_dir DEFAULT_BENCHMARK'a set edilir
        """
        scanner = ProjectScanner(benchmark_dir=None)
        assert "benchmark" in str(scanner.benchmark_dir)

    def test_given_valid_path_object_when_init_should_preserve_it(self):
        """
        GIVEN: Path nesnesi olarak geçerli benchmark_dir
        WHEN : ProjectScanner oluşturulur
        THEN : benchmark_dir aynı Path değerini taşır
        """
        p = Path("/tmp/mydir")
        scanner = ProjectScanner(benchmark_dir=p)
        assert scanner.benchmark_dir == p

    def test_given_valid_string_when_init_should_convert_to_path(self):
        """
        GIVEN: String olarak benchmark_dir
        WHEN : ProjectScanner oluşturulur
        THEN : benchmark_dir Path tipine dönüştürülür
        """
        scanner = ProjectScanner(benchmark_dir="/tmp/bench")
        assert isinstance(scanner.benchmark_dir, Path)

    def test_given_any_init_when_called_should_create_complexity_calc(self):
        """
        GIVEN: Herhangi bir geçerli init
        WHEN : ProjectScanner oluşturulur
        THEN : complexity_calc bağımlılığı oluşturulur
        """
        scanner = ProjectScanner(benchmark_dir=None)
        assert scanner.complexity_calc is not None

    def test_given_any_init_when_called_should_create_selector(self):
        """
        GIVEN: Herhangi bir geçerli init
        WHEN : ProjectScanner oluşturulur
        THEN : selector bağımlılığı oluşturulur
        """
        scanner = ProjectScanner(benchmark_dir=None)
        assert scanner.selector is not None

    def test_given_any_init_when_called_should_create_exporter(self):
        """
        GIVEN: Herhangi bir geçerli init
        WHEN : ProjectScanner oluşturulur
        THEN : exporter bağımlılığı oluşturulur
        """
        scanner = ProjectScanner(benchmark_dir=None)
        assert scanner.exporter is not None


# ===========================================================================
# run
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     run() içinde:
#
#         projects = [d for d in self.benchmark_dir.iterdir() if d.is_dir()]
#
#     benchmark_dir mevcut olsa bile iterdir() PermissionError fırlatabilir
#     (ör. kısıtlı sistem dizinleri). Bu exception hiç yakalanmıyor →
#     uygulama çöker. Doğru davranış: try/except ile sarılmalı, hata
#     loglanıp gracefully sonlandırılmalı.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     benchmark_dir.exists() True dönerken benchmark_dir.iterdir()
#     PermissionError fırlatmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_permission_error_on_iterdir_when_run_should_fail_not_crash
#       [GÖREV 1c — orijinal kodla BAŞARISIZ olmalı]

class TestRun:

    def test_given_permission_error_on_iterdir_when_run_should_fail_not_crash(self):
        """
        GIVEN: benchmark_dir mevcut ama iterdir() PermissionError fırlatıyor
        WHEN : run() çağrılır
        THEN : Exception dışarıya sızmamalı; hata loglanıp gracefully sonlanmalı
               Orijinal kod PermissionError'ı yakalamıyor → uygulama çöker → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", side_effect=PermissionError("Erişim reddedildi")):
            try:
                scanner.run()
                # Buraya gelindiyse exception yakalandı → GEÇER (düzeltilmiş kod)
            except PermissionError:
                pytest.fail(
                    "PermissionError dışarıya sızdı — run() içinde yakalanmıyor: KUSUR aktif"
                )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: _process_project exception → tüm döngü durur
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     run() içindeki döngü:
    #
    #         for project_path in projects:
    #             self._process_project(project_path)
    #
    #     _process_project herhangi bir exception fırlatırsa try/except yok →
    #     kalan projeler işlenmeden döngü durur. İlk hatalı proje tüm taramayı keser.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     En az 2 proje dizini olmalı; ilk projenin işlenmesi exception fırlatmalı.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_first_project_raises_exception_when_run_should_fail_stopping_remaining(self):
        """
        GIVEN: 2 proje dizini var; ilk _process_project çağrısı exception fırlatıyor
        WHEN : run() çağrılır
        THEN : İkinci proje de işlenmelidir (exception yakalanıp devam edilmeli)
               Orijinal kodda exception döngüyü durdurur → ikinci proje işlenmez → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")

        proj1 = MagicMock(spec=Path)
        proj1.is_dir.return_value = True
        proj1.name = "project1"

        proj2 = MagicMock(spec=Path)
        proj2.is_dir.return_value = True
        proj2.name = "project2"

        call_count = 0

        def failing_process(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("İlk proje başarısız")

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter([proj1, proj2])), \
             patch.object(scanner, "_process_project", side_effect=failing_process):
            try:
                scanner.run()
            except RuntimeError:
                pass  # orijinal kodda exception sızıyor

        assert call_count == 2, (
            f"İkinci proje işlenmedi — döngü ilk exception'da durdu. "
            f"Çağrı sayısı: {call_count} — KUSUR aktif"
        )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. benchmark_dir mevcut değilse "if not self.benchmark_dir.exists()"
    #     kontrolü erken return eder → iterdir() ve döngü hiç çalışmaz.
    #
    # (b) Test: var olmayan dizin → erken return

    def test_given_nonexistent_benchmark_dir_when_run_should_not_trigger_iterdir_defect(self):
        """
        GIVEN: Var olmayan benchmark_dir
        WHEN : run() çağrılır
        THEN : iterdir() hiç çağrılmaz, PermissionError kusuru tetiklenmez

        [GÖREV 2b — iterdir kusuru tetiklenmez]
        """
        scanner = make_scanner(benchmark_dir="/nonexistent/path/xyz")

        with patch.object(Path, "exists", return_value=False), \
             patch.object(Path, "iterdir") as mock_iter:
            scanner.run()

        mock_iter.assert_not_called()

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. iterdir() başarılı AMA projects listesi boşsa döngüye
    #     hiç girilmez → _process_project çağrılmaz → exception riski sıfır.
    #     Kusurlu path çalıştı ama durum bozulmadı.
    #
    # (b) Test: boş benchmark dizini → döngü çalışmaz

    def test_given_empty_benchmark_dir_when_run_should_not_infect_via_loop(self):
        """
        GIVEN: benchmark_dir mevcut ama içinde hiç alt dizin yok
        WHEN : run() çağrılır
        THEN : _process_project hiç çağrılmaz, döngü exception riski olmadan biter

        [GÖREV 3b — iterdir çalışır ama döngü boş, infection yok]
        """
        scanner = make_scanner(benchmark_dir="/tmp/empty")

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter([])), \
             patch.object(scanner, "_process_project") as mock_process:
            scanner.run()

        mock_process.assert_not_called()

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. 2 proje var, ilki exception fırlatıyor (döngü duruyor = infection).
    #     Ama test yalnızca "ilk proje çağrıldı mı?" kontrol ederse ikincinin
    #     atlandığını görmez → failure yok.
    #
    # (b) Test: sadece ilk çağrıyı kontrol et

    def test_given_failing_first_project_when_only_first_call_checked_infection_hidden(self):
        """
        GIVEN: İlk _process_project exception fırlatıyor (ikinci proje atlanıyor = infection)
        WHEN : Yalnızca call_count >= 1 kontrol edilir
        THEN : Test geçer — ikinci projenin işlenmediği görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")

        proj1 = MagicMock(spec=Path)
        proj1.name = "project1"
        proj2 = MagicMock(spec=Path)
        proj2.name = "project2"

        call_count = 0

        def failing_process(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated")

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter([proj1, proj2])), \
             patch.object(scanner, "_process_project", side_effect=failing_process):
            try:
                scanner.run()
            except RuntimeError:
                pass

        # Yüzeysel kontrol → infection görünmez
        assert call_count >= 1  # İlk çağrı oldu, ikincisi atlandı ama test bunu görmüyor


# ===========================================================================
# SINIR DEĞER TESTLERİ — run
# ===========================================================================

class TestRunBoundaryValues:

    def test_given_nonexistent_dir_when_run_should_print_error_and_return(self, capsys):
        """
        GIVEN: Var olmayan benchmark_dir
        WHEN : run() çağrılır
        THEN : Hata mesajı print edilir, exception fırlatılmaz
        """
        scanner = make_scanner(benchmark_dir="/nonexistent/abc")
        with patch.object(Path, "exists", return_value=False):
            scanner.run()

        captured = capsys.readouterr()
        assert "Hata" in captured.out or "bulunamadı" in captured.out

    def test_given_empty_dir_when_run_should_not_raise(self):
        """
        GIVEN: Mevcut ama boş benchmark dizini
        WHEN : run() çağrılır
        THEN : Exception fırlatılmaz
        """
        scanner = make_scanner(benchmark_dir="/tmp/empty")
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter([])):
            scanner.run()  # crash olmamalı

    def test_given_single_project_when_run_should_call_process_project_once(self):
        """
        GIVEN: Tek proje dizini olan benchmark
        WHEN : run() çağrılır
        THEN : _process_project tam 1 kez çağrılır
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")
        proj = MagicMock(spec=Path)
        proj.name = "only_project"

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter([proj])), \
             patch.object(scanner, "_process_project") as mock_process:
            scanner.run()

        mock_process.assert_called_once_with(proj)

    def test_given_dir_with_files_not_dirs_when_run_should_skip_files(self):
        """
        GIVEN: benchmark_dir içinde dizin değil dosya var
        WHEN : run() çağrılır
        THEN : Dosyalar is_dir=False olduğu için atlanır, _process_project çağrılmaz
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")

        file_entry = MagicMock(spec=Path)
        file_entry.is_dir.return_value = False
        file_entry.name = "some_file.py"

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter([file_entry])), \
             patch.object(scanner, "_process_project") as mock_process:
            scanner.run()

        mock_process.assert_not_called()

    def test_given_multiple_projects_when_run_should_process_each(self):
        """
        GIVEN: 3 proje dizini
        WHEN : run() çağrılır
        THEN : _process_project her biri için çağrılır
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")

        projects = []
        for i in range(3):
            p = MagicMock(spec=Path)
            p.name = f"project{i}"
            projects.append(p)

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter(projects)), \
             patch.object(scanner, "_process_project") as mock_process:
            scanner.run()

        assert mock_process.call_count == 3

    def test_given_benchmark_dir_when_run_should_print_scan_path(self, capsys):
        """
        GIVEN: Geçerli benchmark_dir
        WHEN : run() çağrılır
        THEN : Tarama dizini print edilir
        """
        scanner = make_scanner(benchmark_dir="/tmp/bench")
        with patch.object(Path, "exists", return_value=False):
            scanner.run()

        captured = capsys.readouterr()
        assert "Tarama" in captured.out or "bench" in captured.out.lower()


# ===========================================================================
# _process_project
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     _process_project içinde:
#
#         selected = self.selector.select_best_methods(methods)
#         self.exporter.export(selected, project_name)
#
#     Bu iki çağrı için try/except yok. selector veya exporter exception
#     fırlatırsa _process_project'i çağıran run() döngüsü kırılır →
#     sonraki projeler işlenmez. Her projenin izole edilmesi gerekir.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     selector.select_best_methods() RuntimeError gibi bir exception
#     fırlatmalı ve _process_project bunu yakalamamalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_selector_raises_when_process_project_should_fail_propagating_exception
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestProcessProject:

    def test_given_selector_raises_when_process_project_should_fail_propagating_exception(self):
        """
        GIVEN: selector.select_best_methods() RuntimeError fırlatıyor
        WHEN : _process_project çağrılır
        THEN : Exception dışarıya sızmamalı; hata loglanıp metot gracefully sonlanmalı
               Orijinal kodda exception yakalanmıyor → döngü kırılır → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner()
        scanner.selector.select_best_methods.side_effect = RuntimeError("Selector patladı")

        project_path = MagicMock(spec=Path)
        project_path.name = "test_project"

        mock_method = make_mock_method()
        scanner.complexity_calc.calculate.return_value = MagicMock()

        with patch.object(scanner, "_scan_files", return_value=[mock_method]):
            try:
                scanner._process_project(project_path)
                # Buraya gelinirse exception yakalandı → düzeltilmiş kod
            except RuntimeError:
                pytest.fail(
                    "selector exception'ı _process_project'ten sızdı — KUSUR aktif. "
                    "Bu durum run() döngüsünü kırar."
                )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: selected boşsa export çağrılıyor, uyarı yok
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     _process_project içinde:
    #
    #         selected = self.selector.select_best_methods(methods)
    #         self.exporter.export(selected, project_name)
    #
    #     `selected` boş liste ([]) dönerse export yine çağrılır.
    #     Kullanıcıya "seçilecek metot bulunamadı" uyarısı verilmez.
    #     `if not methods:` kontrolü var ama `if not selected:` yok.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     methods dolu, ama selector boş liste döndürmeli.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_selector_returns_empty_when_process_project_should_fail_exporting_silently(self):
        """
        GIVEN: methods dolu, selector boş liste döndürüyor
        WHEN : _process_project çağrılır
        THEN : export çağrılmamalı VEYA kullanıcıya uyarı verilmeli
               Orijinal kodda export([], project_name) sessizce çağrılır → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner()
        scanner.selector.select_best_methods.return_value = []

        project_path = MagicMock(spec=Path)
        project_path.name = "test_project"

        mock_method = make_mock_method()
        scanner.complexity_calc.calculate.return_value = MagicMock()

        with patch.object(scanner, "_scan_files", return_value=[mock_method]):
            scanner._process_project(project_path)

        # Boş selected ile export çağrılmamalıydı
        scanner.exporter.export.assert_not_called(), (
            "Seçilen metot yokken export sessizce çağrıldı — KUSUR aktif. "
            "Beklenen: export çağrılmamalı ya da uyarı verilmeli."
        )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 3: complexity döngüsünde exception → loop kırılır
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     _process_project içinde:
    #
    #         for method in methods:
    #             method.complexity = self.complexity_calc.calculate(method.body)
    #
    #     complexity_calc.calculate() exception fırlatırsa for döngüsü kırılır.
    #     Kalan metotların complexity'si hesaplanmaz → eksik veriyle selector
    #     çağrılır ya da tamamen hata oluşur.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     2+ metot var, ilkinde calculate() exception fırlatmalı.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_complexity_calc_raises_for_one_method_when_process_project_should_fail_skipping(self):
        """
        GIVEN: 2 metot var, ilkinde complexity_calc exception fırlatıyor
        WHEN : _process_project çağrılır
        THEN : Hatalı metot atlanmalı, ikinci metot işlenmeye devam etmeli
               Orijinal kodda exception yakalanmıyor → loop kırılır → BAŞARISIZ

        [GÖREV 1c — KUSUR 3 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner()
        method1 = make_mock_method("method1", "body1")
        method2 = make_mock_method("method2", "body2")

        calc_count = 0

        def failing_calc(body):
            nonlocal calc_count
            calc_count += 1
            if calc_count == 1:
                raise ValueError("Complexity hesaplanamadı")
            return MagicMock()

        scanner.complexity_calc.calculate.side_effect = failing_calc
        scanner.selector.select_best_methods.return_value = [method2]

        project_path = MagicMock(spec=Path)
        project_path.name = "test_project"

        with patch.object(scanner, "_scan_files", return_value=[method1, method2]):
            try:
                scanner._process_project(project_path)
            except ValueError:
                pytest.fail(
                    "complexity exception atlandı ve ikinci metot işlenemedi — KUSUR aktif"
                )

        assert calc_count == 2, (
            f"complexity_calc yalnızca {calc_count} kez çağrıldı; "
            f"ikinci metot için çağrılmalıydı — döngü kırıldı, KUSUR aktif"
        )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. methods boşsa `if not methods: return` erken döner.
    #     selector, exporter ve complexity döngüsü hiç çalışmaz → kusurlar tetiklenmez.
    #
    # (b) Test: _scan_files boş liste döner

    def test_given_no_methods_found_when_process_project_should_not_trigger_any_defect(self):
        """
        GIVEN: _scan_files boş liste döndürüyor
        WHEN : _process_project çağrılır
        THEN : selector ve exporter hiç çağrılmaz, kusurlar tetiklenmez

        [GÖREV 2b — tüm kusurlar tetiklenmez]
        """
        scanner = make_scanner()
        project_path = MagicMock(spec=Path)
        project_path.name = "empty_project"

        with patch.object(scanner, "_scan_files", return_value=[]):
            scanner._process_project(project_path)

        scanner.selector.select_best_methods.assert_not_called()
        scanner.exporter.export.assert_not_called()

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. selector başarılı çalışıp dolu liste döndürürse, exporter
    #     exception risk altında ama exception fırlatmazsa durum bozulmaz.
    #
    # (b) Test: her şey başarılı → normal akış

    def test_given_successful_pipeline_when_process_project_should_not_infect(self):
        """
        GIVEN: _scan_files, selector ve exporter hepsi başarılı
        WHEN : _process_project çağrılır
        THEN : Pipeline tamamlanır, durum bozulmaz

        [GÖREV 3b — kusurlu path'ler çalışır ama infection yok]
        """
        scanner = make_scanner()
        method = make_mock_method()
        scanner.complexity_calc.calculate.return_value = MagicMock()
        scanner.selector.select_best_methods.return_value = [method]

        project_path = MagicMock(spec=Path)
        project_path.name = "good_project"

        with patch.object(scanner, "_scan_files", return_value=[method]):
            scanner._process_project(project_path)

        scanner.exporter.export.assert_called_once()

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. selected boşsa export çağrılıyor (infection). Ama test
    #     yalnızca "exception fırlatıldı mı?" kontrol ederse boş export
    #     görünmez.
    #
    # (b) Test: exception yokluğunu kontrol et, export içeriğini değil

    def test_given_empty_selected_when_only_no_exception_checked_infection_hidden(self):
        """
        GIVEN: selector boş liste döndürüyor (infection: boş export çağrılıyor)
        WHEN : Yalnızca exception fırlatılmadığı kontrol edilir
        THEN : Test geçer — boş export sessizce çağrıldı ama bu görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        scanner = make_scanner()
        scanner.selector.select_best_methods.return_value = []
        scanner.complexity_calc.calculate.return_value = MagicMock()

        project_path = MagicMock(spec=Path)
        project_path.name = "test_project"
        method = make_mock_method()

        with patch.object(scanner, "_scan_files", return_value=[method]):
            scanner._process_project(project_path)  # exception fırlatmaz

        # Yüzeysel kontrol → infection gizleniyor
        # (boş export çağrıldı ama bu assert bunu sormuyor)
        assert True  # kasıtlı boş kontrol — infection gizli


# ===========================================================================
# SINIR DEĞER TESTLERİ — _process_project
# ===========================================================================

class TestProcessProjectBoundaryValues:

    def test_given_empty_methods_when_process_project_should_print_warning(self, capsys):
        """
        GIVEN: _scan_files boş liste döndürüyor
        WHEN : _process_project çağrılır
        THEN : Uyarı mesajı print edilir
        """
        scanner = make_scanner()
        project_path = MagicMock(spec=Path)
        project_path.name = "empty_proj"

        with patch.object(scanner, "_scan_files", return_value=[]):
            scanner._process_project(project_path)

        captured = capsys.readouterr()
        assert "Uyarı" in captured.out or "bulunamadı" in captured.out

    def test_given_methods_when_process_project_should_calculate_complexity_for_each(self):
        """
        GIVEN: 3 metot içeren proje
        WHEN : _process_project çağrılır
        THEN : complexity_calc.calculate tam 3 kez çağrılır
        """
        scanner = make_scanner()
        methods = [make_mock_method(f"m{i}", f"body{i}") for i in range(3)]
        scanner.complexity_calc.calculate.return_value = MagicMock()
        scanner.selector.select_best_methods.return_value = methods

        project_path = MagicMock(spec=Path)
        project_path.name = "proj"

        with patch.object(scanner, "_scan_files", return_value=methods):
            scanner._process_project(project_path)

        assert scanner.complexity_calc.calculate.call_count == 3

    def test_given_methods_when_process_project_should_call_selector(self):
        """
        GIVEN: Dolu methods listesi
        WHEN : _process_project çağrılır
        THEN : selector.select_best_methods çağrılır
        """
        scanner = make_scanner()
        method = make_mock_method()
        scanner.complexity_calc.calculate.return_value = MagicMock()
        scanner.selector.select_best_methods.return_value = [method]

        project_path = MagicMock(spec=Path)
        project_path.name = "proj"

        with patch.object(scanner, "_scan_files", return_value=[method]):
            scanner._process_project(project_path)

        scanner.selector.select_best_methods.assert_called_once()

    def test_given_selected_methods_when_process_project_should_call_exporter_with_project_name(self):
        """
        GIVEN: selector dolu liste döndürüyor
        WHEN : _process_project çağrılır
        THEN : exporter.export proje adıyla çağrılır
        """
        scanner = make_scanner()
        method = make_mock_method()
        scanner.complexity_calc.calculate.return_value = MagicMock()
        scanner.selector.select_best_methods.return_value = [method]

        project_path = MagicMock(spec=Path)
        project_path.name = "my_project"

        with patch.object(scanner, "_scan_files", return_value=[method]):
            scanner._process_project(project_path)

        scanner.exporter.export.assert_called_once()
        call_args = scanner.exporter.export.call_args
        assert "my_project" in call_args[0] or "my_project" in str(call_args)

    def test_given_project_path_when_process_project_should_use_path_name_as_project_name(self):
        """
        GIVEN: project_path.name = "django"
        WHEN : _process_project çağrılır
        THEN : exporter.export("django") şeklinde çağrılır
        """
        scanner = make_scanner()
        method = make_mock_method()
        scanner.complexity_calc.calculate.return_value = MagicMock()
        scanner.selector.select_best_methods.return_value = [method]

        project_path = MagicMock(spec=Path)
        project_path.name = "django"

        with patch.object(scanner, "_scan_files", return_value=[method]):
            scanner._process_project(project_path)

        args, _ = scanner.exporter.export.call_args
        assert "django" in args


# ===========================================================================
# _scan_files
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     _scan_files içinde:
#
#         for file_path in project_path.rglob("*.py"):
#
#     rglob("*.py") pattern'i __pycache__ dizini altındaki .py dosyalarını
#     (örn. __pycache__/module.cpython-311.pyc değil ama bazı edge case'ler)
#     ve daha önemlisi test/vendor/migration gibi dizinleri de kapsar.
#     __pycache__ filtresi yoktur → gereksiz/yanlış dosyalar taranır.
#     Bu; hatalı metot çıkarımı veya performans sorununa yol açar.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     project_path içinde "__pycache__" dizini olmalı ve içinde .py uzantılı
#     bir dosya bulunmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_pycache_py_file_when_scan_files_should_fail_including_it
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestScanFiles:

    def test_given_pycache_py_file_when_scan_files_should_fail_including_it(self):
        """
        GIVEN: __pycache__ içinde .py uzantılı dosya var
        WHEN : _scan_files çağrılır
        THEN : __pycache__ içindeki dosyalar taranmamalıdır
               Orijinal kod rglob("*.py") ile bu dosyayı da tarar → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner()

        pycache_file = MagicMock(spec=Path)
        pycache_file.__str__ = lambda self: "/proj/__pycache__/module.py"
        pycache_file.parts = ("/", "proj", "__pycache__", "module.py")
        pycache_file.read_text.return_value = "def cached(): pass"

        normal_file = MagicMock(spec=Path)
        normal_file.__str__ = lambda self: "/proj/module.py"
        normal_file.parts = ("/", "proj", "module.py")
        normal_file.read_text.return_value = "def real_func(): pass"
        normal_file.stem = "module"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([normal_file, pycache_file])

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_analyzer_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = []
            mock_analyzer_cls.return_value = mock_analyzer

            scanner._scan_files(project_path)

        # ASTAnalyzer'ın __pycache__ dosyasıyla çağrılmaması gerekir
        for call_args in mock_analyzer_cls.call_args_list:
            file_arg = str(call_args[1].get("file_path", "") or call_args[0])
            assert "__pycache__" not in file_arg, (
                f"__pycache__ içindeki dosya tarandı — KUSUR aktif. "
                f"Çağrı: {call_args}"
            )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: encoding hatası ile okuma hatası aynı mesaj
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     _scan_files içinde:
    #
    #         except Exception as e:
    #             print(f"Hata: {file_path} okunamadı - {e}")
    #             continue
    #
    #     UnicodeDecodeError (encoding uyumsuzluğu) ile PermissionError
    #     (okuma izni yok) aynı "okunamadı" mesajıyla loglanıyor.
    #     Kullanıcı hatanın gerçek nedenini ayırt edemiyor.
    #     Doğru davranış: hata tipine göre farklı mesaj verilmeli.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     read_text() UnicodeDecodeError fırlatmalı.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_unicode_decode_error_when_scan_files_should_fail_with_specific_message(self, capsys):
        """
        GIVEN: read_text() UnicodeDecodeError fırlatıyor
        WHEN : _scan_files çağrılır
        THEN : Log mesajı 'encoding' veya 'unicode' içermeli, hata türünü açıklamalı
               Orijinal kod sadece 'okunamadı' yazıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        scanner = make_scanner()

        bad_file = MagicMock(spec=Path)
        bad_file.__str__ = lambda self: "/proj/latin_file.py"
        bad_file.stem = "latin_file"
        bad_file.read_text.side_effect = UnicodeDecodeError(
            "utf-8", b"\xff\xfe", 0, 1, "invalid start byte"
        )

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([bad_file])

        scanner._scan_files(project_path)
        captured = capsys.readouterr()

        assert "encoding" in captured.out.lower() or "unicode" in captured.out.lower(), (
            f"UnicodeDecodeError için özel mesaj yok — log: '{captured.out.strip()}' — KUSUR aktif"
        )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. project_path içinde hiç .py dosyası yoksa rglob boş döner →
    #     döngüye girilmez → ne __pycache__ kusuru ne encoding kusuru tetiklenir.
    #
    # (b) Test: rglob boş döner

    def test_given_no_py_files_when_scan_files_should_not_trigger_any_defect(self):
        """
        GIVEN: Proje dizininde hiç .py dosyası yok
        WHEN : _scan_files çağrılır
        THEN : Döngüye girilmez, tüm kusurlar tetiklenmez, boş liste döner

        [GÖREV 2b — kusurlar tetiklenmez]
        """
        scanner = make_scanner()
        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([])

        result = scanner._scan_files(project_path)
        assert result == []

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. rglob çalışır, .py dosyaları bulunur, ama hiçbiri
    #     __pycache__ içinde değilse ve encoding uyumlu ise durum bozulmaz.
    #
    # (b) Test: normal .py dosyaları → her şey başarılı

    def test_given_normal_py_files_when_scan_files_should_not_infect(self):
        """
        GIVEN: __pycache__ dışında, UTF-8 encoding'li geçerli .py dosyaları
        WHEN : _scan_files çağrılır
        THEN : Dosyalar başarıyla taranır, durum bozulmaz

        [GÖREV 3b — kusurlu path'ler çalışır ama infection yok]
        """
        scanner = make_scanner()

        good_file = MagicMock(spec=Path)
        good_file.__str__ = lambda self: "/proj/module.py"
        good_file.stem = "module"
        good_file.read_text.return_value = "def foo(): pass"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([good_file])

        mock_method = make_mock_method()

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = [mock_method]
            mock_cls.return_value = mock_analyzer

            result = scanner._scan_files(project_path)

        assert len(result) == 1

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. __pycache__ dosyası tarandı (infection: yanlış dosya dahil edildi).
    #     Ama test yalnızca "sonuç listesi boş değil mi?" kontrol ederse
    #     hangi dosyadan geldiğini görmez → failure yok.
    #
    # (b) Test: sadece len > 0 kontrol et

    def test_given_pycache_file_when_only_result_length_checked_infection_hidden(self):
        """
        GIVEN: __pycache__ içindeki dosya taranıyor (infection: yanlış kaynak)
        WHEN : Yalnızca sonuç listesinin boş olmadığı kontrol edilir
        THEN : Test geçer — __pycache__'den gelen metot görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        scanner = make_scanner()

        pycache_file = MagicMock(spec=Path)
        pycache_file.__str__ = lambda self: "/proj/__pycache__/cached.py"
        pycache_file.stem = "cached"
        pycache_file.read_text.return_value = "def cached_func(): pass"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([pycache_file])

        mock_method = make_mock_method("cached_func")

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = [mock_method]
            mock_cls.return_value = mock_analyzer

            result = scanner._scan_files(project_path)

        # Yüzeysel kontrol → infection gizleniyor
        assert len(result) >= 0  # Kasıtlı boş/trivial kontrol


# ===========================================================================
# SINIR DEĞER TESTLERİ — _scan_files
# ===========================================================================

class TestScanFilesBoundaryValues:

    def test_given_empty_project_dir_when_scan_files_should_return_empty_list(self):
        """
        GIVEN: Proje dizininde hiç .py dosyası yok
        WHEN : _scan_files çağrılır
        THEN : Boş liste döner
        """
        scanner = make_scanner()
        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([])

        result = scanner._scan_files(project_path)
        assert result == []

    def test_given_single_py_file_with_methods_when_scan_files_should_return_methods(self):
        """
        GIVEN: Tek .py dosyası, 2 metot içeriyor
        WHEN : _scan_files çağrılır
        THEN : 2 MethodModel döner
        """
        scanner = make_scanner()

        py_file = MagicMock(spec=Path)
        py_file.stem = "utils"
        py_file.read_text.return_value = "def foo(): pass\ndef bar(): pass\n"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([py_file])

        m1 = make_mock_method("foo")
        m2 = make_mock_method("bar")

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = [m1, m2]
            mock_cls.return_value = mock_analyzer

            result = scanner._scan_files(project_path)

        assert len(result) == 2

    def test_given_file_with_read_error_when_scan_files_should_skip_and_continue(self):
        """
        GIVEN: Bir dosyada PermissionError, diğeri normal
        WHEN : _scan_files çağrılır
        THEN : Hatalı dosya atlanır, diğeri işlenir; boş liste değil 1 metot döner
        """
        scanner = make_scanner()

        bad_file = MagicMock(spec=Path)
        bad_file.__str__ = lambda self: "/proj/bad.py"
        bad_file.stem = "bad"
        bad_file.read_text.side_effect = PermissionError("Erişim yok")

        good_file = MagicMock(spec=Path)
        good_file.__str__ = lambda self: "/proj/good.py"
        good_file.stem = "good"
        good_file.read_text.return_value = "def foo(): pass"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([bad_file, good_file])

        mock_method = make_mock_method("foo")

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = [mock_method]
            mock_cls.return_value = mock_analyzer

            result = scanner._scan_files(project_path)

        assert len(result) == 1

    def test_given_file_read_error_when_scan_files_should_not_raise(self):
        """
        GIVEN: read_text() exception fırlatıyor
        WHEN : _scan_files çağrılır
        THEN : Exception dışarıya sızmaz
        """
        scanner = make_scanner()

        bad_file = MagicMock(spec=Path)
        bad_file.__str__ = lambda self: "/proj/bad.py"
        bad_file.stem = "bad"
        bad_file.read_text.side_effect = OSError("Disk hatası")

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([bad_file])

        result = scanner._scan_files(project_path)  # crash olmamalı
        assert result == []

    def test_given_file_read_error_when_scan_files_should_log_file_path(self, capsys):
        """
        GIVEN: read_text() exception fırlatıyor
        WHEN : _scan_files çağrılır
        THEN : Hata mesajında dosya yolu yer alır
        """
        scanner = make_scanner()

        bad_file = MagicMock(spec=Path)
        bad_file.__str__ = lambda self: "/proj/problematic.py"
        bad_file.stem = "problematic"
        bad_file.read_text.side_effect = OSError("Hata")

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([bad_file])

        scanner._scan_files(project_path)
        captured = capsys.readouterr()
        assert "problematic" in captured.out or "Hata" in captured.out

    def test_given_py_file_when_scan_files_should_pass_file_path_to_analyzer(self):
        """
        GIVEN: Geçerli .py dosyası
        WHEN : _scan_files çağrılır
        THEN : ASTAnalyzer file_path parametresiyle doğru dosya yoluyla çağrılır
        """
        scanner = make_scanner()

        py_file = MagicMock(spec=Path)
        py_file.__str__ = lambda self: "/proj/models.py"
        py_file.stem = "models"
        py_file.read_text.return_value = "def foo(): pass"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([py_file])

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = []
            mock_cls.return_value = mock_analyzer

            scanner._scan_files(project_path)

        call_kwargs = mock_cls.call_args[1]
        assert "file_path" in call_kwargs
        assert "/proj/models.py" in str(call_kwargs["file_path"])

    def test_given_py_file_when_scan_files_should_pass_module_name_as_stem(self):
        """
        GIVEN: stem='utils' olan .py dosyası
        WHEN : _scan_files çağrılır
        THEN : ASTAnalyzer module_name='utils' ile çağrılır
        """
        scanner = make_scanner()

        py_file = MagicMock(spec=Path)
        py_file.__str__ = lambda self: "/proj/utils.py"
        py_file.stem = "utils"
        py_file.read_text.return_value = "def helper(): pass"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([py_file])

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = []
            mock_cls.return_value = mock_analyzer

            scanner._scan_files(project_path)

        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("module_name") == "utils"

    def test_given_multiple_files_when_scan_files_should_aggregate_all_methods(self):
        """
        GIVEN: 3 dosya, her birinde 2 metot
        WHEN : _scan_files çağrılır
        THEN : Toplam 6 MethodModel döner
        """
        scanner = make_scanner()

        files = []
        for i in range(3):
            f = MagicMock(spec=Path)
            f.__str__ = lambda self, i=i: f"/proj/module{i}.py"
            f.stem = f"module{i}"
            f.read_text.return_value = f"def func{i}a(): pass\ndef func{i}b(): pass"
            files.append(f)

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter(files)

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = [
                make_mock_method("a"), make_mock_method("b")
            ]
            mock_cls.return_value = mock_analyzer

            result = scanner._scan_files(project_path)

        assert len(result) == 6

    def test_given_file_with_no_methods_when_scan_files_should_not_add_to_result(self):
        """
        GIVEN: .py dosyası parse ediliyor ama metot içermiyor
        WHEN : _scan_files çağrılır
        THEN : Sonuç listesine ekleme yapılmaz
        """
        scanner = make_scanner()

        empty_file = MagicMock(spec=Path)
        empty_file.__str__ = lambda self: "/proj/constants.py"
        empty_file.stem = "constants"
        empty_file.read_text.return_value = "X = 42\n"

        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([empty_file])

        with patch("src.preprocess.scanner.ASTAnalyzer") as mock_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.get_methods_info.return_value = []
            mock_cls.return_value = mock_analyzer

            result = scanner._scan_files(project_path)

        assert result == []

    def test_given_return_value_should_always_be_list(self):
        """
        GIVEN: Herhangi bir proje dizini
        WHEN : _scan_files çağrılır
        THEN : Dönüş değeri her zaman list tipindedir
        """
        scanner = make_scanner()
        project_path = MagicMock(spec=Path)
        project_path.rglob.return_value = iter([])

        result = scanner._scan_files(project_path)
        assert isinstance(result, list)