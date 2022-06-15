from __future__ import annotations

import logging

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from letsdance.core.constants import BOARD_MAX_COUNT, TEST_KEY_PUBLIC, TEST_KEY_SECRET
from letsdance.core.crypto import load_private_key
from letsdance.core.utils import generate_fake_board_content

logger = logging.getLogger(__name__)


class BoardManager(models.Manager):
    def get_or_none(self, **kwargs) -> Board | None:
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class Board(models.Model):

    key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        validators=[RegexValidator(f"[0-9a-f]{64}")],
    )
    content = models.TextField()
    signature = models.CharField(
        max_length=128,
        validators=[RegexValidator(f"[0-9a-f]{128}")],
    )
    last_modified = models.DateTimeField(default=timezone.now)

    objects = BoardManager()

    def __str__(self):
        return self.key

    @classmethod
    def get_difficulty_factor(cls) -> float:
        num_boards_stored = cls.objects.all().count()
        difficulty_factor = (num_boards_stored / BOARD_MAX_COUNT) ** 4
        return difficulty_factor

    @classmethod
    def generate_board(cls) -> Board:
        last_modified = timezone.now()
        content = generate_fake_board_content(last_modified)
        private_key = load_private_key(TEST_KEY_SECRET)
        signature = private_key.sign(content.encode()).hex()
        return cls(
            key=TEST_KEY_PUBLIC,
            content=content,
            signature=signature,
            last_modified=last_modified,
        )


class Peer(models.Model):
    url = models.URLField(verbose_name="URL", unique=True, db_index=True)

    def __str__(self):
        return self.url
