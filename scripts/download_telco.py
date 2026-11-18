"""Retrieve the immutable IBM sample. Raw data is not committed to our repository."""

from pathlib import Path
from urllib.request import urlopen
import hashlib, json

REV = "d5371f5d83a446ad5673cbcca3b814b926491f8a"
URL = f"https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/{REV}/data/Telco-Customer-Churn.csv"


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / "projects/churniq/data"
    out.mkdir(parents=True, exist_ok=True)
    data = urlopen(URL, timeout=60).read()
    (out / "raw.csv").write_bytes(data)
    license = urlopen(
        f"https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/{REV}/LICENSE",
        timeout=60,
    ).read()
    (out / "IBM_LICENSE.txt").write_bytes(license)
    manifest = {
        "url": URL,
        "revision": REV,
        "sha256": hashlib.sha256(data).hexdigest(),
        "access_date": "2026-11-17",
        "data_class": "IBM fictional telecom sample; not live customers",
        "license": "Repository Apache-2.0; retain IBM attribution; raw CSV excluded from Git",
    }
    (out / "source.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
