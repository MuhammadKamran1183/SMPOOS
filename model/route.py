class Route:
    def __init__(self, route_id, start_location, end_location, route_type, distance_km, status):
        self.route_id = route_id
        self.start_location = start_location
        self.end_location = end_location
        self.route_type = route_type
        self.distance_km = distance_km
        self.status = status

    def is_open(self):
        return self.status.lower() == "open"

    def __str__(self):
        return f"{self.start_location} → {self.end_location}"