from .models import ViewCount
from modules.services.utils import get_client_ip

class ViewCountMixin:
    """
    Миксин для увеличения счетчика просмотров статьи
    """
    def get_object(self):
        # получаем статью из метода родительского класса
        obj = super().get_object()
        # получаем IP-адрес пользователя
        ip_address = get_client_ip(self.request)
        # получаем или создаем запись о просмотре статьи для данного пользователя
        ViewCount.objects.get_or_create(article=obj, ip_address=ip_address)
        return obj