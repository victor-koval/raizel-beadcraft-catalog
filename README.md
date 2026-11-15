# Raizel Beadcraft • Preciosa Ornela 10/0 Catalog

[![Catalog Validation](https://github.com/victor-koval/raizel-beadcraft-catalog/actions/workflows/validate_catalog.yml/badge.svg)](https://github.com/victor-koval/raizel-beadcraft-catalog/actions/workflows/validate_catalog.yml)
![Total Beads](https://img.shields.io/badge/Preciosa%2010%2F0-613%20кольорів-ff69b4)
![License](https://img.shields.io/badge/License-MIT-blue)

Офіційний відкритий онлайн-каталог чеського бісеру **Preciosa Ornela** розміру **10/0** для мобільного застосунку **«Raizel Beadcraft»**.

- **Кількість відтінків у базі:** <!-- COUNT_START -->**613 артикулів**<!-- COUNT_END -->
- **Останнє оновлення каталогу:** <!-- DATE_START -->2026-11-15<!-- DATE_END -->
- **Пряме посилання на сирий JSON для додатка:**  
  `https://raw.githubusercontent.com/victor-koval/raizel-beadcraft-catalog/main/preciosa_palette.json`

---

## Структура палітри (`preciosa_palette.json`)

Кожен елемент каталогу має чітко типізовану структуру:

```json
[
  {
    "code": "93190",
    "nameUk": "Червоний насичений глухий",
    "finish": "OPAQUE",
    "hex": "#D32F2F",
    "symbol": "■"
  }
]
```

### Поля:
- `code` (*string*): 5-значний офіційний артикул Preciosa Ornela (00050–98370).
- `nameUk` (*string*): Назва кольору українською мовою за традиційною термінологією бісероплетіння.
- `finish` (*string*): Тип покриття:
  - `OPAQUE` — глухий / непрозорий;
  - `TRANSPARENT` — прозорий натуральний;
  - `SILVER_LINED` — вогник (зі срібною серединкою);
  - `LUSTRE` — перламутровий / перлинний глянець;
  - `METALLIC` — металік;
  - `MATTE` — матовий / сатиновий;
  - `IRIS` — райдужний бензиновий (хамелеон).
- `hex` (*string*): 7-символьний шістнадцятковий код кольору (`#RRGGBB`).
- `symbol` (*string*): Графічний символ для друку чорно-білих схем та легенд розрахунку.

---

## Як оновлюється каталог

Автоматичного завантаження кольорів від постачальників **немає** — каталог ведеться вручну.

1. Додайте або виправте артикули в `preciosa_palette.json`
   (або в списках `scripts/build_comprehensive_catalog.py` і перезапустіть його).
2. Запустіть `python scripts/validate_catalog.py --fix` — файл буде відсортовано за кодом,
   у README оновиться кількість і дата (лише якщо каталог справді змінився).
3. Закомітьте в `master`.

GitHub Actions (`.github/workflows/validate_catalog.yml`) на кожен push і pull request перевіряє
обов'язкові поля, тип покриття, формат HEX і коду, унікальність кодів та сортування,
а після push у `master` віддзеркалює його в `main` — саме звідти додаток бере каталог.

Додаток Raizel Beadcraft має цей каталог вбудованим і **автоматично підтягує оновлення** з гілки `main`
раз на добу під час запуску (умовний запит з ETag — без повторного завантаження, якщо нічого не змінилось).
Також можна оновити вручну кнопкою синхронізації в палітрі Preciosa. Отже, щойно зміни потрапляють у `main`,
нові кольори з'являються в додатку протягом доби.

### Джерело даних
Каталог побудовано з офіційного PDF виробника «Seed Beads – Rocailles» (Sample Cards):
`https://www.preciosa-ornela.com/content/files/downloads/Rocailles-Sample-Cards.pdf`
скриптом `scripts/build_from_pdf.py` (PDF у репозиторій не входить — завантажте за посиланням):

    python scripts/build_from_pdf.py Rocailles-Sample-Cards.pdf preciosa_palette.json preciosa_palette.json build_report.md

- `code` — з текстового шару PDF; лише коди, що є в картах виробника.
- `hex` — виміряний медіанний колір смужки бісеру поруч із кодом (без фону й бліків).
- `finish` — за назвою секції (Opaque, Silver Lined, Matt, Rainbow, Lustered, Metallic…);
  для секцій з неоднозначним покриттям (Terra Color Lined, Solgel Dyed, Striped, Harlequin, Cornelian тощо) відповідність задана явно в скрипті.
- Багатоколірний бісер (смужки, арлекін, мелафір, травертин) має лише усереднений `hex` і позначку в назві;
  додаток не підставляє його автоматично замість суцільних кольорів.
- `nameUk` — описова назва за кольором і покриттям з позначкою спецефектів («зі смужками», «сфінкс», «фарбований»).

### Відомі обмеження
- Виробник попереджає, що кольори на екрані можуть відрізнятися від реальних; HEX — це вимірювання зі зразків у PDF.
- Символи (`symbol`) повторюються між артикулами; додаток призначає унікальні символи в межах кожної схеми.
