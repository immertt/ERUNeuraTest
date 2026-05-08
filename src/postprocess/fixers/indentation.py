class IndentationFixer:
    """
    Python test kodlarındaki girinti hatalarını düzeltmek için
    kullanılan kural tabanlı fixer sınıfı.

    Düzeltme adımları:
    1. Tab karakterlerini space'e çevir
    2. Satır sonu boşluklarını temizle
    3. compile() ile hatayı yakala
    4. Hata mesajına göre ilgili rule'u çalıştır
    5. Tekrar compile et
    6. max_iterations kadar dene
    7. Düzelmiyorsa orijinal koda zarar vermeden en iyi sonucu döndür
    """

    def __init__(self, indent_size: int = 4, max_iterations: int = 5):
        self.indent_size = indent_size
        self.max_iterations = max_iterations

    def fix(self, code: str) -> str:
        """
        Verilen Python kodundaki girinti hatalarını düzeltmeye çalışır.
        """
        fixed_code = self._normalize_whitespace(code)

        for _ in range(self.max_iterations):
            try:
                compile(fixed_code, "<string>", "exec")
                return fixed_code
            except TabError:
                fixed_code = self._normalize_whitespace(fixed_code)
            except IndentationError as error:
                fixed_code = self._apply_indentation_rule(fixed_code, error)
            except SyntaxError:
                return fixed_code

        return fixed_code

    def _normalize_whitespace(self, code: str) -> str:
        """
        Tab karakterlerini 4 boşluğa çevirir ve satır sonu boşluklarını temizler.
        Boş string için '\n' döndürür — pipeline'ın kırılmaması için kasıtlı davranış.
        """
        lines = code.replace("\t", " " * self.indent_size).splitlines()
        return "\n".join(line.rstrip() for line in lines) + "\n"

    def _apply_indentation_rule(self, code: str, error: IndentationError) -> str:
        """
        IndentationError mesajına göre ilgili düzeltme kuralını uygular.
        """
        message = str(error)
        lineno = getattr(error, "lineno", None)

        if lineno is None:
            return code

        if "expected an indented block" in message:
            return self._fix_expected_indented_block(code, lineno)

        if "unexpected indent" in message:
            return self._fix_unexpected_indent(code, lineno)

        if "unindent does not match any outer indentation level" in message:
            return self._fix_unmatched_unindent(code, lineno)

        return code

    def _fix_expected_indented_block(self, code: str, lineno: int) -> str:
        """
        Blok açan satırdan sonra gelen satırı içeri alır.
        """
        lines = code.splitlines()

        target_index = lineno - 1

        if target_index < 0 or target_index >= len(lines):
            return code

        current_line = lines[target_index]
        current_indent = len(current_line) - len(current_line.lstrip())

        lines[target_index] = " " * (current_indent + self.indent_size) + current_line.lstrip()

        return "\n".join(lines) + "\n"

    def _fix_unexpected_indent(self, code: str, lineno: int) -> str:
        """
        Beklenmeyen fazla girintiyi azaltır.
        Hatalı satır ve altındaki bloğu birlikte kaydırır.
        """
        lines = code.splitlines()
        target_index = lineno - 1

        if target_index < 0 or target_index >= len(lines):
            return code

        # Hatalı satırın mevcut ve olması gereken indent'ini hesapla
        current_line = lines[target_index]
        current_indent = len(current_line) - len(current_line.lstrip())

        # Bir önceki anlamlı satırın indent'ine bak
        expected_indent = 0
        for index in range(target_index - 1, -1, -1):
            prev = lines[index]
            if prev.strip():
                prev_indent = len(prev) - len(prev.lstrip())
                # Önceki satır blok açıyorsa (: ile bitiyorsa) bir level içeri
                if prev.rstrip().endswith(":"):
                    expected_indent = prev_indent + self.indent_size
                else:
                    expected_indent = prev_indent
                break

        shift = current_indent - expected_indent  # ne kadar fazla indent var

        if shift <= 0:
            return code  # zaten sorun yok

        # Hatalı satırdan itibaren aynı veya daha derin indent'e sahip
        # tüm satırları birlikte geri kaydır
        new_lines = lines[:target_index]
        for i, line in enumerate(lines[target_index:]):
            if not line.strip():
                new_lines.append(line)
                continue
            line_indent = len(line) - len(line.lstrip())
            if line_indent >= current_indent:
                new_lines.append(" " * (line_indent - shift) + line.lstrip())
            else:
                # Blok bitti, kalan satırları olduğu gibi bırak
                new_lines.extend(lines[target_index + i:])
                break
        
        return "\n".join(new_lines) + "\n"

    def _fix_unmatched_unindent(self, code: str, lineno: int) -> str:
        """
        Uyumsuz girintiyi önceki anlamlı satırın girinti seviyesine yaklaştırır.
        """
        lines = code.splitlines()

        target_index = lineno - 1

        if target_index < 0 or target_index >= len(lines):
            return code

        line = lines[target_index]
        stripped = line.lstrip()

        previous_indent = 0

        for index in range(target_index - 1, -1, -1):
            previous_line = lines[index]

            if previous_line.strip():
                previous_indent = len(previous_line) - len(previous_line.lstrip())
                break

        lines[target_index] = " " * previous_indent + stripped

        return "\n".join(lines) + "\n"