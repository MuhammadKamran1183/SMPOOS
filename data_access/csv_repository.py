from model.location import Location
from model.notification import Notification
from model.route import Route
from model.user import User


class CSVRepository:
    def __init__(self, database):
        self.database = database

    def get_locations(self):
        rows = self.database.read_rows("smpoos_locations.csv")
        return [
            Location(
                row["location_id"],
                row["name"],
                row["type"],
                row["status"],
                row["capacity_tonnes"],
            )
            for row in rows
        ]

    def get_routes(self):
        rows = self.database.read_rows("smpoos_routes.csv")
        return [
            Route(
                row["route_id"],
                row["start_location"],
                row["end_location"],
                row["route_type"],
                row["distance_km"],
                row["status"],
            )
            for row in rows
        ]

    def get_notifications(self):
        rows = self.database.read_rows("smpoos_notifications.csv")
        return [
            Notification(
                row["notification_id"],
                row["alert_type"],
                row["location_id"],
                row["severity"],
                row["message"],
                row["timestamp"],
            )
            for row in rows
        ]

    def get_users(self):
        rows = self.database.read_rows("smpoos_users.csv")
        return [
            User(
                row["user_id"],
                row["name"],
                row["role"],
                row["email"],
                row["active"],
            )
            for row in rows
        ]
