from model.location import Location
from model.notification import Notification
from model.route import Route
from model.user import User


class CSVRepository:
    LOCATION_FILE = "smpoos_locations.csv"
    ROUTE_FILE = "smpoos_routes.csv"
    NOTIFICATION_FILE = "smpoos_notifications.csv"
    USER_FILE = "smpoos_users.csv"
    CREDENTIAL_FILE = "smpoos_credentials.csv"

    LOCATION_FIELDS = [
        "location_id",
        "name",
        "type",
        "status",
        "capacity_tonnes",
    ]
    ROUTE_FIELDS = [
        "route_id",
        "start_location",
        "end_location",
        "route_type",
        "distance_km",
        "status",
    ]
    NOTIFICATION_FIELDS = [
        "notification_id",
        "alert_type",
        "location_id",
        "severity",
        "message",
        "timestamp",
    ]
    CREDENTIAL_FIELDS = [
        "user_id",
        "password_hash",
    ]

    def __init__(self, database):
        self.database = database

    def get_locations(self):
        rows = self.database.read_rows(self.LOCATION_FILE)
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
        rows = self.database.read_rows(self.ROUTE_FILE)
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
        rows = self.database.read_rows(self.NOTIFICATION_FILE)
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
        rows = self.database.read_rows(self.USER_FILE)
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

    def get_user_by_email(self, email):
        email = email.strip().lower()
        return next(
            (user for user in self.get_users() if user.email.strip().lower() == email),
            None,
        )

    def get_credentials(self):
        return self.database.read_rows(self.CREDENTIAL_FILE)

    def get_password_hash(self, user_id):
        credentials = self.get_credentials()
        credential = next(
            (row for row in credentials if row["user_id"] == user_id),
            None,
        )
        return credential["password_hash"] if credential else None

    def create_location(self, payload):
        rows = self.database.read_rows(self.LOCATION_FILE)
        location_id = payload.get("location_id") or self._next_id(rows, "location_id", "L")

        if self._find_row(rows, "location_id", location_id):
            raise ValueError(f"Location {location_id} already exists.")

        row = self._normalise_row(self.LOCATION_FIELDS, {**payload, "location_id": location_id})
        rows.append(row)
        self.database.write_rows(self.LOCATION_FILE, self.LOCATION_FIELDS, rows)
        return row

    def update_location(self, location_id, payload):
        rows = self.database.read_rows(self.LOCATION_FILE)
        row = self._find_row(rows, "location_id", location_id)

        if row is None:
            raise ValueError(f"Location {location_id} was not found.")

        row.update(self._normalise_partial(payload))
        self.database.write_rows(self.LOCATION_FILE, self.LOCATION_FIELDS, rows)
        return row

    def delete_location(self, location_id):
        rows = self.database.read_rows(self.LOCATION_FILE)
        filtered_rows = [row for row in rows if row["location_id"] != location_id]

        if len(filtered_rows) == len(rows):
            raise ValueError(f"Location {location_id} was not found.")

        self.database.write_rows(self.LOCATION_FILE, self.LOCATION_FIELDS, filtered_rows)

    def create_route(self, payload):
        rows = self.database.read_rows(self.ROUTE_FILE)
        route_id = payload.get("route_id") or self._next_id(rows, "route_id", "R")

        if self._find_row(rows, "route_id", route_id):
            raise ValueError(f"Route {route_id} already exists.")

        row = self._normalise_row(self.ROUTE_FIELDS, {**payload, "route_id": route_id})
        rows.append(row)
        self.database.write_rows(self.ROUTE_FILE, self.ROUTE_FIELDS, rows)
        return row

    def update_route(self, route_id, payload):
        rows = self.database.read_rows(self.ROUTE_FILE)
        row = self._find_row(rows, "route_id", route_id)

        if row is None:
            raise ValueError(f"Route {route_id} was not found.")

        row.update(self._normalise_partial(payload))
        self.database.write_rows(self.ROUTE_FILE, self.ROUTE_FIELDS, rows)
        return row

    def delete_route(self, route_id):
        rows = self.database.read_rows(self.ROUTE_FILE)
        filtered_rows = [row for row in rows if row["route_id"] != route_id]

        if len(filtered_rows) == len(rows):
            raise ValueError(f"Route {route_id} was not found.")

        self.database.write_rows(self.ROUTE_FILE, self.ROUTE_FIELDS, filtered_rows)

    def create_notification(self, payload):
        rows = self.database.read_rows(self.NOTIFICATION_FILE)
        notification_id = payload.get("notification_id") or self._next_id(
            rows,
            "notification_id",
            "N",
        )

        if self._find_row(rows, "notification_id", notification_id):
            raise ValueError(f"Notification {notification_id} already exists.")

        row = self._normalise_row(
            self.NOTIFICATION_FIELDS,
            {**payload, "notification_id": notification_id},
        )
        rows.append(row)
        self.database.write_rows(
            self.NOTIFICATION_FILE,
            self.NOTIFICATION_FIELDS,
            rows,
        )
        return row

    def update_notification(self, notification_id, payload):
        rows = self.database.read_rows(self.NOTIFICATION_FILE)
        row = self._find_row(rows, "notification_id", notification_id)

        if row is None:
            raise ValueError(f"Notification {notification_id} was not found.")

        row.update(self._normalise_partial(payload))
        self.database.write_rows(
            self.NOTIFICATION_FILE,
            self.NOTIFICATION_FIELDS,
            rows,
        )
        return row

    def delete_notification(self, notification_id):
        rows = self.database.read_rows(self.NOTIFICATION_FILE)
        filtered_rows = [
            row for row in rows if row["notification_id"] != notification_id
        ]

        if len(filtered_rows) == len(rows):
            raise ValueError(f"Notification {notification_id} was not found.")

        self.database.write_rows(
            self.NOTIFICATION_FILE,
            self.NOTIFICATION_FIELDS,
            filtered_rows,
        )

    def _find_row(self, rows, key, value):
        return next((row for row in rows if row[key] == value), None)

    def _next_id(self, rows, key, prefix):
        max_value = 0

        for row in rows:
            raw_value = row.get(key, "")
            if raw_value.startswith(prefix):
                suffix = raw_value[len(prefix) :]
                if suffix.isdigit():
                    max_value = max(max_value, int(suffix))

        return f"{prefix}{max_value + 1:04d}"

    def _normalise_row(self, fieldnames, payload):
        return {
            field: str(payload.get(field, "")).strip()
            for field in fieldnames
        }

    def _normalise_partial(self, payload):
        return {
            key: str(value).strip()
            for key, value in payload.items()
            if value is not None
        }
