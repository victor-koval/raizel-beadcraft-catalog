"""Побудова каталогу preciosa_palette.json з офіційного PDF Preciosa «Rocailles Sample Cards».

Для кожного 5-значного коду з PDF (дублікати — перший запис):
- вимірюється медіанний колір смужки бісеру (RGB / HEX);
- визначається тип покриття (finish) з назви секції за пріоритетом:
  MATTE > IRIS > SILVER_LINED > METALLIC > LUSTRE > OPAQUE/TRANSPARENT;
- генерується опис кольору українською (nameUk) за тоном, світлотою та покриттям;
- призначається символ для схеми (symbol);
- незіставлені секції відкидаються та фіксуються як TODO у docs/catalog/build_report.md.
"""
import sys
import os
import re
import json
import statistics
import colorsys
import fitz
from PIL import Image

DPI = 300
SCALE = DPI / 72

CODE_PATTERN = re.compile(r"^\d{5}[A-Z]?$")

DEFAULT_SYMBOLS = [
    "●", "○", "▲", "△", "■", "□", "◆", "◇", "▼", "▽",
    "★", "☆", "⬡", "⬢", "◈", "¤", "♠", "♣", "♥", "♦",
    "◐", "◑", "◒", "◓"
]

def rgb_to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s * 100.0, l * 100.0

def match_finish(section_name):
    """Визначає finish за назвою секції з пріоритетом:
    MATTE > IRIS > SILVER_LINED > METALLIC > LUSTRE > OPAQUE/TRANSPARENT.
    """
    s = section_name.lower()
    has_matte = bool(re.search(r"\bmatt\b", s))
    has_iris = bool(re.search(r"\b(rainbow|iris|ab)\b", s))
    has_silver_lined = bool(re.search(r"\bsilver lined\b", s))
    has_metallic = bool(re.search(r"\b(metallic|plated|solgel metallic)\b", s))
    has_lustre = bool(re.search(r"\b(lustered|pearl|shell)\b", s))
    has_opaque = bool(re.search(r"\b(opaque|chalk|alabaster|natural opaque)\b", s))
    has_transparent = bool(re.search(r"\b(transparent|natural transparent)\b", s))

    if has_matte:
        return "MATTE"
    if has_iris:
        return "IRIS"
    if has_silver_lined:
        return "SILVER_LINED"
    if has_metallic:
        return "METALLIC"
    if has_lustre:
        return "LUSTRE"
    if has_opaque:
        return "OPAQUE"
    if has_transparent:
        return "TRANSPARENT"
    return None

def srgb_to_lab(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, rgb)
    x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) / 0.95047
    y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750)
    z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) / 1.08883
    f = lambda t: t ** (1.0 / 3.0) if t > 0.008856 else 7.787 * t + 16.0 / 116.0
    fx, fy, fz = f(x), f(y), f(z)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)

def section_effect_suffix(section_name):
    """Спецефекти секції, які медіанний колір не передає (смужки, сатин Sfinx, бронза, фарбування).
    Без цього смугастий білий бісер з червоними смужками називався б «Світло-сірий глухий»."""
    s = section_name.lower()
    parts = []
    if "striped" in s:
        parts.append("зі смужками")
    if "sfinx" in s:
        parts.append("сатиновий «сфінкс»")
    if "bronze" in s:
        parts.append("бронзовий відлив")
    if "dyed" in s or "terra color" in s:
        parts.append("фарбований")
    return (", " + ", ".join(parts)) if parts else ""


