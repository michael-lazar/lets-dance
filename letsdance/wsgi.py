import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsdance.settings")

application = get_wsgi_application()

from letsdance.core.tasks import scheduler  # noqa: E402

scheduler.start()
