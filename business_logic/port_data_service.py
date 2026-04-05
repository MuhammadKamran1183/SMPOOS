import hashlib
from datetime import datetime, timezone


class PortDataService:
    AUTHORISED_ROLES = {
        "administrator",
        "harbourmaster",
        "operations supervisor",
        "safety officer",
    }
    DISRUPTED_LOCATION_STATUSES = {"Closed", "Inactive", "Under Maintenance", "Hazardous"}
    ACTIVE_OUTAGE_STATUSES = {"Active", "Out", "Unavailable"}
    ACTIVE_RESTRICTION_STATUSES = {"Active", "Restricted", "Closed"}

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
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}.")

    def _normalise_status(self, status):
        return str(status).strip().title()

    def _now_iso(self):
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _is_disrupted_location_status(self, status):
        return self._normalise_status(status) in self.DISRUPTED_LOCATION_STATUSES

    def authenticate_user(self, email, password):
        user = self.repository.get_user_by_email(email)
        if user is None:
            raise ValueError("Invalid email or password.")
        if not user.is_active():
            raise PermissionError("Only active users can access the admin interface.")
        if user.role.strip().lower() not in self.AUTHORISED_ROLES:
            raise PermissionError("This user is not authorised for admin changes.")

        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if self.repository.get_password_hash(user.user_id) != password_hash:
            raise ValueError("Invalid email or password.")
        return self._serialise_user(user)

    def create_location(self, payload):
        self._ensure_required(payload, ["name", "type", "status", "capacity_tonnes"])
        payload["status"] = self._normalise_status(payload["status"])
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
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_route(payload)

    def update_route(self, route_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_route(route_id, payload)

    def delete_route(self, route_id):
        self.repository.delete_route(route_id)

    def create_notification(self, payload):
        self._ensure_required(payload, ["alert_type", "location_id", "severity", "message"])
        payload.setdefault("timestamp", self._now_iso())
        return self.repository.create_notification(payload)

    def update_notification(self, notification_id, payload):
        return self.repository.update_notification(notification_id, payload)

    def delete_notification(self, notification_id):
        self.repository.delete_notification(notification_id)

    def create_vessel_path(self, payload):
        self._ensure_required(
            payload,
            [
                "vessel_name",
                "vessel_type",
                "cargo_tonnes",
                "current_location_id",
                "destination_location_id",
                "status",
            ],
        )
        payload.setdefault("last_updated", self._now_iso())
        return self.repository.create_vessel_path(payload)

    def update_vessel_path(self, path_id, payload):
        payload["last_updated"] = self._now_iso()
        return self.repository.update_vessel_path(path_id, payload)

    def delete_vessel_path(self, path_id):
        self.repository.delete_vessel_path(path_id)

    def create_restricted_area(self, payload):
        self._ensure_required(
            payload,
            ["name", "location_id", "area_type", "status", "severity", "reason"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_restricted_area(payload)

    def update_restricted_area(self, area_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_restricted_area(area_id, payload)

    def delete_restricted_area(self, area_id):
        self.repository.delete_restricted_area(area_id)

    def create_crane_outage(self, payload):
        self._ensure_required(
            payload,
            ["crane_id", "location_id", "status", "severity", "reason"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_crane_outage(payload)

    def update_crane_outage(self, outage_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_crane_outage(outage_id, payload)

    def delete_crane_outage(self, outage_id):
        self.repository.delete_crane_outage(outage_id)

    def create_berth_allocation(self, payload):
        self._ensure_required(
            payload,
            ["vessel_name", "cargo_tonnes", "eta", "status", "priority"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_berth_allocation(payload)

    def update_berth_allocation(self, allocation_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_berth_allocation(allocation_id, payload)

    def delete_berth_allocation(self, allocation_id):
        self.repository.delete_berth_allocation(allocation_id)

    def recalculate_operations(self):
        impacted_routes = self._recalculate_route_statuses()
        berth_allocations = self._recalculate_berth_allocations()
        vessel_paths = self._recalculate_vessel_paths()
        return {
            "impacted_routes": impacted_routes,
            "berth_allocations": berth_allocations,
            "vessel_paths": vessel_paths,
            "blocked_locations": sorted(self._get_blocked_location_ids()),
        }

    def apply_operational_change(self, payload):
        self._ensure_required(payload, ["target_type", "target_id", "new_status", "message"])
        target_type = payload["target_type"].strip().lower()
        target_id = payload["target_id"].strip()
        new_status = self._normalise_status(payload["new_status"])
        message = payload["message"].strip()

        handlers = {
            "location": self.update_location,
            "route": self.update_route,
            "restricted_area": self.update_restricted_area,
            "crane_outage": self.update_crane_outage,
            "vessel_path": self.update_vessel_path,
            "berth_allocation": self.update_berth_allocation,
        }
        if target_type not in handlers:
            raise ValueError(
                "target_type must be one of: location, route, restricted_area, crane_outage, vessel_path, berth_allocation."
            )

        updated_target = handlers[target_type](target_id, {"status": new_status})
        recalculation = self.recalculate_operations()
        notification = self.create_notification(
            {
                "alert_type": payload.get("alert_type", "Operational Change"),
                "location_id": payload.get("location_id", payload.get("target_id", "")),
                "severity": payload.get("severity", "High"),
                "message": message,
                "timestamp": self._now_iso(),
            }
        )

        return {
            "updated_target": updated_target,
            "recalculation": recalculation,
            "notification": notification,
        }

    def _get_blocked_location_ids(self):
        blocked_locations = {
            location.location_id
            for location in self.repository.get_locations()
            if self._is_disrupted_location_status(location.status)
        }
        blocked_locations.update(
            area.location_id
            for area in self.repository.get_restricted_areas()
            if area.status.strip().title() in self.ACTIVE_RESTRICTION_STATUSES
        )
        blocked_locations.update(
            outage.location_id
            for outage in self.repository.get_crane_outages()
            if outage.status.strip().title() in self.ACTIVE_OUTAGE_STATUSES
        )
        return blocked_locations

    def _recalculate_route_statuses(self):
        blocked_locations = self._get_blocked_location_ids()
        impacted_routes = []
        for route in self.repository.get_routes():
            should_restrict = route.start_location in blocked_locations or route.end_location in blocked_locations
            next_status = "Restricted" if should_restrict else "Open"
            if route.status != next_status:
                impacted_routes.append(
                    self.repository.update_route(route.route_id, {"status": next_status})
                )
        return impacted_routes

    def _get_available_berths(self, exclude_location_id=None):
        blocked_locations = self._get_blocked_location_ids()
        available_berths = []
        for location in self.repository.get_locations():
            location_type = location.type.strip().lower()
            if "berth" not in location_type and "dock" not in location_type:
                continue
            if not location.is_active():
                continue
            if location.location_id == exclude_location_id:
                continue
            if location.location_id in blocked_locations:
                continue
            available_berths.append(vars(location))

        available_berths.sort(key=lambda berth: int(berth["capacity_tonnes"]), reverse=True)
        return available_berths

    def _recalculate_berth_allocations(self):
        available_berths = self._get_available_berths()
        allocations = []
        for allocation in self.repository.get_berth_allocations():
            if not allocation.is_open_for_recalculation():
                continue

            preferred_berth = allocation.berth_id
            available_berth_ids = {berth["location_id"] for berth in available_berths}
            target_berth = preferred_berth if preferred_berth in available_berth_ids else ""

            if not target_berth:
                cargo_tonnes = int(float(allocation.cargo_tonnes or 0))
                target_berth = self._find_best_berth_for_cargo(available_berths, cargo_tonnes)

            if target_berth:
                updated = self.repository.update_berth_allocation(
                    allocation.allocation_id,
                    {"berth_id": target_berth, "status": "Scheduled"},
                )
            else:
                updated = self.repository.update_berth_allocation(
                    allocation.allocation_id,
                    {"status": "Waiting"},
                )
            allocations.append(updated)
        return allocations

    def _find_best_berth_for_cargo(self, available_berths, cargo_tonnes):
        suitable_berths = [
            berth
            for berth in available_berths
            if int(berth["capacity_tonnes"]) >= cargo_tonnes
        ]
        if suitable_berths:
            suitable_berths.sort(key=lambda berth: int(berth["capacity_tonnes"]))
            return suitable_berths[0]["location_id"]
        return available_berths[0]["location_id"] if available_berths else ""

    def _recalculate_vessel_paths(self):
        blocked_locations = self._get_blocked_location_ids()
        open_routes = [route for route in self.repository.get_routes() if route.is_open()]
        berth_allocations = {
            allocation.vessel_name: allocation
            for allocation in self.repository.get_berth_allocations()
        }
        updated_paths = []

        for path in self.repository.get_vessel_paths():
            payload = {"last_updated": self._now_iso()}
            destination_blocked = path.destination_location_id in blocked_locations

            if path.current_location_id in blocked_locations or destination_blocked:
                payload["status"] = "Holding"

            matching_route = next(
                (
                    route
                    for route in open_routes
                    if route.end_location == path.destination_location_id
                ),
                open_routes[0] if open_routes else None,
            )
            if matching_route is not None:
                payload["assigned_route_id"] = matching_route.route_id
                if payload.get("status") != "Holding":
                    payload["status"] = "Rerouted"

            allocation = berth_allocations.get(path.vessel_name)
            if allocation and allocation.berth_id:
                payload["assigned_berth_id"] = allocation.berth_id

            updated_paths.append(self.repository.update_vessel_path(path.path_id, payload))
        return updated_paths
