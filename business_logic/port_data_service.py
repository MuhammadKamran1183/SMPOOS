import hashlib
from datetime import datetime, timezone


class PortDataService:
    AUTHORISED_ROLES = {
        "administrator",
        "harbourmaster",
        "operations supervisor",
        "safety officer",
    }

    def __init__(self, repository):
        self.repository = repository

    def _serialize_records(self, records):
        return [vars(record) for record in records]

    def _serialise_user(self, user):
        return {
            "user_id": user.user_id,
            "name": user.name,
            "role": user.role,
            "email": user.email,
            "active": user.is_active(),
        }

    def _ensure_required(self, payload, required_fields):
        missing_fields = [
            field for field in required_fields if not str(payload.get(field, "")).strip()
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}."
            )

    def _normalise_status(self, status):
        return str(status).strip().title()

    def _is_location_disrupted(self, status):
        return self._normalise_status(status) in {
            "Closed",
            "Inactive",
            "Under Maintenance",
            "Hazardous",
        }

    def authenticate_user(self, email, password):
        user = self.repository.get_user_by_email(email)

        if user is None:
            raise ValueError("Invalid email or password.")

        if not user.is_active():
            raise PermissionError("Only active users can access the admin interface.")

        if user.role.strip().lower() not in self.AUTHORISED_ROLES:
            raise PermissionError("This user is not authorised for admin changes.")

        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        stored_hash = self.repository.get_password_hash(user.user_id)

        if stored_hash != password_hash:
            raise ValueError("Invalid email or password.")

        return self._serialise_user(user)

    def create_location(self, payload):
        self._ensure_required(
            payload,
            ["name", "type", "status", "capacity_tonnes"],
        )
        return self.repository.create_location(payload)

    def update_location(self, location_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_location(location_id, payload)

    def delete_location(self, location_id):
        self.repository.delete_location(location_id)

    def create_route(self, payload):
        self._ensure_required(
            payload,
            ["start_location", "end_location", "route_type", "distance_km", "status"],
        )
        return self.repository.create_route(payload)

    def update_route(self, route_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_route(route_id, payload)

    def delete_route(self, route_id):
        self.repository.delete_route(route_id)

    def create_notification(self, payload):
        self._ensure_required(
            payload,
            ["alert_type", "location_id", "severity", "message"],
        )

        payload.setdefault(
            "timestamp",
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        return self.repository.create_notification(payload)

    def update_notification(self, notification_id, payload):
        return self.repository.update_notification(notification_id, payload)

    def delete_notification(self, notification_id):
        self.repository.delete_notification(notification_id)

    def apply_operational_change(self, payload):
        self._ensure_required(
            payload,
            ["target_type", "target_id", "new_status", "message"],
        )

        target_type = payload["target_type"].strip().lower()
        target_id = payload["target_id"].strip()
        new_status = self._normalise_status(payload["new_status"])
        message = payload["message"].strip()

        if target_type not in {"location", "route"}:
            raise ValueError("target_type must be either 'location' or 'route'.")

        if target_type == "location":
            updated_target = self.repository.update_location(
                target_id,
                {"status": new_status},
            )
            impacted_routes = self._reconfigure_routes_for_location(target_id, new_status)
            berth_recommendations = self._get_available_berths(exclude_location_id=target_id)
            notification_location_id = target_id
        else:
            updated_target = self.repository.update_route(
                target_id,
                {"status": new_status},
            )
            impacted_routes = [updated_target]
            berth_recommendations = []
            notification_location_id = payload.get("location_id", "")

        notification = self.create_notification(
            {
                "alert_type": payload.get("alert_type", "Operational Change"),
                "location_id": notification_location_id,
                "severity": payload.get("severity", "High"),
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

        return {
            "updated_target": updated_target,
            "impacted_routes": impacted_routes,
            "recommended_berths": berth_recommendations,
            "notification": notification,
        }

    def _reconfigure_routes_for_location(self, location_id, new_status):
        impacted_routes = []
        routes = self.repository.get_routes()

        for route in routes:
            if location_id not in {route.start_location, route.end_location}:
                continue

            route_status = (
                "Restricted"
                if self._is_location_disrupted(new_status)
                else "Open"
            )
            impacted_routes.append(
                self.repository.update_route(route.route_id, {"status": route_status})
            )

        return impacted_routes

    def _get_available_berths(self, exclude_location_id=None):
        berth_rows = [
            vars(location)
            for location in self.repository.get_locations()
            if location.type.strip().lower() == "berth"
            and location.is_active()
            and location.location_id != exclude_location_id
        ]

        berth_rows.sort(
            key=lambda berth: int(berth["capacity_tonnes"]),
            reverse=True,
        )
        return berth_rows[:5]
