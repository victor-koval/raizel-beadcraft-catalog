#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Перевірка каталогу Preciosa Ornela 10/0 (preciosa_palette.json).

ВАЖЛИВО: скрипт НЕ завантажує дані від постачальників. Нові артикули додаються вручну:
відредагуйте preciosa_palette.json (або список у scripts/build_comprehensive_catalog.py
і перезапустіть його), потім запустіть:

    python scripts/validate_catalog.py --fix    # відсортувати + оновити статистику в README
    python scripts/validate_catalog.py          # лише перевірка (так робить CI)

Перевіряється: обов'язкові поля, тип покриття, формат HEX, унікальність кодів, сортування за кодом.
Попередження (не помилки): артикули з однаковим HEX та повторювані символи.
"""

import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE_FILE = os.path.join(REPO_ROOT, "preciosa_palette.json")
README_FILE = os.path.join(REPO_ROOT, "README.md")

VALID_FINISHES = {"OPAQUE", "TRANSPARENT", "SILVER_LINED", "LUSTRE", "METALLIC", "MATTE", "IRIS"}
HEX_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
CODE_REGEX = re.compile(r"^\d{5}[A-Z]?$")  # 5 цифр + необов'язкова літера варіанту (напр. 23980M)
REQUIRED = ("code", "nameUk", "finish", "hex", "symbol")


def validate(palette):
    errors = []
    for idx, bead in enumerate(palette):
        for field in REQUIRED:
            if not bead.get(field):
                errors.append(f"#{idx}: відсутнє поле '{field}': {bead}")
        code = bead.get("code", "")
        if code and not CODE_REGEX.match(code):
            errors.append(f"{code}: код має бути 5 цифр (+ необов'язкова велика літера)")
        if bead.get("finish") and bead["finish"] not in VALID_FINISHES:
            errors.append(f"{code}: невідомий тип покриття {bead['finish']}")
        if bead.get("hex") and not HEX_REGEX.match(bead["hex"]):
            errors.append(f"{code}: некоректний HEX {bead['hex']}")
    dup_codes = [c for c, n in Counter(b.get("code") for b in palette).items() if n > 1]
    if dup_codes:
        errors.append(f"Дублікати кодів: {dup_codes}")
    return errors


def warnings(palette):
    hex_groups = Counter(b["hex"].upper() for b in palette)
    shared = {h: n for h, n in hex_groups.items() if n > 1}
    symbols = Counter(b["symbol"] for b in palette)
    out = []
    if shared:
        worst = max(shared.items(), key=lambda kv: kv[1])
        out.append(f"{len(shared)} груп артикулів мають однаковий HEX (найбільша: {worst[0]} × {worst[1]}). "
                   f"HEX у каталозі наближені; додаток робить кольори унікальними автоматично.")
    out.append(f"{len(symbols)} різних символів на {len(palette)} артикулів; "
               f"додаток призначає унікальні символи в межах кожної схеми.")
    return out


def dump(palette):
    return json.dumps(palette, ensure_ascii=False, indent=2) + "\n"


def update_readme(total_count):
    if not os.path.exists(README_FILE):
        return
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    content = re.sub(r"(<!-- COUNT_START -->)(.*?)(<!-- COUNT_END -->)",
                     lambda m: f"{m.group(1)}**{total_count} артикулів**{m.group(3)}", content)
    content = re.sub(r"(<!-- DATE_START -->)(.*?)(<!-- DATE_END -->)",
                     lambda m: f"{m.group(1)}{today}{m.group(3)}", content)
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Перевірка каталогу Preciosa")
    parser.add_argument("--fix", action="store_true",
                        help="відсортувати файл за кодом і оновити статистику в README (лише якщо каталог змінився)")
    parser.add_argument("--check-only", action="store_true", help="синонім режиму за замовчуванням (сумісність)")
    args = parser.parse_args()

    with open(PALETTE_FILE, "r", encoding="utf-8") as f:
        raw = f.read()
    palette = json.loads(raw)
    print(f"Завантажено {len(palette)} артикулів")

    errors = validate(palette)
    if errors:
        print("ПОМИЛКИ:", *errors, sep="\n  ", file=sys.stderr)
        sys.exit(1)

    for w in warnings(palette):
        print("Попередження:", w)

    sorted_palette = sorted(palette, key=lambda b: b["code"])
    normalized = dump(sorted_palette)

    if not args.fix:
        if normalized != raw:
            print("Файл не відсортований за кодом або не відформатований. "
                  "Запустіть: python scripts/validate_catalog.py --fix", file=sys.stderr)
            sys.exit(1)
        print("Каталог коректний.")
        return

    readme_count = None
    if os.path.exists(README_FILE):
        m = re.search(r"<!-- COUNT_START -->\*\*(\d+)", open(README_FILE, encoding="utf-8").read())
        readme_count = int(m.group(1)) if m else None
    if normalized == raw and readme_count == len(sorted_palette):
        print("Змін немає — README не оновлюється.")
        return
    with open(PALETTE_FILE, "w", encoding="utf-8") as f:
        f.write(normalized)
    update_readme(len(sorted_palette))
    print(f"Каталог відсортовано, README оновлено ({len(sorted_palette)} артикулів).")


if __name__ == "__main__":
    main()
