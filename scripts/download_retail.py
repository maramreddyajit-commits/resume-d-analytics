from pathlib import Path
from urllib.request import urlopen
import zipfile, io, hashlib, json

URL = "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / "projects/marketscope/data"
    folder.mkdir(parents=True, exist_ok=True)
    blob = urlopen(URL, timeout=180).read()
    z = zipfile.ZipFile(io.BytesIO(blob))
    name = next(n for n in z.namelist() if n.endswith(".xlsx"))
    data = z.read(name)
    (folder / "retail.xlsx").write_bytes(data)
    m = {
        "url": URL,
        "access_date": "2026-11-17",
        "sha256_zip": hashlib.sha256(blob).hexdigest(),
        "sha256_xlsx": hashlib.sha256(data).hexdigest(),
        "citation": "Chen, D. (2012). Online Retail II. UCI. DOI 10.24432/C5CG6D",
        "license": "CC BY 4.0",
        "data_class": "Historical UK retailer transactions, 2009–2011; GBP",
    }
    (folder / "source.json").write_text(json.dumps(m, indent=2))
    print(json.dumps(m))


if __name__ == "__main__":
    main()
