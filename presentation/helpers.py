from datetime import datetime, timezone


TIME_COLUMNS = {
    "timestamp",
    "last_updated",
    "estimated_arrival",
    "estimated_departure",
    "start_time",
    "end_time",
    "created_at",
    "updated_at",
    "delivered_at",
    "eta",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def is_timestamp_column(column_name):
    normalized = str(column_name or "").strip().lower()
    if not normalized:
        return False
    if normalized in TIME_COLUMNS:
        return True
    return normalized.endswith(("_at", "_time", "_date")) or normalized.startswith(("timestamp", "date_"))


def format_timestamp_display(value):
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    return parsed.strftime("%d %b %Y, %I:%M %p")


def format_table_rows(rows, columns):
    formatted_rows = []
    for row in rows or []:
        formatted_row = dict(row)
        for column in columns:
            if is_timestamp_column(column) and column in formatted_row:
                formatted_row[column] = format_timestamp_display(formatted_row.get(column))
        formatted_rows.append(formatted_row)
    return formatted_rows


def combine_date_time(date_value, time_value):
    if not date_value and not time_value:
        return ""
    date_part = str(date_value or "").split("T")[0]
    time_part = str(time_value or "").strip()
    if not date_part:
        return ""
    if not time_part:
        time_part = "00:00"
    if len(time_part) == 5:
        time_part = time_part + ":00"
    return f"{date_part}T{time_part}+00:00"

