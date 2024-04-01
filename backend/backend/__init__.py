# This will make sure the app is always imported when Django starts so that shares_task will use the app
# Это позволит гарантировать, что приложение всегда импортируется при запуске Django, и Shares_task будет использовать это приложение.

from .celery import app as celery_app

__all__ = ('celery_app',)
