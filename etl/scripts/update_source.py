# coding: utf8

"""
Download World Bank Education Statistics data from DataBank.
"""

import os
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

SOURCE_URL = "https://databank.worldbank.org/data/download/EdStats_CSV.zip"
SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR.parent / "source"


def download_and_extract():
    """Download the EdStats CSV zip file and extract to source directory."""
    zip_path = SOURCE_DIR / "EdStats_CSV.zip"

    print(f"Downloading from {SOURCE_URL}...")
    urlretrieve(SOURCE_URL, zip_path)
    print(f"Downloaded to {zip_path}")

    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(SOURCE_DIR)
    print(f"Extracted to {SOURCE_DIR}")

    # List extracted files
    print("\nExtracted files:")
    for f in SOURCE_DIR.iterdir():
        if f.name != ".gitignore":
            print(f"  {f.name}")


if __name__ == "__main__":
    os.makedirs(SOURCE_DIR, exist_ok=True)
    download_and_extract()
