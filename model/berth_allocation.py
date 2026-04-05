class BerthAllocation:
    def __init__(
        self,
        allocation_id,
        vessel_name,
        cargo_tonnes,
        berth_id,
        eta,
        status,
        priority,
        notes,
    ):
        self.allocation_id = allocation_id
        self.vessel_name = vessel_name
        self.cargo_tonnes = cargo_tonnes
        self.berth_id = berth_id
        self.eta = eta
        self.status = status
        self.priority = priority
        self.notes = notes

    def is_open_for_recalculation(self):
        return self.status.lower() in {"pending", "scheduled", "reassign"}
