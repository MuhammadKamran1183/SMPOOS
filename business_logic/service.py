from pathlib import Path

from business_logic.port_data_service import PortDataService
from data_access.csv_repository import CSVRepository
from database.csv_database import CSVDatabase


def build_service():
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    database = CSVDatabase(data_dir)
    repository = CSVRepository(database)
    return PortDataService(repository)


service = build_service()
