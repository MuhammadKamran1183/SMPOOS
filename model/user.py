class User:
    def __init__(self, user_id, name, role, email, active):
        self.user_id = user_id
        self.name = name
        self.role = role
        self.email = email
        self.active = active

    def is_active(self):
        return str(self.active).lower() in ["yes", "true"]

    def is_admin(self):
        return self.role.lower() == "administrator"

    def __str__(self):
        return f"{self.name} ({self.role})"