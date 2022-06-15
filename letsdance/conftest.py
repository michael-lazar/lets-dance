import pytest


# Allow database access in all unit tests
def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.django_db)


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath
