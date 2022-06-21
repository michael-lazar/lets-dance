import argparse

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from requests.exceptions import ConnectionError

from letsdance.core.client import put_board
from letsdance.core.constants import BOARD_MAX_SIZE_BYTES
from letsdance.core.crypto import load_private_key
from letsdance.core.models import Board


class Command(BaseCommand):
    help = "Upload a board to a Spring '83 server."

    def add_arguments(self, parser):
        parser.add_argument(
            "--public-key",
            required=True,
            help="Your public key, formatted as a hex string.",
        )
        parser.add_argument(
            "--private-key",
            required=True,
            help="Your private key, formatted as a hex string.",
        )
        parser.add_argument(
            "--server-url",
            required=True,
            help="URL of the server to upload to.",
        )
        parser.add_argument(
            "--content-file",
            required=True,
            type=argparse.FileType("r"),
            help="A text file containing your board HTML, use '-' to pipe from stdin.",
        )

    def handle(self, *args, **options):
        last_modified = timezone.now()
        key = options["public_key"]
        url = options["server_url"]

        content = options["content_file"].read()
        content = f'<time datetime="{last_modified:%Y-%m-%dT%H:%M:%SZ}">\n' + content
        encoded_content = content.encode()
        if len(encoded_content) > BOARD_MAX_SIZE_BYTES:
            raise CommandError(f"Board exceeds maximum size of {BOARD_MAX_SIZE_BYTES} bytes.")

        private_key = load_private_key(options["private_key"])
        signature = private_key.sign(encoded_content).hex()

        board = Board(
            key=key,
            content=content,
            signature=signature,
            last_modified=last_modified,
        )
        self.stdout.write(f"Uploading board to {url}")
        self.stdout.write(content)
        try:
            response = put_board(board, url)
        except ConnectionError as e:
            self.stdout.write(str(e))
        else:
            self.stdout.write(f"Server response: {response.status_code}")
