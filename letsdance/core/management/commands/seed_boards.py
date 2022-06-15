from django.core.management.base import BaseCommand
from django.utils import timezone

from letsdance.core.crypto import dump_public_key, generate_private_key
from letsdance.core.models import Board
from letsdance.core.utils import generate_fake_board_content


class Command(BaseCommand):
    help = "Create fake boards for development/testing"

    def add_arguments(self, parser):
        parser.add_argument("--count", default=1, type=int)

    def handle(self, *args, **options):
        for _ in range(options["count"]):
            last_modified = timezone.now()
            content = generate_fake_board_content(last_modified)
            private_key = generate_private_key()
            signature = private_key.sign(content.encode()).hex()
            board = Board.objects.create(
                key=dump_public_key(private_key.public_key()),
                content=content,
                signature=signature,
                last_modified=last_modified,
            )
            self.stdout.write(f"Generated board: {board}")
