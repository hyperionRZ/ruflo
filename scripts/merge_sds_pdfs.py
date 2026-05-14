#!/usr/bin/env python3
"""Download and merge NI-712 SDS PDFs from Neutron Industries."""

import os
import re
import sys
import requests
import pikepdf
from pathlib import Path

API_URL = "https://www.neutronindustries.com/safetydatasheet/list"
DOWNLOAD_DIR = Path("ni712_sds_downloads")
OUTPUT_FILE = "R_87474-16269.pdf"

# Files to download — (FileDisplayName to match in API, label for manifest, group_key for ordering)
TARGETS = [
    # Both versions
    ("NI-712 Dry Fine Mist Bamboo Lagoon_129568_SDS.pdf",             "NI-712 Dry Fine Mist Bamboo Lagoon",              "bamboo", 0, "Dry Fine Mist"),
    ("NI-712 Autoscents Total Release Bamboo Lagoon_129569_SDS.pdf",  "NI-712 Autoscents Total Release Bamboo Lagoon",   "bamboo", 1, "AutoScents"),
    ("NI-712 Warm Summer Nights Fine-Mist Dry Spray SDS",             "NI-712 Warm Summer Nights Fine-Mist Dry Spray",   "warm",   0, "Dry Fine Mist"),
    ("NI-712 Warm Summer Night SDS",                                   "NI-712 Warm Summer Night",                        "warm",   1, "Standard"),
    ("NI-712 Dry Fine Mist Passionfruit Citrus_129631_SDS",            "NI-712 Dry Fine Mist Passionfruit Citrus",        "passion",0, "Dry Fine Mist"),
    ("NI-712 Passionfruit Citrus SDS",                                 "NI-712 Passionfruit Citrus",                      "passion",1, "Standard"),
    ("NI-712 Orange Fine-Mist Dry Spray SDS",                          "NI-712 Orange Fine-Mist Dry Spray",               "orange", 0, "Dry Fine Mist"),
    ("NI-712 Fresh Orange SDS",                                        "NI-712 Fresh Orange",                             "orange", 1, "Standard"),
    # Singles
    ("NI-712 Clothesline Fresh SDS",                                   "NI-712 Clothesline Fresh",                        "clothesline", 0, "Standard"),
    ("NI-712 Sweet Lemon SDS",                                         "NI-712 Sweet Lemon",                              "sweetlemon",  0, "Standard"),
    ("NI-712 Botanical Bliss SDS",                                     "NI-712 Botanical Bliss",                          "botanical",   0, "Standard"),
    ("NI-712 Purely Lavender SDS",                                     "NI-712 Purely Lavender",                          "lavender",    0, "Standard"),
    ("AutoScents Tranquil Power SDS",                                  "AutoScents Tranquil Power",                       "tranquil",    0, "AutoScents"),
    ("AutoScents Happy Energy SDS",                                    "AutoScents Happy Energy",                         "happy",       0, "AutoScents"),
    ("Neutron Odor Eliminator - Super Dooper SDS",                     "Neutron Odor Eliminator - Super Dooper",          "superdooper",  0, "CS"),
]

# Explicit merge order (1-indexed from spec)
MERGE_ORDER = [
    "AutoScents Happy Energy SDS",
    "AutoScents Tranquil Power SDS",
    "NI-712 Botanical Bliss SDS",
    "NI-712 Clothesline Fresh SDS",
    "NI-712 Orange Fine-Mist Dry Spray SDS",
    "NI-712 Fresh Orange SDS",
    "NI-712 Dry Fine Mist Bamboo Lagoon_129568_SDS.pdf",
    "NI-712 Autoscents Total Release Bamboo Lagoon_129569_SDS.pdf",
    "NI-712 Dry Fine Mist Passionfruit Citrus_129631_SDS",
    "NI-712 Passionfruit Citrus SDS",
    "NI-712 Purely Lavender SDS",
    "Neutron Odor Eliminator - Super Dooper SDS",
    "NI-712 Sweet Lemon SDS",
    "NI-712 Warm Summer Nights Fine-Mist Dry Spray SDS",
    "NI-712 Warm Summer Night SDS",
]


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.neutronindustries.com/",
}


