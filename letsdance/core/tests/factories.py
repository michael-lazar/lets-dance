import factory
from django.utils import timezone
from factory import Faker
from factory.django import DjangoModelFactory

from letsdance.core.models import Board, Peer

now = timezone.now()


class UniqueFaker(factory.Faker):
    @classmethod
    def _get_faker(cls, locale=None):
        return super()._get_faker(locale=locale).unique


class BoardFactory(DjangoModelFactory):

    content = Faker("text")
    key = UniqueFaker("hexify", text=f"{'^'*58}ed{now.year}")
    signature = Faker("hexify", text="^" * 128)

    class Meta:
        model = Board


class PeerFactory(DjangoModelFactory):

    url = UniqueFaker("url")

    class Meta:
        model = Peer
