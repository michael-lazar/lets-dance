from datetime import datetime

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import http_date, parse_http_date_safe
from faker import Faker

fake = Faker()


def date_to_header(date: datetime) -> str:
    """
    Convert a datetime object into an RFC 1123 formatted date string.
    """
    return http_date(date.timestamp())


def date_from_header(header: str) -> datetime | None:
    """
    Convert an RFC 1123 date string into a native datetime object.
    """
    timestamp = parse_http_date_safe(header)
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def generate_fake_board_content(last_modified: datetime) -> str:
    content = render_to_string(
        "board.html",
        {
            "body": fake.paragraphs(),
            "last_modified": f"{last_modified:%Y-%m-%dT%H:%M:%SZ}",
        },
    )
    return content
