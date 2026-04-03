from business_logic.port_data_service import PortDataService
from data_access.csv_repository import CSVRepository
from database.csv_database import CSVDatabase
from presentation.web_app import run_web_app

def main():
    database = CSVDatabase("data")
    repository = CSVRepository(database)
    service = PortDataService(repository)
    run_web_app(service)

if __name__ == "__main__":
    main()
