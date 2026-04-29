# Faulty Tests Analysis

Bu dosya, LLM tarafından üretilen hatalı pytest testlerini sınıflandırmak ve bu testlerin neden hatalı olduğunu açıklamak için hazırlanmıştır.

Amaç, postprocess aşamasında uygulanacak **rule-based repair** ve **LLM-based self-debug** mekanizmalarına temel oluşturmaktır.

---

## Hata Kategorileri

| ID | Hata Türü | Repair Yöntemi |
|----|-----------|----------------|
| T001 | SyntaxError | Rule-based |
| T002 | IndentationError | Rule-based |
| T003 | NameError (Missing Import) | Rule-based / LLM-based |
| T004 | ModuleNotFoundError | Rule-based |
| T005 | TypeError: Missing Argument | Rule-based / LLM-based |
| T006 | TypeError: Wrong Argument Type | LLM-based |
| T007 | AssertionError (Wrong Expected Value) | LLM-based / Rule-based |
| T008 | Weak / Meaningless Assertion | LLM-based |
| T009 | Fixture Error (FixtureNotFound) | LLM-based |
| T010 | Flaky Test | LLM-based |

---

## T001 — SyntaxError

**Hata Türü:** `SyntaxError`  
**Repair Yöntemi:** Rule-based

### Hatalı Test

```python
def test_add()
    assert add(2, 3) == 5
```

### Neden Hatalı?

Fonksiyon tanımından sonra `:` karakteri eksiktir. Python kodu çalıştırmadan önce parse ettiği için bu test pytest aşamasına geçmeden hata verir.

### Düzeltilmiş Test

```python
def test_add():
    assert add(2, 3) == 5
```

---

## T002 — IndentationError (Girinti Hatası)

**Hata Türü:** `IndentationError`  
**Repair Yöntemi:** Rule-based

### Hatalı Test

```python
def test_add():
assert add(2, 3) == 5
```

### Neden Hatalı?

Python girintiye duyarlı bir dildir. Fonksiyon gövdesindeki kod satırı girintilenmediği için test çalıştırılamaz.

### Düzeltilmiş Test

```python
def test_add():
    assert add(2, 3) == 5
```

---

## T003 — Missing Import / NameError

**Hata Türü:** `NameError`  
**Repair Yöntemi:** Rule-based veya LLM-based

### Hatalı Test

```python
def test_add():
    assert add(2, 3) == 5
```

### Neden Hatalı?

`add` fonksiyonu test dosyasında tanımlı değildir ve kaynak dosyadan import edilmemiştir. Pytest testi çalıştırırken fonksiyonu bulamaz.

### Düzeltilmiş Test

```python
from src.calculator import add

def test_add():
    assert add(2, 3) == 5
```

---

## T004 — ModuleNotFoundError

**Hata Türü:** `ModuleNotFoundError`  
**Repair Yöntemi:** Rule-based

### Hatalı Test

```python
from calculator import add

def test_add():
    assert add(2, 3) == 5
```

### Neden Hatalı?

Import yolu proje yapısına uygun değildir. Eğer kaynak dosya `src/calculator.py` altında bulunuyorsa, doğrudan `calculator` olarak import etmek başarısız olabilir.

### Düzeltilmiş Test

```python
from src.calculator import add

def test_add():
    assert add(2, 3) == 5
```

> **Not:** Testler proje kök dizininden çalıştırılmalıdır: `pytest tests/`

---

## T005 — TypeError: Missing Argument

**Hata Türü:** `TypeError`  
**Repair Yöntemi:** Rule-based veya LLM-based

### Hatalı Test

```python
def test_add():
    assert add(2) == 2
```

### Neden Hatalı?

`add` fonksiyonu iki parametre beklerken testte yalnızca bir parametre verilmiştir. Fonksiyon imzası ile test çağrısı uyumsuzdur.

### Düzeltilmiş Test

```python
def test_add():
    assert add(2, 0) == 2
```

---

## T006 — TypeError: Wrong Argument Type

**Hata Türü:** `TypeError`  
**Repair Yöntemi:** LLM-based

### Hatalı Test

```python
def test_divide():
    assert divide("10", 2) == 5
```

### Neden Hatalı?

Fonksiyon sayısal işlem beklerken `string` değer verilmiştir. Eğer fonksiyon string input desteklemiyorsa test yanlış input üretmiştir.

### Düzeltilmiş Test

```python
def test_divide():
    assert divide(10, 2) == 5
```

---

## T007 — AssertionError (Yanlış Beklenen Değer)

**Hata Türü:** `AssertionError`  
**Repair Yöntemi:** LLM-based veya güvenli durumlarda Rule-based

### Hatalı Test

```python
def test_add():
    assert add(2, 3) == 6
```

### Neden Hatalı?

Test çalıştırılabilir durumdadır fakat beklenen sonuç yanlıştır. `add(2, 3)` işleminin doğru çıktısı `5` olmalıdır.

### Düzeltilmiş Test

```python
def test_add():
    assert add(2, 3) == 5
```

---

## T008 — Weak / Meaningless Assertion (Zayıf / Anlamsız Doğrulama)

**Hata Türü:** Weak Assertion  
**Repair Yöntemi:** LLM-based

### Hatalı Test

```python
def test_add():
    result = add(2, 3)
    assert result is not None
```

### Neden Hatalı?

Bu test teknik olarak geçebilir fakat fonksiyonun doğru çalışıp çalışmadığını güçlü şekilde doğrulamaz. `add(2, 3)` sonucunun gerçekten `5` olup olmadığını kontrol etmez.

### Düzeltilmiş Test

```python
def test_add():
    assert add(2, 3) == 5
```

---

## T009 — Fixture Error (FixtureNotFound)

**Hata Türü:** `FixtureNotFound`  
**Repair Yöntemi:** LLM-based

### Hatalı Test

```python
def test_user_creation(user):
    assert user.name == "Ali"
```

### Neden Hatalı?

Testte `user` isimli fixture kullanılmıştır fakat pytest tarafında böyle bir fixture tanımlı değildir.

### Düzeltilmiş Test

```python
import pytest

@pytest.fixture
def user():
    return User(name="Ali")

def test_user_creation(user):
    assert user.name == "Ali"
```

---

## T010 — Flaky Test (Kararsız Test)

**Hata Türü:** Flaky Test  
**Repair Yöntemi:** LLM-based

### Hatalı Test

```python
import random

def test_random_value():
    assert random.randint(1, 10) == 5
```

### Neden Hatalı?

Test deterministik değildir. Aynı test bazı çalıştırmalarda geçebilir, bazı çalıştırmalarda başarısız olabilir.

### Düzeltilmiş Test — Sabit Değer

```python
def test_fixed_value():
    value = 5
    assert value == 5
```

### Düzeltilmiş Test — Random Seed ile

```python
import random

def test_random_value():
    random.seed(0)
    assert isinstance(random.randint(1, 10), int)
```