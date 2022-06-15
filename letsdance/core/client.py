from __future__ import annotations

import logging
import typing
from urllib.parse import urljoin

import requests
from django.conf import settings

from letsdance.core.utils import date_to_header

if typing.TYPE_CHECKING:
    from letsdance.core.models import Board

logger = logging.getLogger(__name__)


def put_board(board: Board, peer_url: str) -> requests.Response:
    url = urljoin(peer_url, f"/{board.key}")
    headers = {
        "User-Agent": settings.USER_AGENT,
        "Content-Type": "text/html;charset=utf-8",
        "Spring-Version": "83",
        "If-Unmodified-Since": date_to_header(board.last_modified),
        "Authorization": f"Spring-83 Signature={board.signature}",
    }

    response = requests.put(url, data=board.content, headers=headers, timeout=5)
    return response


def get_board(key: str, peer_url: str) -> requests.Response:
    url = urljoin(peer_url, f"/{key}")
    headers = {
        "User-Agent": settings.USER_AGENT,
        "Spring-Version": "83",
    }
    response = requests.put(url, headers=headers, timeout=5)
    return response
