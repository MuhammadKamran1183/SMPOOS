import os
from pathlib import Path

from business_logic.port_data_service import PortDataService
from data_access.csv_repository import CSVRepository
from database.csv_database import CSVDatabase
from presentation.web_app import run_web_app
from security.secure_storage import SecureStorage

def main():
    data_dir = Path(__file__).resolve().parent / "data"
    database = CSVDatabase(data_dir)
    repository = CSVRepository(database)
    secure_storage = SecureStorage()
    service = PortDataService(repository, secure_storage=secure_storage)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    ssl_cert_file = os.getenv("SSL_CERT_FILE", "")
    ssl_key_file = os.getenv("SSL_KEY_FILE", "")
    run_web_app(
        service,
        host=host,
        port=port,
        ssl_cert_file=ssl_cert_file,
        ssl_key_file=ssl_key_file,
    )

if __name__ == "__main__":
    main()
