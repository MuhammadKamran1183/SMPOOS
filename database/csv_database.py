import csv
from pathlib import Path


class CSVDatabase:
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)

    def read_rows(self, filename):
        file_path = self.data_folder / filename

        with file_path.open(newline="", encoding="utf-8") as csv_file:
            return list(csv.DictReader(csv_file))
