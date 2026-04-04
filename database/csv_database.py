import csv
import tempfile
from pathlib import Path


class CSVDatabase:
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)

    def read_rows(self, filename):
        file_path = self.data_folder / filename

        with file_path.open(newline="", encoding="utf-8") as csv_file:
            return list(csv.DictReader(csv_file))

    def write_rows(self, filename, fieldnames, rows):
        file_path = self.data_folder / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            dir=file_path.parent,
            delete=False,
        ) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            temp_path = Path(temp_file.name)

        temp_path.replace(file_path)
