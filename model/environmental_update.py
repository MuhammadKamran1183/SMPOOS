class EnvironmentalUpdate:
    def __init__(
        self,
        update_id,
        zone_name,
        wind_speed_knots,
        tide_level_m,
        visibility_km,
        condition_status,
        recorded_at,
    ):
        self.update_id = update_id
        self.zone_name = zone_name
        self.wind_speed_knots = wind_speed_knots
        self.tide_level_m = tide_level_m
        self.visibility_km = visibility_km
        self.condition_status = condition_status
        self.recorded_at = recorded_at
