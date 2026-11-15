# Raizel Beadcraft • Preciosa Ornela 10/0 Catalog

[![Catalog Sync & Validation](https://github.com/victor-koval/raizel-beadcraft-catalog/actions/workflows/update_catalog.yml/badge.svg)](https://github.com/victor-koval/raizel-beadcraft-catalog/actions/workflows/update_catalog.yml)
![Total Beads](https://img.shields.io/badge/Preciosa%2010%2F0-502%20кольорів-ff69b4)
![License](https://img.shields.io/badge/License-MIT-blue)

Офіційний відкритий онлайн-каталог чеського бісеру **Preciosa Ornela** розміру **10/0** для мобільного застосунку **«Raizel Beadcraft»**.

- **Кількість відтінків у базі:** <!-- COUNT_START -->**502 артикулів**<!-- COUNT_END -->
- **Останнє оновлення:** <!-- DATE_START -->2026-11-15 10:57 UTC<!-- DATE_END -->
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

## Автоматичне оновлення (GitHub Actions)

Репозиторій налаштований на регулярну синхронізацію та валідацію:
1. **Періодичний запуск (Cron):** Щомісяця 1-го числа о 03:00 UTC виконується робочий процес `.github/workflows/update_catalog.yml`.
2. **Ручний запуск (workflow_dispatch):** Можна запустити перевірку та синхронізацію в будь-який момент через вкладку **Actions** -> **Update & Validate Preciosa Catalog** -> **Run workflow**.
3. **Автокоміт:** Якщо скрипт виявляє нові артикули або корективи, зміни автоматично комітяться від імені `github-actions[bot]`.
