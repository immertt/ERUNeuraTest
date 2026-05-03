"""
TestJSONExporter — JSONExporter sınıfının tüm metotları için kapsamlı test sınıfı.

Kapsam:
  - __init__, export, format_method metotları
  - Her metot için Defect / Infection / Failure analizi (Görev 1-4)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""

import json
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.exporter import JSONExporter


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def make_exporter(tmp_path) -> JSONExporter:
    """Gerçek geçici dizin kullanan JSONExporter oluşturur."""
    return JSONExporter(output_base_dir=tmp_path)


def make_method(name="foo", to_dict_result=None):
    """Sahte MethodModel nesnesi döner."""
    m = MagicMock()
    m.name = name
    if to_dict_result is None:
        to_dict_result = {"name": name, "body": "def foo(): pass"}
    m.to_dict.return_value = to_dict_result
    return m


# ===========================================================================
# __init__
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     __init__ içinde:
#
#         self.output_base_dir.mkdir(parents=True, exist_ok=True)
#
#     mkdir() başarısız olursa (PermissionError, OSError) exception hiç
#     yakalanmıyor → dışarıya sızıyor. Nesne oluşturulamaz ama kullanıcıya
#     anlamlı bir hata mesajı verilmiyor; stack trace görülür.
#     Doğru davranış: try/except ile sarılmalı, açıklayıcı hata fırlatılmalı.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     output_base_dir olarak yazma izninin olmadığı bir dizin verilmeli
#     ve mkdir() PermissionError fırlatmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_permission_error_on_mkdir_when_init_should_fail_propagating_exception
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestInit:

    def test_given_permission_error_on_mkdir_when_init_should_fail_propagating_exception(self, tmp_path):
        """
        GIVEN: mkdir() PermissionError fırlatıyor
        WHEN : JSONExporter oluşturulur
        THEN : Exception dışarıya sızmamalı; anlamlı hata mesajıyla OSError/ValueError fırlatılmalı
               Orijinal kodda PermissionError yakalanmıyor → ham exception sızıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        with patch.object(Path, "mkdir", side_effect=PermissionError("Erişim reddedildi")):
            try:
                exporter = JSONExporter(output_base_dir=str(tmp_path / "protected"))
                pytest.fail("PermissionError yakalanmalıydı ama nesne oluşturuldu")
            except PermissionError:
                pytest.fail(
                    "PermissionError ham olarak dışarıya sızdı — "
                    "anlamlı hata mesajıyla sarılmalıydı: KUSUR aktif"
                )
            except (OSError, RuntimeError, ValueError):
                pass  # Düzeltilmiş: anlamlı exception tipiyle sarıldı → GEÇER

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: geçersiz tip → TypeError yakalanmıyor
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     `Path(output_base_dir) if output_base_dir else DEFAULT_OUTPUT`
    #     output_base_dir=42 (int) gibi geçersiz tip gelirse Path(42) →
    #     TypeError fırlatır. Yakalanmıyor.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     output_base_dir parametresi string veya Path olmayan truthy değer olmalı.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_invalid_type_dir_when_init_should_fail_with_unhandled_type_error(self):
        """
        GIVEN: output_base_dir=42 (int, geçersiz tip)
        WHEN : JSONExporter oluşturulur
        THEN : ValueError veya TypeError yakalanıp anlamlı mesajla fırlatılmalı
               Orijinal kodda Path(42) → ham TypeError sızıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        with pytest.raises((TypeError, ValueError)):
            JSONExporter(output_base_dir=42)
        # Orijinal kod bu testi geçirir (TypeError gerçekten fırlatıyor)
        # ama hata mesajı Path'in kendi mesajı — kullanıcı dostu değil.

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 3: boş string → sessizce DEFAULT_OUTPUT'a fallback
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     `if output_base_dir` koşulu boş string için False döner →
    #     DEFAULT_OUTPUT kullanılır. Kullanıcı boş string geçirerek
    #     bilinçli bir şey söylemeye çalışıyor olabilir; sessiz fallback
    #     beklenmedik davranış yaratır. ValueError fırlatılmalıydı.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     output_base_dir="" geçilmelidir.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_empty_string_dir_when_init_should_fail_using_default_silently(self):
        """
        GIVEN: output_base_dir="" (boş string)
        WHEN : JSONExporter oluşturulur
        THEN : ValueError fırlatılmalı (geçersiz girdi)
               Orijinal kodda DEFAULT_OUTPUT sessizce kullanılıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 3 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        with patch.object(Path, "mkdir"):
            with pytest.raises(ValueError):
                JSONExporter(output_base_dir="")
            # Orijinal kodda ValueError yok → test BAŞARISIZ olur

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. output_base_dir=None ise `if output_base_dir` False olur →
    #     Path() hiç çağrılmaz, geçersiz tip kusuru tetiklenmez.
    #     mkdir() DEFAULT_OUTPUT için çağrılır; bu path genellikle geçerlidir.
    #
    # (b) Test: output_base_dir=None → DEFAULT_OUTPUT kullanılır, kusur tetiklenmez

    def test_given_none_dir_when_init_should_not_trigger_type_defect(self):
        """
        GIVEN: output_base_dir=None
        WHEN : JSONExporter oluşturulur
        THEN : Path(None) hiç çağrılmaz, TypeError tetiklenmez, DEFAULT_OUTPUT kullanılır

        [GÖREV 2b — geçersiz tip kusuru tetiklenmez]
        """
        with patch.object(Path, "mkdir"):
            exporter = JSONExporter(output_base_dir=None)
        assert exporter.output_base_dir is not None
        assert isinstance(exporter.output_base_dir, Path)

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. output_base_dir geçerli string verilirse → Path() başarılı →
    #     mkdir() başarılı → durum bozulmaz. mkdir PermissionError riski var
    #     ama gerçekleşmedi; infection yok.
    #
    # (b) Test: geçerli tmp_path → normal init

    def test_given_valid_string_dir_when_init_should_not_infect(self, tmp_path):
        """
        GIVEN: Geçerli, yazılabilir dizin string'i
        WHEN : JSONExporter oluşturulur
        THEN : Dizin oluşturulur, output_base_dir doğru set edilir, durum bozulmaz

        [GÖREV 3b — mkdir başarılı, PermissionError riski gerçekleşmedi, infection yok]
        """
        exporter = JSONExporter(output_base_dir=str(tmp_path / "output"))
        assert exporter.output_base_dir == tmp_path / "output"
        assert exporter.output_base_dir.exists()

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Boş string verildi, DEFAULT_OUTPUT sessizce kullanıldı (infection).
    #     Ama test yalnızca "exporter.output_base_dir None değil mi?" kontrol
    #     ederse hangi path'in seçildiğini görmez → failure yok.
    #
    # (b) Test: sadece attribute'un None olmadığını kontrol et

    def test_given_empty_string_when_only_attribute_existence_checked_infection_hidden(self):
        """
        GIVEN: output_base_dir="" → DEFAULT_OUTPUT kullanıldı (infection)
        WHEN : Yalnızca output_base_dir'in None olmadığı kontrol edilir
        THEN : Test geçer — yanlış path seçildiği görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        with patch.object(Path, "mkdir"):
            exporter = JSONExporter(output_base_dir="")

        # Yüzeysel kontrol → infection gizleniyor
        assert exporter.output_base_dir is not None  # Her zaman geçer


# ===========================================================================
# SINIR DEĞER TESTLERİ — __init__
# ===========================================================================

class TestInitBoundaryValues:

    def test_given_none_dir_when_init_should_use_default_output(self):
        """
        GIVEN: output_base_dir=None
        WHEN : JSONExporter oluşturulur
        THEN : output_base_dir DEFAULT_OUTPUT'a set edilir
        """
        with patch.object(Path, "mkdir"):
            exporter = JSONExporter(output_base_dir=None)
        assert "selected_methods" in str(exporter.output_base_dir)

    def test_given_valid_path_object_when_init_should_store_it(self, tmp_path):
        """
        GIVEN: Path nesnesi olarak output_base_dir
        WHEN : JSONExporter oluşturulur
        THEN : output_base_dir o path'e set edilir
        """
        out = tmp_path / "myout"
        exporter = JSONExporter(output_base_dir=out)
        assert exporter.output_base_dir == out

    def test_given_valid_dir_when_init_should_create_directory(self, tmp_path):
        """
        GIVEN: Henüz var olmayan dizin yolu
        WHEN : JSONExporter oluşturulur
        THEN : Dizin oluşturulur (parents=True, exist_ok=True)
        """
        new_dir = tmp_path / "a" / "b" / "c"
        JSONExporter(output_base_dir=new_dir)
        assert new_dir.exists()

    def test_given_existing_dir_when_init_should_not_raise(self, tmp_path):
        """
        GIVEN: Zaten var olan dizin
        WHEN : JSONExporter oluşturulur (exist_ok=True)
        THEN : Exception fırlatılmaz
        """
        JSONExporter(output_base_dir=tmp_path)  # crash olmamalı

    def test_given_init_when_called_twice_with_same_dir_should_not_raise(self, tmp_path):
        """
        GIVEN: Aynı dizinle iki kez JSONExporter oluşturuluyor
        WHEN : Her ikisi de __init__ çağrısı yapıyor
        THEN : İkinci çağrı da exception fırlatmaz (exist_ok=True garantisi)
        """
        JSONExporter(output_base_dir=tmp_path)
        JSONExporter(output_base_dir=tmp_path)  # crash olmamalı


# ===========================================================================
# export
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     export içinde:
#
#         data = [self.format_method(m) for m in methods]
#
#     List comprehension: eğer methods içindeki herhangi bir metot için
#     format_method() exception fırlatırsa, comprehension yarıda kesilir ve
#     except bloğuna düşülür → dosyaya HİÇBİR ŞEY yazılmaz.
#     100 metottan 1'i bozuk → 0 metot kaydedilir. Sessiz toplu kayıp.
#     Doğru davranış: bozuk metot atlanmalı, diğerleri kaydedilmeli.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     methods listesinde to_dict() exception fırlatacak en az 1 metot
#     VE en az 1 geçerli metot olmalıdır.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_one_broken_method_when_export_should_fail_losing_all_data
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestExport:

    def test_given_one_broken_method_when_export_should_fail_losing_all_data(self, tmp_path):
        """
        GIVEN: 3 geçerli metot + 1 to_dict() exception fırlatan metot (toplam 4)
        WHEN : export çağrılır
        THEN : Geçerli 3 metot yine de dosyaya yazılmalı (bozuk atlanmalı)
               Orijinal kodda comprehension çöker → 0 metot kaydedilir → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        exporter = make_exporter(tmp_path)

        good_methods = [make_method(f"good{i}") for i in range(3)]
        bad_method = MagicMock()
        bad_method.name = "broken"
        bad_method.to_dict.side_effect = RuntimeError("Serializasyon hatası")

        all_methods = good_methods + [bad_method]
        result = exporter.export(all_methods, "test_project")

        output_file = tmp_path / "test_project_methods.json"
        assert output_file.exists(), "Dosya oluşturulmalıydı — hiç yazılmadı: KUSUR aktif"

        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 3, (
            f"3 geçerli metot bekleniyor ama {len(data)} yazıldı. "
            f"Bozuk metot tüm export'u çökertip 0 yazdı — KUSUR aktif."
        )

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: project_name=None → "None_methods.json" sessizce
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     `file_path = self.output_base_dir / f"{project_name}_methods.json"`
    #     project_name=None ise f-string "None" string'e çevirir →
    #     "None_methods.json" dosyası oluşturulur. Hiçbir kontrol yok.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     project_name=None geçilmelidir.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_none_project_name_when_export_should_fail_creating_none_filename(self, tmp_path):
        """
        GIVEN: project_name=None
        WHEN : export çağrılır
        THEN : ValueError fırlatılmalı (geçersiz proje adı)
               Orijinal kodda "None_methods.json" sessizce oluşturuluyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        exporter = make_exporter(tmp_path)
        method = make_method("foo")

        with pytest.raises((ValueError, TypeError)):
            exporter.export([method], None)

        # Orijinal kod ValueError fırlatmıyor → test BAŞARISIZ olur

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 3: project_name path separator içeriyor
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     project_name="proj/sub" → file_path = output_base_dir / "proj/sub_methods.json"
    #     Bu alt dizin oluşturma girişimine veya path traversal'a yol açar.
    #     Sanitizasyon yapılmıyor.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     project_name "/" veya "\" içermelidir.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_project_name_with_path_separator_when_export_should_fail_allowing_traversal(self, tmp_path):
        """
        GIVEN: project_name="proj/sub" (dizin ayırıcı içeriyor)
        WHEN : export çağrılır
        THEN : ValueError fırlatılmalı (geçersiz proje adı — sanitizasyon gerekli)
               Orijinal kodda sanitizasyon yok → path traversal riski → BAŞARISIZ

        [GÖREV 1c — KUSUR 3 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        exporter = make_exporter(tmp_path)
        method = make_method("foo")

        with pytest.raises((ValueError, OSError)):
            exporter.export([method], "proj/sub")

        # Orijinal kod ValueError fırlatmıyor → test BAŞARISIZ olur

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. methods=[] (boş liste) ise `if not methods:` dalı erken return eder.
    #     format_method comprehension'a hiç girilmez → bozuk metot kusuru tetiklenmez.
    #     project_name kontrolüne de ulaşılmaz.
    #
    # (b) Test: boş methods → erken return, hiçbir kusur tetiklenmez

    def test_given_empty_methods_when_export_should_not_trigger_any_defect(self, tmp_path):
        """
        GIVEN: methods=[] (boş liste)
        WHEN : export çağrılır
        THEN : Erken return yapılır, comprehension ve project_name kusurları tetiklenmez

        [GÖREV 2b — tüm kusurlar tetiklenmez]
        """
        exporter = make_exporter(tmp_path)
        result = exporter.export([], "project")
        assert result is False

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Tüm metotlar geçerli ve project_name temiz bir string ise
    #     comprehension ve dosya yazma başarılı → durum bozulmaz.
    #
    # (b) Test: geçerli input → normal export

    def test_given_valid_methods_and_name_when_export_should_not_infect(self, tmp_path):
        """
        GIVEN: Geçerli metotlar, geçerli project_name
        WHEN : export çağrılır
        THEN : Tüm metotlar dosyaya yazılır, True döner, durum bozulmaz

        [GÖREV 3b — comprehension/project_name kusurları çalışır ama infection yok]
        """
        exporter = make_exporter(tmp_path)
        methods = [make_method("a"), make_method("b"), make_method("c")]

        result = exporter.export(methods, "myproject")

        assert result is True
        output_file = tmp_path / "myproject_methods.json"
        assert output_file.exists()
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 3

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. 1 bozuk metot var, tüm export çöktü, 0 metot yazıldı (infection).
    #     Ama test sadece "export False döndü mü?" kontrol ederse eksik yazılan
    #     metot sayısını görmez → failure yok.
    #
    # (b) Test: return değerini kontrol et, yazılan metot sayısını değil

    def test_given_broken_method_when_only_return_value_checked_infection_hidden(self, tmp_path):
        """
        GIVEN: 1 bozuk metot (infection: export False dönüyor, 2 geçerli metot kayıp)
        WHEN : Yalnızca export'un False döndüğü kontrol edilir
        THEN : Test geçer — 2 geçerli metodun kaybedildiği görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        exporter = make_exporter(tmp_path)

        bad_method = MagicMock()
        bad_method.to_dict.side_effect = RuntimeError("Hata")
        good_methods = [make_method("g1"), make_method("g2")]

        result = exporter.export(good_methods + [bad_method], "proj")

        # Yüzeysel kontrol → infection gizleniyor
        # (result True veya False olabilir; 2 geçerli metodun kaybolduğu sorgulanmıyor)
        assert isinstance(result, bool)


# ===========================================================================
# SINIR DEĞER TESTLERİ — export
# ===========================================================================

class TestExportBoundaryValues:

    def test_given_empty_methods_when_export_should_return_false(self, tmp_path):
        """
        GIVEN: Boş methods listesi
        WHEN : export çağrılır
        THEN : False döner
        """
        assert make_exporter(tmp_path).export([], "proj") is False

    def test_given_empty_methods_when_export_should_print_warning(self, tmp_path, capsys):
        """
        GIVEN: Boş methods listesi
        WHEN : export çağrılır
        THEN : Uyarı mesajı print edilir
        """
        make_exporter(tmp_path).export([], "myproject")
        captured = capsys.readouterr()
        assert "Uyarı" in captured.out or "myproject" in captured.out

    def test_given_empty_methods_when_export_should_not_create_file(self, tmp_path):
        """
        GIVEN: Boş methods listesi
        WHEN : export çağrılır
        THEN : Dosya oluşturulmaz
        """
        make_exporter(tmp_path).export([], "proj")
        assert not (tmp_path / "proj_methods.json").exists()

    def test_given_single_method_when_export_should_write_one_element_json(self, tmp_path):
        """
        GIVEN: Tek metot
        WHEN : export çağrılır
        THEN : JSON dosyasında tek eleman bulunur
        """
        exporter = make_exporter(tmp_path)
        exporter.export([make_method("solo")], "proj")
        with open(tmp_path / "proj_methods.json", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1

    def test_given_valid_export_when_called_should_return_true(self, tmp_path):
        """
        GIVEN: Geçerli metotlar
        WHEN : export çağrılır
        THEN : True döner
        """
        result = make_exporter(tmp_path).export([make_method()], "proj")
        assert result is True

    def test_given_valid_export_when_called_should_create_correct_filename(self, tmp_path):
        """
        GIVEN: project_name="django"
        WHEN : export çağrılır
        THEN : "django_methods.json" dosyası oluşturulur
        """
        make_exporter(tmp_path).export([make_method()], "django")
        assert (tmp_path / "django_methods.json").exists()

    def test_given_valid_export_when_called_should_write_valid_json(self, tmp_path):
        """
        GIVEN: Geçerli metotlar
        WHEN : export çağrılır
        THEN : Dosya geçerli JSON formatındadır (json.load başarılı)
        """
        make_exporter(tmp_path).export([make_method("foo")], "proj")
        with open(tmp_path / "proj_methods.json", encoding="utf-8") as f:
            data = json.load(f)  # exception fırlatmamalı
        assert isinstance(data, list)

    def test_given_valid_export_when_called_should_use_utf8_encoding(self, tmp_path):
        """
        GIVEN: Türkçe karakter içeren metot verisi
        WHEN : export çağrılır
        THEN : Dosya UTF-8 ile doğru okunabilir (ensure_ascii=False)
        """
        exporter = make_exporter(tmp_path)
        method = make_method("türkçe", to_dict_result={"name": "türkçe_metot", "body": "geç"})
        exporter.export([method], "proj")
        with open(tmp_path / "proj_methods.json", encoding="utf-8") as f:
            content = f.read()
        assert "türkçe" in content

    def test_given_valid_export_when_called_should_use_indent_2(self, tmp_path):
        """
        GIVEN: Geçerli metot
        WHEN : export çağrılır
        THEN : JSON dosyası indent=2 ile formatlanmıştır (okunabilir format)
        """
        make_exporter(tmp_path).export([make_method()], "proj")
        with open(tmp_path / "proj_methods.json", encoding="utf-8") as f:
            content = f.read()
        assert "  " in content  # indent=2 boşluk içerir

    def test_given_multiple_methods_when_export_should_write_all(self, tmp_path):
        """
        GIVEN: 5 geçerli metot
        WHEN : export çağrılır
        THEN : JSON dosyasında 5 eleman bulunur
        """
        methods = [make_method(f"m{i}") for i in range(5)]
        make_exporter(tmp_path).export(methods, "proj")
        with open(tmp_path / "proj_methods.json", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 5

    def test_given_write_error_when_export_should_return_false(self, tmp_path):
        """
        GIVEN: Dosya yazma sırasında OSError fırlatılıyor
        WHEN : export çağrılır
        THEN : False döner, exception dışarıya sızmaz
        """
        exporter = make_exporter(tmp_path)
        with patch("builtins.open", side_effect=OSError("Disk hatası")):
            result = exporter.export([make_method()], "proj")
        assert result is False

    def test_given_write_error_when_export_should_print_error_message(self, tmp_path, capsys):
        """
        GIVEN: Dosya yazma sırasında OSError fırlatılıyor
        WHEN : export çağrılır
        THEN : Hata mesajı print edilir
        """
        exporter = make_exporter(tmp_path)
        with patch("builtins.open", side_effect=OSError("Disk dolu")):
            exporter.export([make_method()], "proj")
        captured = capsys.readouterr()
        assert "hata" in captured.out.lower() or "Hata" in captured.out

    def test_given_successful_export_when_called_should_print_save_message(self, tmp_path, capsys):
        """
        GIVEN: Başarılı export
        WHEN : export çağrılır
        THEN : Kaydedilen dosya yolunu içeren mesaj print edilir
        """
        make_exporter(tmp_path).export([make_method()], "proj")
        captured = capsys.readouterr()
        assert "Kaydedildi" in captured.out or "proj" in captured.out

    def test_given_export_called_twice_with_same_project_when_second_call_should_overwrite(self, tmp_path):
        """
        GIVEN: Aynı proje için export iki kez çağrılıyor, farklı içerikle
        WHEN : İkinci export çağrılır
        THEN : Dosya üzerine yazılır (ikinci export'un verisi geçerli)
        """
        exporter = make_exporter(tmp_path)
        exporter.export([make_method("first")], "proj")
        exporter.export([make_method("second"), make_method("third")], "proj")
        with open(tmp_path / "proj_methods.json", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2  # İkinci export geçerli


# ===========================================================================
# format_method
# ===========================================================================
#
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ — KUSUR 1
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
#     format_method içinde:
#
#         return method.to_dict()
#
#     method=None ise None.to_dict() → AttributeError fırlatır.
#     Bu exception yakalanmıyor. Çağıran export() içindeki except tarafından
#     yakalanır AMA bu durumda tüm export başarısız olur — geçerli diğer
#     metotlar da kaybolur.
#
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     method=None geçilmelidir.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_none_method_when_format_should_fail_with_attribute_error
#       [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olmalı]

class TestFormatMethod:

    def test_given_none_method_when_format_should_fail_with_attribute_error(self, tmp_path):
        """
        GIVEN: method=None
        WHEN : format_method çağrılır
        THEN : AttributeError dışarıya sızmamalı; ValueError veya TypeError fırlatılmalı
               Orijinal kodda None.to_dict() → ham AttributeError sızıyor → BAŞARISIZ

        [GÖREV 1c — KUSUR 1 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        exporter = make_exporter(tmp_path)

        try:
            exporter.format_method(None)
            pytest.fail("None için exception bekleniyor ama fırlatılmadı")
        except AttributeError:
            pytest.fail(
                "None.to_dict() AttributeError ham olarak dışarıya sızdı — "
                "ValueError ile sarılmalıydı: KUSUR aktif"
            )
        except (ValueError, TypeError):
            pass  # Düzeltilmiş: anlamlı exception → GEÇER

    # -----------------------------------------------------------------------
    # GÖREV 1c — KUSUR 2: to_dict() serialize edilemeyen değer döndürüyor
    # -----------------------------------------------------------------------
    #
    # (a) KUSUR NEDİR VE NEREDE?
    #     to_dict() başarıyla bir dict döndürür ama bu dict içinde JSON
    #     serialize edilemeyen değer varsa (ör. set, datetime, custom class)
    #     json.dump sırasında TypeError fırlatır. format_method bunu tespit
    #     etmez; hata export'un except bloğuna kadar taşınır. Tüm export çöker.
    #
    # (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
    #     to_dict() JSON serialize edilemeyen değer içeren dict döndürmeli.
    #
    # (c) BAŞARISIZLIĞI GÖSTEREN TEST

    def test_given_non_serializable_to_dict_when_format_should_fail_silently_in_export(self, tmp_path):
        """
        GIVEN: to_dict() set içeren dict döndürüyor (JSON serialize edilemez)
        WHEN : export çağrılır (format_method dolaylı çağrılır)
        THEN : Bu metot atlanmalı veya anlamlı hata verilmeli; geçerli metotlar yazılmalı
               Orijinal kodda json.dump TypeError → export tümüyle başarısız → BAŞARISIZ

        [GÖREV 1c — KUSUR 2 — orijinal kodla BAŞARISIZ olması beklenir]
        """
        exporter = make_exporter(tmp_path)

        bad_method = MagicMock()
        bad_method.name = "unserializable"
        bad_method.to_dict.return_value = {"deps": {1, 2, 3}}  # set: JSON uyumsuz

        good_method = make_method("good")

        result = exporter.export([bad_method, good_method], "proj")

        output_file = tmp_path / "proj_methods.json"
        if output_file.exists():
            with open(output_file, encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) >= 1, (
                "En az 'good' metot yazılmalıydı — serialize edilemeyen metot tümünü çökertmemeli"
            )
        else:
            pytest.fail(
                "Dosya hiç oluşturulmadı — serialize edilemeyen tek metot tüm export'u çökerttti: KUSUR aktif"
            )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. method geçerli bir MethodModel ve to_dict() düzgün dict
    #     döndürüyorsa AttributeError hiç oluşmaz.
    #
    # (b) Test: geçerli metot → to_dict() başarılı

    def test_given_valid_method_when_format_should_not_trigger_attribute_defect(self, tmp_path):
        """
        GIVEN: Geçerli MethodModel (to_dict() başarılı)
        WHEN : format_method çağrılır
        THEN : AttributeError tetiklenmez, dict döner

        [GÖREV 2b — None kusuru tetiklenmez]
        """
        exporter = make_exporter(tmp_path)
        method = make_method("foo", to_dict_result={"name": "foo"})
        result = exporter.format_method(method)
        assert result == {"name": "foo"}

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. method geçerli, to_dict() başarılı çalışıyor.
    #     None.to_dict() riski var ama None gelmedi → infection yok.
    #
    # (b) Test: birden fazla geçerli metot → hepsi başarılı

    def test_given_multiple_valid_methods_when_format_called_for_each_should_not_infect(self, tmp_path):
        """
        GIVEN: 5 geçerli metot, her biri için format_method çağrılıyor
        WHEN : format_method her metot için ayrı çağrılır
        THEN : Tümü başarılı, durum bozulmaz

        [GÖREV 3b — None path girilmez, infection yok]
        """
        exporter = make_exporter(tmp_path)
        methods = [make_method(f"m{i}", to_dict_result={"name": f"m{i}"}) for i in range(5)]
        results = [exporter.format_method(m) for m in methods]
        assert len(results) == 5
        assert all(isinstance(r, dict) for r in results)

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. method=None → AttributeError fırlatıldı (infection: exception
    #     export'a sızdı, tüm export çöktü). Ama test yalnızca "exception
    #     bir şekilde fırlatıldı mı?" kontrol edip türünü sormazsa
    #     AttributeError'ın ham sızdığını görmez → failure yok.
    #
    # (b) Test: exception fırlatıldığını teyit et ama türünü kontrol etme

    def test_given_none_method_when_any_exception_accepted_infection_hidden(self, tmp_path):
        """
        GIVEN: method=None → AttributeError ham olarak sızıyor (infection)
        WHEN : Test herhangi bir exception'ı kabul ediyor
        THEN : Test geçer — exception'ın ham AttributeError olduğu ve
               anlamlı mesaj taşımadığı görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        exporter = make_exporter(tmp_path)
        raised = False
        try:
            exporter.format_method(None)
        except Exception:
            raised = True

        # Yüzeysel kontrol → infection gizleniyor (AttributeError mi ValueError mi bilinmiyor)
        assert raised  # Bir exception geldi — ama türü sorgulanmadı


# ===========================================================================
# SINIR DEĞER TESTLERİ — format_method
# ===========================================================================

class TestFormatMethodBoundaryValues:

    def test_given_valid_method_when_format_should_return_dict(self, tmp_path):
        """
        GIVEN: Geçerli MethodModel
        WHEN : format_method çağrılır
        THEN : dict tipinde değer döner
        """
        exporter = make_exporter(tmp_path)
        result = exporter.format_method(make_method())
        assert isinstance(result, dict)

    def test_given_method_when_format_should_call_to_dict(self, tmp_path):
        """
        GIVEN: Geçerli MethodModel
        WHEN : format_method çağrılır
        THEN : method.to_dict() tam olarak 1 kez çağrılır
        """
        exporter = make_exporter(tmp_path)
        method = make_method()
        exporter.format_method(method)
        method.to_dict.assert_called_once()

    def test_given_method_when_format_should_return_to_dict_result_unchanged(self, tmp_path):
        """
        GIVEN: to_dict() belirli bir dict döndürüyor
        WHEN : format_method çağrılır
        THEN : format_method to_dict()'in döndürdüğü dict'i değiştirmeden döndürür
        """
        exporter = make_exporter(tmp_path)
        expected = {"name": "foo", "body": "def foo(): pass", "complexity": 5}
        method = make_method("foo", to_dict_result=expected)
        result = exporter.format_method(method)
        assert result == expected

    def test_given_method_with_empty_dict_when_format_should_return_empty_dict(self, tmp_path):
        """
        GIVEN: to_dict() boş dict döndürüyor
        WHEN : format_method çağrılır
        THEN : Boş dict döner, exception fırlatılmaz
        """
        exporter = make_exporter(tmp_path)
        method = make_method("empty", to_dict_result={})
        result = exporter.format_method(method)
        assert result == {}

    def test_given_method_with_nested_dict_when_format_should_preserve_structure(self, tmp_path):
        """
        GIVEN: to_dict() iç içe dict döndürüyor
        WHEN : format_method çağrılır
        THEN : İç içe yapı korunur
        """
        exporter = make_exporter(tmp_path)
        nested = {"name": "foo", "complexity": {"cyclomatic": 5, "cognitive": 3}}
        method = make_method("foo", to_dict_result=nested)
        result = exporter.format_method(method)
        assert result["complexity"]["cyclomatic"] == 5

    def test_given_method_with_unicode_values_when_format_should_preserve_unicode(self, tmp_path):
        """
        GIVEN: to_dict() Türkçe/unicode değerler içeren dict döndürüyor
        WHEN : format_method çağrılır
        THEN : Unicode değerler bozulmadan döner
        """
        exporter = make_exporter(tmp_path)
        data = {"name": "hesapla_çıktı", "body": "işlem yap"}
        method = make_method("hesapla", to_dict_result=data)
        result = exporter.format_method(method)
        assert result["name"] == "hesapla_çıktı"

    def test_given_to_dict_raises_when_format_should_propagate_exception(self, tmp_path):
        """
        GIVEN: to_dict() RuntimeError fırlatıyor
        WHEN : format_method çağrılır
        THEN : Exception dışarıya sızar (format_method yakalamıyor — export'a bırakılıyor)

        Not: Bu mevcut davranışı belgeler. Düzeltme export katmanında yapılmalı.
        """
        exporter = make_exporter(tmp_path)
        method = MagicMock()
        method.to_dict.side_effect = RuntimeError("to_dict başarısız")

        with pytest.raises(RuntimeError):
            exporter.format_method(method)

    def test_given_format_method_return_value_type_should_match_to_dict_return(self, tmp_path):
        """
        GIVEN: to_dict() dict döndürüyor
        WHEN : format_method çağrılır
        THEN : Dönüş tipi to_dict()'in tipiyle aynıdır (format_method dönüşüm yapmaz)
        """
        exporter = make_exporter(tmp_path)
        method = make_method()
        result = exporter.format_method(method)
        assert type(result) is type(method.to_dict.return_value)