def fetch_inventory() -> dict:
    print(f"Fetching inventory from {API_URL} ...")
    r = requests.get(API_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    # Build lookup: FileDisplayName -> FileDownloadPath
    inventory = {}
    for item in data.get("Data", []):
        name = item.get("FileDisplayName", "").strip()
        path = item.get("FileDownloadPath", "").strip()
        if name and path:
            inventory[name] = path
    print(f"  Found {len(inventory)} entries in API.\n")
    return inventory


def download_pdf(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  [CACHED] {dest.name}")
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  [OK]     {dest.name}  ({len(r.content):,} bytes)")
        return True
    except Exception as exc:
        print(f"  [ERROR]  {dest.name}: {exc}")
        return False


def main():
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    inventory = fetch_inventory()

    # --- Step 1: Download ---
    print("=== STEP 1: Downloading PDFs ===\n")
    manifest = []  # (display_name, format, local_path | None, included, warning)

    target_lookup = {}  # FileDisplayName -> (label, format, local_path)

    for (api_name, label, _group, _order, fmt) in TARGETS:
        warning = ""
        local_path = None

        # Try exact match first
        download_url = inventory.get(api_name)

        # If not found, try stripping trailing ".pdf" from api_name and matching
        if not download_url:
            # Try matching without .pdf extension on lookup key
            stripped = api_name
            if stripped.endswith(".pdf"):
                stripped = stripped[:-4]
            download_url = inventory.get(stripped)

        if not download_url:
            warning = "NOT FOUND in API"
            print(f"  [WARN] '{api_name}' not found in API — skipping.")
            manifest.append((label, fmt, None, False, warning))
            target_lookup[api_name] = (label, fmt, None)
            continue

        # Construct a clean local filename
        safe_name = sanitize_filename(api_name)
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        dest = DOWNLOAD_DIR / safe_name

        ok = download_pdf(download_url, dest)
        if ok:
            local_path = dest
            manifest.append((label, fmt, dest, True, ""))
        else:
            warning = "Download failed"
            manifest.append((label, fmt, None, False, warning))

        target_lookup[api_name] = (label, fmt, local_path)

    print()

    # --- Step 2: Merge ---
    print("=== STEP 2: Merging PDFs ===\n")

    # Build ordered list of (api_name, label, fmt, local_path)
    ordered = []
    for api_name in MERGE_ORDER:
        entry = target_lookup.get(api_name)
        if entry is None:
            print(f"  [WARN] Merge-order entry '{api_name}' has no download record.")
            continue
        label, fmt, local_path = entry
        ordered.append((api_name, label, fmt, local_path))

    merged_count = 0
    pdf_out = pikepdf.Pdf.new()
    for api_name, label, fmt, local_path in ordered:
        if local_path and local_path.exists():
            try:
                src = pikepdf.Pdf.open(str(local_path))
                pdf_out.pages.extend(src.pages)
                merged_count += 1
                print(f"  [{merged_count:02d}] {label}  ({len(src.pages)} pages)")
            except Exception as exc:
                print(f"  [ERROR] Could not merge '{label}': {exc}")
        else:
            print(f"  [SKIP]  '{label}' — file not available")

    pdf_out.save(OUTPUT_FILE)

    size = os.path.getsize(OUTPUT_FILE)
    print(f"\n  Merged {merged_count} PDFs → {OUTPUT_FILE}  ({size:,} bytes)\n")

    # --- Step 3: Manifest ---
    print("=== STEP 3: Manifest ===\n")
    col_widths = (45, 16, 55, 10, 30)
    header = (
        f"{'Scent Name':<{col_widths[0]}} "
        f"{'Format':<{col_widths[1]}} "
        f"{'Source Filename':<{col_widths[2]}} "
        f"{'Included':<{col_widths[3]}} "
        f"{'Warnings'}"
    )
    sep = "-" * (sum(col_widths) + 4)
    print(header)
    print(sep)
    for label, fmt, local_path, included, warning in manifest:
        src = local_path.name if local_path else "—"
        inc = "yes" if included else "no"
        row = (
            f"{label:<{col_widths[0]}} "
            f"{fmt:<{col_widths[1]}} "
            f"{src:<{col_widths[2]}} "
            f"{inc:<{col_widths[3]}} "
            f"{warning}"
        )
        print(row)
    print()


if __name__ == "__main__":
    main()
