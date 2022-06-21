from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from letsdance.core.constants import TEST_KEY_PUBLIC
from letsdance.core.crypto import dump_public_key, generate_private_key
from letsdance.core.models import Board
from letsdance.core.tests.factories import BoardFactory
from letsdance.core.utils import date_to_header, generate_fake_board_content


class TestIndexView(TestCase):
    def test_difficulty_factor_zero(self):
        """
        Difficulty factor should always be zero.
        """
        BoardFactory.create_batch(10)
        response = self.client.get(reverse("index"))
        assert response.status_code == 200
        assert response.headers["Spring-Version"] == "83"
        assert response.headers["Spring-Difficulty"] == "0"


class TestBoardView(TestCase):

    # Normally keys need to end in "ed2022", but this makes it too expensive to
    # generate keys for testing.
    skip_public_key_validation = mock.patch(
        "letsdance.core.views.validate_public_key",
        return_value=True,
    )

    def test_get_unrecognized_board(self):
        """
        If the supplied key is not in the database return an error.
        """
        board = BoardFactory()
        board.delete()

        response = self.client.get(reverse("board", args=[board.key]))
        assert response.status_code == 404
        assert response.headers["Spring-Version"] == "83"

    def test_get_if_modified_since_invalid(self):
        """
        If the if-modified-since header is newer than the saved board, don't return it.
        """
        board = BoardFactory(last_modified=timezone.now() - timedelta(minutes=30))

        if_modified_since = timezone.now() - timedelta(minutes=20)
        headers = {"HTTP_IF_MODIFIED_SINCE": date_to_header(if_modified_since)}
        response = self.client.get(reverse("board", args=[board.key]), **headers)
        assert response.status_code == 304
        assert response.headers["Spring-Version"] == "83"

    def test_get_success(self):
        """
        If everything checks out, we should return the board content.
        """
        board = BoardFactory(last_modified=timezone.now() - timedelta(minutes=30))

        if_modified_since = timezone.now() - timedelta(minutes=40)
        headers = {"HTTP_IF_MODIFIED_SINCE": date_to_header(if_modified_since)}
        response = self.client.get(reverse("board", args=[board.key]), **headers)
        assert response.status_code == 200
        assert response.getvalue() == board.content.encode()
        assert response.headers["Spring-Version"] == "83"
        assert response.headers["Spring-Signature"] == board.signature

    def test_get_test_board(self):
        """
        Should return an automatically generate board if the test key is used.
        """
        response = self.client.get(reverse("board", args=[TEST_KEY_PUBLIC]))
        assert response.status_code == 200
        assert response.getvalue()
        assert response.headers["Spring-Version"] == "83"
        assert response.headers["Spring-Signature"]

    def test_put_above_max_size(self):
        """
        The board content must be under the maximum allowed size.
        """
        content = "X" * 5000
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        signature = private_key.sign(content.encode()).hex()

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(timezone.now()),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 413

    def test_put_test_board(self):
        """
        Cannot put a board using the test keypair.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        content = generate_fake_board_content(last_modified)
        signature = private_key.sign(content.encode()).hex()

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[TEST_KEY_PUBLIC])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 401

    def test_put_invalid_key(self):
        """
        Should not be able to PUT if the key doesn't have the correct suffix.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = generate_fake_board_content(last_modified)
        signature = private_key.sign(content.encode()).hex()

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 400

    @skip_public_key_validation
    def test_put_unmodified_old_timestamp(self, *_):
        """
        Cannot put a board with an older timestamp than the board in the database.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = generate_fake_board_content(last_modified)
        signature = private_key.sign(content.encode()).hex()

        BoardFactory(content=content, key=key, signature=signature)

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified - timedelta(hours=1)),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 409

    @skip_public_key_validation
    def test_put_missing_authorization(self, *_):
        """
        Cannot put without an authorization header.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = generate_fake_board_content(last_modified)

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified),
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 401

    @skip_public_key_validation
    def test_put_invalid_signature(self, *_):
        """
        Cannot put if the signature does not match the content body.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = generate_fake_board_content(last_modified)
        signature = private_key.sign(content.encode()).hex()

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        malicious_content = content + "😈"
        response = self.client.put(url, data=malicious_content, content_type="text/html", **headers)
        assert response.status_code == 401

    @skip_public_key_validation
    def test_put_missing_last_modified_time(self, *_):
        """
        The last-modified <time> tag must be included in the html.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = "Hello World!"
        signature = private_key.sign(content.encode()).hex()

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 400

    @skip_public_key_validation
    def test_put_success_create(self, *_):
        """
        Should be able to create a new board via PUT.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = generate_fake_board_content(last_modified)
        signature = private_key.sign(content.encode()).hex()

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(last_modified),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 200

        board = Board.objects.get(key=key)
        assert board.signature == signature
        assert board.content == content

    @skip_public_key_validation
    def test_put_success_update(self, *_):
        """
        Should be able to update an existing board via PUT.
        """
        last_modified = timezone.now()
        private_key = generate_private_key()
        key = dump_public_key(private_key.public_key())
        content = generate_fake_board_content(last_modified)
        signature = private_key.sign(content.encode()).hex()

        board = BoardFactory(key=key, last_modified=last_modified - timedelta(days=1))

        headers = {
            "HTTP_IF_UNMODIFIED_SINCE": date_to_header(timezone.now()),
            "HTTP_SPRING_SIGNATURE": signature,
        }
        url = reverse("board", args=[key])
        response = self.client.put(url, data=content, content_type="text/html", **headers)
        assert response.status_code == 200

        board.refresh_from_db()
        assert board.signature == signature
        assert board.content == content