def generate_name_uk(rgb, finish):
    """Генерує детермінований опис кольору українською за виміряним RGB та типом покриття."""
    r, g, b = rgb
    L, a, lab_b = srgb_to_lab(rgb)
    chroma = (a**2 + lab_b**2) ** 0.5
    h, s, l = rgb_to_hsl(r, g, b)
    
    finish_desc = {
        "OPAQUE": "глухий",
        "TRANSPARENT": "прозорий",
        "SILVER_LINED": "прозорий вогник",
        "LUSTRE": "перламутровий",
        "METALLIC": "металік",
        "MATTE": "матовий",
        "IRIS": "бензиновий ірис"
    }.get(finish, "")
    
    # Ахроматичні (дуже низька насиченість у CIELAB або HSL)
    if chroma < 12.0 or s < 10.0:
        if L >= 88.0:
            base = "Білий"
        elif L >= 72.0:
            base = "Світло-сірий"
        elif L >= 40.0:
            base = "Сірий"
        elif L >= 22.0:
            base = "Темно-сірий"
        else:
            base = "Чорний"
        return f"{base} {finish_desc}".strip()
    
    # Префікс світлоти
    if L >= 75.0 or l >= 75.0:
        prefix = "Світло-"
    elif L <= 32.0 or l <= 30.0:
        prefix = "Темно-"
    else:
        prefix = ""
        
    # Специфічні групи: коричневі, бежеві, оливкові
    if 15 <= h < 45 and s < 65 and l < 58:
        if l < 35:
            base = "Темно-коричневий"
        elif l >= 50:
            base = "Світло-коричневий"
        else:
            base = "Коричневий"
        return f"{base} {finish_desc}".strip()
    
    if 25 <= h < 55 and s < 45 and l >= 65:
        base = "Бежевий" if l < 80 else "Світло-бежевий"
        return f"{base} {finish_desc}".strip()

    if 65 <= h < 105 and s < 50 and l < 45:
        base = "Темно-оливковий" if l < 32 else "Оливковий"
        return f"{base} {finish_desc}".strip()

    # Спектральні тони
    if h < 12 or h >= 350:
        tone = "червоний"
    elif 12 <= h < 25:
        tone = "кораловий"
    elif 25 <= h < 45:
        tone = "помаранчевий"
    elif 45 <= h < 60:
        tone = "бурштиновий"
    elif 60 <= h < 75:
        tone = "жовтий"
    elif 75 <= h < 95:
        tone = "салатовий"
    elif 95 <= h < 145:
        tone = "зелений"
    elif 145 <= h < 170:
        tone = "смарагдовий"
    elif 170 <= h < 195:
        tone = "бірюзовий"
    elif 195 <= h < 215:
        tone = "блакитний"
    elif 215 <= h < 240:
        if s > 65 and l < 40 and not prefix:
            tone = "синій кобальт"
        else:
            tone = "синій"
    elif 240 <= h < 260:
        tone = "волошковий"
    elif 260 <= h < 285:
        tone = "фіолетовий"
    elif 285 <= h < 320:
        tone = "бузковий" if l >= 50 else "пурпуровий"
    else:  # 320 <= h < 350
        tone = "рожевий" if l >= 65 else "малиновий"
        
    if prefix:
        if tone.startswith("синій кобальт"):
            full_color = prefix + "синій кобальт"
        else:
            full_color = prefix + tone
    else:
        full_color = tone
        
    full_color = full_color.capitalize()
    return f"{full_color} {finish_desc}".strip()

def build_catalog(pdf_path, old_palette_path, output_json_path, report_md_path):
    # Зчитуємо старий каталог для збереження символів
    old_symbols = {}
    if os.path.exists(old_palette_path):
        try:
            old_data = json.load(open(old_palette_path, encoding="utf-8"))
            for item in old_data:
                if "code" in item and "symbol" in item:
                    old_symbols[item["code"]] = item["symbol"]
        except Exception as e:
            print(f"Попередження: не вдалося зчитати старий каталог {old_palette_path}: {e}")

    doc = fitz.open(pdf_path)
    
    # 4 колонки по горизонталі
    cols = [
        (30, 160),
        (160, 290),
        (290, 420),
        (420, 560),
    ]

    found_entries = {}  # code -> dict
    unmatched_sections = {}  # section -> list of codes
    total_raw_codes = 0

    for pno in range(1, 6):  # сторінки 2-6 (індекси 1..5)
        page = doc[pno]
        pix = page.get_pixmap(dpi=DPI)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        d = page.get_text("dict")
        lines = []
        for b in d["blocks"]:
            if "lines" in b:
                for l in b["lines"]:
                    text = " ".join(s["text"].strip() for s in l["spans"] if s["text"].strip())
                    if text:
                        lines.append((l["bbox"], text))

        codes = [l for l in lines if CODE_PATTERN.match(l[1])]
        total_raw_codes += len(codes)

        for min_x, max_x in cols:
            col_codes = [c for c in codes if min_x <= c[0][0] < max_x]
            col_headers = []
            for l in lines:
                if min_x <= l[0][0] < max_x:
                    bbox, text = l
                    if pno == 1 and bbox[1] < 150:
                        # Пропускаємо розмірну сітку 13/0..4/0 на сторінці 2
                        continue
                    if CODE_PATTERN.match(text) or "displayed colors" in text or text.startswith("Seed Beads") or text.startswith("NEW ARRIVALS"):
                        continue
                    col_headers.append((bbox, text))
            col_headers.sort(key=lambda h: h[0][1])

            for c_bbox, code in col_codes:
                code_y = c_bbox[1]
                h_above = [h for h in col_headers if h[0][3] <= code_y + 2 and not h[1].startswith("ART No")]
                if not h_above:
                    sec = "?"
                else:
                    last_h = h_above[-1]
                    sec_lines = [last_h[1]]
                    cur_y = last_h[0][1]
                    for prev_h in reversed(h_above[:-1]):
                        if cur_y - prev_h[0][3] < 18 and not prev_h[1].startswith("ART No"):
                            sec_lines.insert(0, prev_h[1])
                            cur_y = prev_h[0][1]
                        else:
                            break
                    sec = " ".join(sec_lines)

                finish = match_finish(sec)
                if finish is None:
                    unmatched_sections.setdefault(sec, []).append(code)
                    continue

                if code in found_entries:
                    continue  # дублікати — перший запис

                # Вимірювання кольору смужки бісеру (ідентично до verify_catalog.py)
                x0, y0, x1, y1 = c_bbox
                sx0, sx1 = (x1 + 8) * SCALE, (x1 + 82) * SCALE
                sy0, sy1 = (y0 + (y1 - y0) * 0.30) * SCALE, (y0 + (y1 - y0) * 0.75) * SCALE
                crop = img.crop((int(sx0), int(sy0), int(sx1), int(sy1)))
                
                # Pillow сумісність
                if hasattr(crop, "get_flattened_data"):
                    px = list(crop.get_flattened_data())
                else:
                    px = list(crop.getdata())
                
                bead = [p for p in px if not (p[0] > 245 and p[1] > 245 and p[2] > 245)]
                if len(bead) < 20:
                    bead = px
                bead.sort(key=lambda p: sum(p))
                n = len(bead)
                core = bead[int(n * 0.15): int(n * 0.85)] or bead
                rgb = tuple(int(statistics.median(c[i] for c in core)) for i in range(3))
                hex_str = "#%02X%02X%02X" % rgb

                name_uk = generate_name_uk(rgb, finish) + section_effect_suffix(sec)
                symbol = old_symbols.get(code, DEFAULT_SYMBOLS[len(found_entries) % len(DEFAULT_SYMBOLS)])

                found_entries[code] = {
                    "code": code,
                    "nameUk": name_uk,
                    "finish": finish,
                    "hex": hex_str,
                    "symbol": symbol,
                    "_section": sec
                }

    # Сортування за code
    sorted_catalog = [
        {
            "code": entry["code"],
            "nameUk": entry["nameUk"],
            "finish": entry["finish"],
            "hex": entry["hex"],
            "symbol": entry["symbol"]
        }
        for code, entry in sorted(found_entries.items(), key=lambda x: x[0])
    ]

    # Запис preciosa_palette.json
    os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Статистика за finish
    finish_counts = {}
    for entry in sorted_catalog:
        f = entry["finish"]
        finish_counts[f] = finish_counts.get(f, 0) + 1

    # Запис build_report.md
    os.makedirs(os.path.dirname(os.path.abspath(report_md_path)), exist_ok=True)
    report_lines = [
        "# Звіт побудови каталогу Preciosa з офіційного PDF",
        "",
        f"- **Джерело:** `{pdf_path}`",
        f"- **Всього артикулів на сторінках PDF (із дублікатами):** {total_raw_codes}",
        f"- **Унікальних валідних кодів у каталозі:** {len(sorted_catalog)}",
        "",
        "## Розподіл за типом покриття (finish)",
        "",
        "| Покриття | Кількість кодів | Відсоток |",
        "|---|---|---|"
    ]
    for finish, count in sorted(finish_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(sorted_catalog)) * 100
        report_lines.append(f"| `{finish}` | {count} | {pct:.1f}% |")

    report_lines.extend([
        "",
        "## Секції, які не вдалося зіставити з правилами (TODO)",
        "",
        "Ці секції не містять ключових слів для однозначного визначення покриття згідно з правилами.",
        "Коди з цих секцій **НЕ** додавалися до каталогу (без вигадування).",
        "",
        "| Назва секції в PDF | Кількість входжень | Приклади кодів |",
        "|---|---|---|"
    ])

    for sec, codes in sorted(unmatched_sections.items(), key=lambda x: -len(x[1])):
        sample = ", ".join(codes[:5])
        if len(codes) > 5:
            sample += f" ... (разом {len(codes)})"
        report_lines.append(f"| `{sec}` | {len(codes)} | {sample} |")

    report_lines.append("")

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Збірку завершено успішно.")
    print(f"Збережено артикулів: {len(sorted_catalog)} у {output_json_path}")
    print(f"Звіт збережено у {report_md_path}")
    print("Розподіл finish:", finish_counts)

if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "tools/catalog/Rocailles-Sample-Cards.pdf"
    old_pal = sys.argv[2] if len(sys.argv) > 2 else "app/src/main/assets/preciosa_palette.json"
    out_json = sys.argv[3] if len(sys.argv) > 3 else "app/src/main/assets/preciosa_palette.json"
    report_md = sys.argv[4] if len(sys.argv) > 4 else "docs/catalog/build_report.md"
    build_catalog(pdf, old_pal, out_json, report_md)
