from pathlib import Path

path = Path("src/data/sales_data_sample.csv")
data = path.read_bytes()

print(f"File size: {len(data):,} bytes")

encodings = [
    "utf-8",
    "utf-8-sig",
    "cp1252",
    "latin-1",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
]

for encoding in encodings:
    try:
        text = data.decode(encoding)
        print(f"✓ {encoding}: valid ({len(text):,} characters)")
    except UnicodeDecodeError as e:
        print(f"✗ {encoding}: {e}")
