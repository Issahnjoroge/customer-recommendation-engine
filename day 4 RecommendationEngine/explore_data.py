import csv
from pathlib import Path

file_path = Path("data") / "purchases.csv"

with file_path.open("r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row)