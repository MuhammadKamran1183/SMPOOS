class Location:
    def __init__(self, location_id, name, type, status, capacity_tonnes):
        self.location_id = location_id
        self.name = name
        self.type = type
        self.status = status
        self.capacity_tonnes = capacity_tonnes

    def is_active(self):
        return self.status.lower() == "active"

    def __str__(self):
        return f"{self.name} ({self.type})"