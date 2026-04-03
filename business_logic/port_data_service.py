class PortDataService:
    def __init__(self, repository):
        self.repository = repository

    def _serialize_records(self, records):
        return [vars(record) for record in records]

    def get_port_summary(self):
        locations = self.repository.get_locations()
        routes = self.repository.get_routes()
        notifications = self.repository.get_notifications()
        users = self.repository.get_users()

        return {
            "locations": len(locations),
            "routes": len(routes),
            "notifications": len(notifications),
            "users": len(users),
        }

    def get_port_data(self):
        locations = self.repository.get_locations()
        routes = self.repository.get_routes()
        notifications = self.repository.get_notifications()
        users = self.repository.get_users()

        return {
            "summary": {
                "locations": len(locations),
                "routes": len(routes),
                "notifications": len(notifications),
                "users": len(users),
            },
            "locations": self._serialize_records(locations),
            "routes": self._serialize_records(routes),
            "notifications": self._serialize_records(notifications),
            "users": self._serialize_records(users),
        }
