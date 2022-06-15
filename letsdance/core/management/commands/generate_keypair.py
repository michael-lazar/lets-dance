import time

from django.core.management.base import BaseCommand

from letsdance.core.crypto import (
    dump_private_key,
    dump_public_key,
    generate_private_key,
    get_valid_public_key_endings,
)


class Command(BaseCommand):
    help = "Generate a new, valid Spring '83 keypair."

    def handle(self, *args, **options):
        valid_endings = get_valid_public_key_endings()
        self.stderr.write(f"Finding an ed25519 key ending with: {valid_endings}")

        start = time.time()
        i = 0
        while True:
            if not i % 5000:
                self.stderr.write(f"Iteration {i}...")
            private_key = generate_private_key()
            public_key = private_key.public_key()
            public_key_hex = dump_public_key(public_key)
            if public_key_hex.endswith(valid_endings):
                break
            i += 1

        private_key_hex = dump_private_key(private_key)
        delta = int(time.time() - start)

        self.stdout.write(f"Generated keypair in {delta}s:")
        self.stdout.write(f"Public : {public_key_hex}")
        self.stdout.write(f"Secret : {private_key_hex}")
