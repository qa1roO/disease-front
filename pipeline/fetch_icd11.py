"""Stage 1: download the ICD-11 MMS simple tabulation and the ICD-10 mapping tables into data/raw/icd11/."""
import io
import urllib.request
import zipfile

from pipeline import icd11

# zip name -> folder it is extracted into
DOWNLOADS = {"SimpleTabulation-ICD-11-MMS-en.zip": "tab", "mapping.zip": "map"}


def fetch(raw_dir):
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, folder in DOWNLOADS.items():
        url = icd11.RELEASE_URL + name
        print(f"  downloading {url}")
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = response.read()
        (raw_dir / name).write_bytes(payload)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for member in archive.infolist():
                # Flatten: keep only plain file names, so nothing can land outside the target folder.
                filename = member.filename.replace("\\", "/").rsplit("/", 1)[-1]
                if member.is_dir() or not filename:
                    continue
                target = raw_dir / folder / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
