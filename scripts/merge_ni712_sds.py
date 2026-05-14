#!/usr/bin/env python3
"""
Download NI-712 / AutoScents SDS PDFs from Neutron Industries and merge
them into a single PDF named R_87474-16269.pdf.

Requirements:
    pip install requests pypdf
"""

import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests pypdf")

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    sys.exit("Missing dependency: pip install requests pypdf")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DOWNLOAD_DIR = Path("ni712_sds_downloads")
OUTPUT_FILE   = "R_87474-16269.pdf"

# (display_name, direct_url)  — in merge order (1-15)
DOWNLOADS = [
    # 1
    ("AutoScents Happy Energy SDS",
     "https://neutronindustries.com/files/SDS/AutoScents_Happy_Energy_SDS_01302020122329.pdf"),
    # 2
    ("AutoScents Tranquil Power SDS",
     "https://neutronindustries.com/files/SDS/AutoScents_Tranquil_Power_SDS_09152020091017.pdf"),
    # 3
    ("NI-712 Botanical Bliss SDS",
     "https://neutronindustries.com/files/SDS/NI-712_Botanical_Bliss_SDS.pdf"),
    # 4
    ("NI-712 Clothesline Fresh SDS",
     "https://neutronindustries.com/files/SDS/NI-712_Clothesline_Fresh_SDS.pdf"),
    # 5
    ("NI-712 Orange Fine-Mist Dry Spray SDS",
     "https://neutronindustries.com/files/SDS/NI_712_Orange_Fine_Mist_Dry_Spray_SDS_09212023092318.pdf"),
    # 6
    ("NI-712 Fresh Orange SDS",
     "https://neutronindustries.com/files/SDS/NI-712_Fresh_Orange_SDS.pdf"),
    # 7
    ("NI-712 Dry Fine Mist Bamboo Lagoon_129568_SDS.pdf",
     "https://neutronindustries.com/files/SDS/NI_712_Dry_Fine_Mist_Bamboo_Lagoon_129568_SDS_pdf_10282025125700.pdf"),
    # 8
    ("NI-712 Autoscents Total Release Bamboo Lagoon_129569_SDS.pdf",
     "https://neutronindustries.com/files/SDS/NI_712_Autoscents_Total_Release_Bamboo_Lagoon_129569_SDS_pdf_10282025125646.pdf"),
    # 9
    ("NI-712 Dry Fine Mist Passionfruit Citrus_129631_SDS",
     "https://neutronindustries.com/files/SDS/NI_712_Dry_Fine_Mist_Passionfruit_Citrus_129631_SDS_09302025112243.pdf"),
    # 10
    ("NI-712 Passionfruit Citrus SDS",
     "https://neutronindustries.com/files/SDS/NI-712_Passionfruit_Citrus_SDS.pdf"),
    # 11
    ("NI-712 Purely Lavender SDS",
     "https://neutronindustries.com/files/SDS/NI_712_Purely_Lavender_SDS_12092021072626.pdf"),
    # 12
    ("Neutron Odor Eliminator - Super Dooper SDS",
     "https://neutronindustries.com/files/SDS/Neutron_Odor_Eliminator_Super_Dooper_SDS_12102024103102.pdf"),
    # 13
    ("NI-712 Sweet Lemon SDS",
     "https://neutronindustries.com/files/SDS/NI-712_Sweet_Lemon_SDS.pdf"),
    # 14
    ("NI-712 Warm Summer Nights Fine-Mist Dry Spray SDS",
     "https://neutronindustries.com/files/SDS/NI_712_Warm_Summer_Nights_Dry_Fine_Mist_Spray_SDS_01312023111754.pdf"),
    # 15
    ("NI-712 Warm Summer Night SDS",
     "https://neutronindustries.com/files/SDS/NI-712_Warm_Summer_Night_SDS.pdf"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def infer_format(name: str) -> str:
    n = name.lower()
    if name.startswith("AutoScents"):
        return "AutoScents"
    if "fine mist" in n or "fine-mist" in n or "dry fine mist" in n:
        return "Dry Fine Mist"
    if "super dooper" in n:
        return "CS"
    return "Standard"


def download(name: str, url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  [CACHED] {dest.name}")
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        if "application/pdf" not in r.headers.get("Content-Type", "") and len(r.content) < 1000:
            print(f"  [ERROR]  {name}: unexpected response (not a PDF?)")
            return False
        dest.write_bytes(r.content)
        print(f"  [OK]     {dest.name}  ({len(r.content):,} bytes)")
        return True
    except Exception as exc:
        print(f"  [ERROR]  {name}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    print(f"=== STEP 1: Downloading {len(DOWNLOADS)} PDFs ===\n")

    results = []   # (name, fmt, local_path | None, warning)

    for name, url in DOWNLOADS:
        fmt       = infer_format(name)
        safe_name = sanitize(name)
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        dest = DOWNLOAD_DIR / safe_name

        ok = download(name, url, dest)
        results.append((name, fmt, dest if ok else None, "" if ok else "Download failed"))

    print()

    # --- Merge ---
    print("=== STEP 2: Merging PDFs ===\n")

    writer      = PdfWriter()
    page_total  = 0
    merged      = 0

    for idx, (name, fmt, local_path, _warn) in enumerate(results, start=1):
        if local_path and local_path.exists():
            try:
                reader      = PdfReader(str(local_path))
                page_count  = len(reader.pages)
                writer.append(reader)
                merged     += 1
                page_total += page_count
                print(f"  [{idx:02d}] {name:<55} ({page_count} pages)")
            except Exception as exc:
                print(f"  [ERROR] [{idx:02d}] {name}: {exc}")
                results[idx - 1] = (name, fmt, None, f"Merge error: {exc}")
        else:
            print(f"  [SKIP]  [{idx:02d}] {name}")

    with open(OUTPUT_FILE, "wb") as f:
        writer.write(f)

    size = os.path.getsize(OUTPUT_FILE)
    print(f"\n  Merged {merged}/{len(DOWNLOADS)} SDS sheets  |  {page_total} pages  |  {size:,} bytes")
    print(f"  Output: {OUTPUT_FILE}\n")

    # --- Manifest ---
    print("=== STEP 3: Manifest ===\n")

    C = (4, 45, 16, 52, 10, 25)
    hdr = (
        f"{'#':<{C[0]}} "
        f"{'Scent Name':<{C[1]}} "
        f"{'Format':<{C[2]}} "
        f"{'Source Filename':<{C[3]}} "
        f"{'Included':<{C[4]}} "
        f"Warnings"
    )
    print(hdr)
    print("-" * (sum(C) + 5))

    for idx, (name, fmt, local_path, warning) in enumerate(results, start=1):
        src = local_path.name if local_path else "—"
        inc = "yes" if (local_path and local_path.exists()) else "no"
        print(
            f"{idx:<{C[0]}} "
            f"{name:<{C[1]}} "
            f"{fmt:<{C[2]}} "
            f"{src:<{C[3]}} "
            f"{inc:<{C[4]}} "
            f"{warning}"
        )

    print()


if __name__ == "__main__":
    main()
