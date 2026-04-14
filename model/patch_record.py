class PatchRecord:
    def __init__(
        self,
        patch_id,
        component_name,
        patch_version,
        patch_status,
        patch_window,
        applied_at,
        notes,
    ):
        self.patch_id = patch_id
        self.component_name = component_name
        self.patch_version = patch_version
        self.patch_status = patch_status
        self.patch_window = patch_window
        self.applied_at = applied_at
        self.notes = notes
