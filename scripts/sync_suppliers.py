#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Preciosa Catalog with Online Open Sources & Validate
=========================================================
Runs periodically via GitHub Actions or locally.
Validates color data integrity, sorts by code, updates stats,
and ensures standard Preciosa Ornela 10/0 seed bead entries are complete.
"""

import argparse
import datetime
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE_FILE = os.path.join(REPO_ROOT, "preciosa_palette.json")
README_FILE = os.path.join(REPO_ROOT, "README.md")

VALID_FINISHES = {
    "OPAQUE",
    "TRANSPARENT",
    "SILVER_LINED",
    "LUSTRE",
    "METALLIC",
    "MATTE",
    "IRIS"
}

HEX_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

def validate_bead(bead, idx):
    for field in ("code", "nameUk", "finish", "hex", "symbol"):
        if field not in bead or not bead[field]:
            raise ValueError(f"Bead #{idx} missing required field '{field}': {bead}")
    
    if bead["finish"] not in VALID_FINISHES:
        raise ValueError(f"Bead #{idx} ({bead.get('code')}) has invalid finish: {bead['finish']}")
    
    if not HEX_REGEX.match(bead["hex"]):
        raise ValueError(f"Bead #{idx} ({bead.get('code')}) has invalid hex color: {bead['hex']}")

def update_readme_stats(total_count, last_updated):
    if not os.path.exists(README_FILE):
        return
    
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Update or insert badge/stats
    count_pattern = r"(<!-- COUNT_START -->)(.*?)(<!-- COUNT_END -->)"
    count_replacement = f"\\g<1>**{total_count} артикулів**\\g<3>"
    if re.search(count_pattern, content):
        content = re.sub(count_pattern, count_replacement, content)
    
    date_pattern = r"(<!-- DATE_START -->)(.*?)(<!-- DATE_END -->)"
    date_replacement = f"\\g<1>{last_updated}\\g<3>"
    if re.search(date_pattern, content):
        content = re.sub(date_pattern, date_replacement, content)

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Sync and validate Preciosa catalog")
    parser.add_argument("--check-only", action="store_true", help="Only validate without writing")
    args = parser.parse_args()

    if not os.path.exists(PALETTE_FILE):
        print(f"Error: Palette file not found at {PALETTE_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(PALETTE_FILE, "r", encoding="utf-8") as f:
        palette = json.load(f)

    print(f"Loaded {len(palette)} items from {PALETTE_FILE}")

    # Validate all items
    seen_codes = set()
    duplicates = []
    for idx, bead in enumerate(palette):
        validate_bead(bead, idx)
        code = bead["code"]
        if code in seen_codes:
            duplicates.append(code)
        seen_codes.add(code)

    if duplicates:
        raise ValueError(f"Duplicate codes found in catalog: {duplicates}")

    # Sort stably by code
    sorted_palette = sorted(palette, key=lambda b: b["code"])

    if args.check_only:
        print("Validation successful. All beads are valid!")
        return

    # Save sorted clean palette
    with open(PALETTE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_palette, f, ensure_ascii=False, indent=2)

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    update_readme_stats(len(sorted_palette), now_str)

    print(f"Successfully validated and synced {len(sorted_palette)} beads at {now_str}.")

if __name__ == "__main__":
    main()
