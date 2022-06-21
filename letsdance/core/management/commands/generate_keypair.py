import time

from django.core.management.base import BaseCommand

from letsdance.core.crypto import (
    dump_private_key,
    dump_public_key,
    generate_private_key,
    validate_public_key,
)


class Command(BaseCommand):
    help = "Generate a new, valid Spring '83 keypair."

    def handle(self, *args, **options):
        self.stderr.write("Generating a valid ed25519 key, this may take a while...")

        start = time.time()
        i = 0
        while True:
            if not i % 5000:
                self.stderr.write(f"Iteration {i}...")
            private_key = generate_private_key()
            public_key = private_key.public_key()
            public_key_hex = dump_public_key(public_key)
            if validate_public_key(public_key_hex):
                break
            i += 1

        private_key_hex = dump_private_key(private_key)
        delta = int(time.time() - start)

        self.stdout.write(f"Generated keypair in {delta}s:")
        self.stdout.write(f"Public : {public_key_hex}")
        self.stdout.write(f"Secret : {private_key_hex}")
