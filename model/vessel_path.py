class VesselPath:
    def __init__(
        self,
        path_id,
        vessel_name,
        vessel_type,
        cargo_tonnes,
        current_location_id,
        destination_location_id,
        assigned_route_id,
        assigned_berth_id,
        status,
        last_updated,
    ):
        self.path_id = path_id
        self.vessel_name = vessel_name
        self.vessel_type = vessel_type
        self.cargo_tonnes = cargo_tonnes
        self.current_location_id = current_location_id
        self.destination_location_id = destination_location_id
        self.assigned_route_id = assigned_route_id
        self.assigned_berth_id = assigned_berth_id
        self.status = status
        self.last_updated = last_updated

    def is_active(self):
        return self.status.lower() in {"active", "rerouted", "approaching"}
