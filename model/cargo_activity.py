class CargoActivity:
    def __init__(
        self,
        activity_id,
        vessel_name,
        berth_id,
        cargo_type,
        operation_type,
        tonnes_processed,
        status,
        last_updated,
    ):
        self.activity_id = activity_id
        self.vessel_name = vessel_name
        self.berth_id = berth_id
        self.cargo_type = cargo_type
        self.operation_type = operation_type
        self.tonnes_processed = tonnes_processed
        self.status = status
        self.last_updated = last_updated
