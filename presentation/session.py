from dash import dcc
from flask import session

from business_logic.service import service


def current_user():
    return session.get("user")


def user_permissions(user=None):
    user = user or current_user() or {}
    permissions = user.get("permissions") or []
    if permissions:
        return set(permissions)
    return set(service._permissions_for_role(user.get("canonical_role", user.get("role", ""))))


def first_allowed_path(user=None):
    perms = user_permissions(user)
    ordered = [
        ("/dashboard", "view_management_dashboard"),
        ("/monitoring", "view_monitoring"),
        ("/admin", "view_admin_portal"),
        ("/notification-engine", "view_notification_engine"),
        ("/analytics", "view_analytics"),
    ]
    for path, perm in ordered:
        if perm in perms:
            return path
    if user or current_user():
        return "/no-access"
    return "/login"


def guard_requires_login(pathname):
    if pathname in {"/", "/login"}:
        return None
    if not current_user():
        return dcc.Location(pathname="/login", id="redirect-login")
    return None

