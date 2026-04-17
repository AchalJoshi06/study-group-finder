def split_csv_field(value: str):
    """Convert comma-separated user input into a normalized list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_text(value: str):
    return (value or "").strip()
