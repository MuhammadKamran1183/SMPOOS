import os
from pathlib import Path

from business_logic.port_data_service import PortDataService
from data_access.csv_repository import CSVRepository
from database.csv_database import CSVDatabase
from presentation.web_app import run_web_app

def main():
    data_dir = Path(__file__).resolve().parent / "data"
    database = CSVDatabase(data_dir)
    repository = CSVRepository(database)
    service = PortDataService(repository)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    run_web_app(service, host=host, port=port)

if __name__ == "__main__":
    main()
