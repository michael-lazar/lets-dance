from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from apscheduler.jobstores.base import ConflictingIdError
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from parsel import Selector

from letsdance.core.constants import BOARD_MAX_SIZE_BYTES, TEST_KEY_PUBLIC
from letsdance.core.crypto import validate_public_key, verify_signature
from letsdance.core.exceptions import Spring83Exception
from letsdance.core.models import Board
from letsdance.core.tasks import broadcast_board, scheduler
from letsdance.core.utils import date_from_header

logger = logging.getLogger(__name__)


def catch_spring83_exceptions(func: Callable):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Spring83Exception as e:
            logger.info(f"Spring 83 error: {e}")
            response = HttpResponse(str(e), status=e.status)
            response.headers["Spring-Version"] = "83"
            return response

    return inner


class IndexView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Retrieve the current difficulty.
        """
        context = {"boards": Board.objects.all().order_by("?")[:500]}
        content = render_to_string("newsstand.html", context, request)

        response = HttpResponse(content)
        response.headers["Spring-Version"] = "83"
        response.headers["Spring-Difficulty"] = "0"
        return response


class BoardView(View):
    @catch_spring83_exceptions
    def get(self, request: HttpRequest, key: str) -> HttpResponse:
        """
        Retrieve a board from the server.
        """
        board: Board | None

        if key == TEST_KEY_PUBLIC:
            board = Board.generate_board()
        else:
            board = Board.objects.get_or_none(key=key)
            if board is None:
                raise Spring83Exception("No board for this key found on this server.", status=404)

        if "If-Modified-Since" in request.headers:
            if_modified_since = date_from_header(request.headers["If-Modified-Since"])
            if if_modified_since and if_modified_since > board.last_modified:
                raise Spring83Exception(
                    "Board requested is newer than server's timestamp.", status=304
                )

        response = HttpResponse(board.content)
        response.headers["Spring-Version"] = "83"
        response.headers["Authorization"] = f"Spring-83 Signature={board.signature}"
        return response

    @catch_spring83_exceptions
    def put(self, request: HttpRequest, key: str) -> HttpResponse:
        """
        Create or replace a board on the server.
        """
        content = self.validate_content(request)
        self.validate_public_key(key)
        signature = self.validate_signature(request, key)

        existing_board = Board.objects.get_or_none(key=key)
        self.validate_last_modified_header(request, existing_board)
        last_modified = self.validate_last_modified_meta(content, existing_board)

        board, created = Board.objects.update_or_create(
            key=key,
            defaults={
                "content": content,
                "signature": signature,
                "last_modified": last_modified,
            },
        )
        if created:
            message = "Board was successfully created."
        else:
            message = "Board was successfully updated."

        eta = 300
        job_id = f"broadcast:{board.key}"
        try:
            scheduler.add_job(
                broadcast_board,
                id=job_id,
                args=[board.key],
                trigger="date",
                run_date=timezone.now() + timedelta(seconds=eta),
                replace_existing=False,
            )
        except ConflictingIdError:
            # Job is already scheduled in the queue, don't replace it
            pass
        else:
            logger.info(f"Scheduled job {job_id} with eta {eta}s.")

        response = HttpResponse(message)
        response.headers["Spring-Version"] = "83"
        response.headers["Authorization"] = f"Spring-83 Signature={board.signature}"
        return response

    def validate_content(self, request: HttpRequest) -> str:
        """
        Validate the board content matches the data constraints.
        """
        if len(request.body) > BOARD_MAX_SIZE_BYTES:
            raise Spring83Exception(
                f"Board is larger than {BOARD_MAX_SIZE_BYTES} bytes.", status=413
            )

        return request.body.decode()

    def validate_public_key(self, key: str) -> str:
        """
        Validate that the public key hex is an allowed value.
        """
        if key == TEST_KEY_PUBLIC:
            raise Spring83Exception("Cannot PUT board with test key value.", status=401)

        if not validate_public_key(key):
            raise Spring83Exception("Key does not end with a valid suffix.", status=400)

        return key

    def validate_signature(self, request: HttpRequest, key: str) -> str:
        """
        Validate that the authorization header and signature is correct.
        """
        if "Authorization" not in request.headers:
            raise Spring83Exception("Missing authorization header.", status=401)

        authorization = request.headers["Authorization"]
        if not authorization.startswith("Spring-83 Signature="):
            raise Spring83Exception("Invalid authorization format.", status=401)

        signature = authorization.removeprefix("Spring-83 Signature=")
        if not verify_signature(signature, key, request.body):
            raise Spring83Exception("Board was submitted without a valid signature.", status=401)

        return signature

    def validate_last_modified_header(self, request: HttpRequest, board: Board | None) -> None:
        """
        Validate the Unmodified-Since header from the HTTP request.
        """
        if board:
            unmodified_since = date_from_header(request.headers["If-Unmodified-Since"])
            if unmodified_since and unmodified_since <= board.last_modified:
                raise Spring83Exception(
                    "Board was submitted with a timestamp older than the server's timestamp.",
                    status=409,
                )

    def validate_last_modified_meta(self, content: str, board: Board | None) -> datetime:
        """
        Validate the last-modified date from a <time> tag in the board HTML.
        """
        selector = Selector(content)
        tags = selector.css("time")
        if not tags:
            raise Spring83Exception("Board is missing last-modified <time> tag.", status=400)

        if len(tags) > 1:
            raise Spring83Exception(
                "Board contains more than one last-modified <time> tag", status=400
            )

        tag = tags[0]

        last_modified_str = tag.attrib.get("datetime", None)
        if last_modified_str is None:
            raise Spring83Exception(
                "Unable to parse date from last-modified <time> tag.", status=400
            )

        last_modified = datetime.strptime(last_modified_str, "%Y-%m-%dT%H:%M:%SZ")
        last_modified = last_modified.replace(tzinfo=timezone.utc)

        if last_modified > timezone.now():
            raise Spring83Exception(
                "Board was submitted with a timestamp in the future.", status=400
            )

        if board and last_modified <= board.last_modified:
            raise Spring83Exception(
                "Board was submitted with a timestamp older than the server's timestamp.",
                status=409,
            )

        return last_modified
