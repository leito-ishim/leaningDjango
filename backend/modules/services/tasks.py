from celery import shared_task
from django.core.management import call_command

from .email import send_activate_email_message, send_contact_email_message

@shared_task
def send_activate_email_message_task(user_id):
    """
    1. Задача обрабатывается в представлении: UserRegisterView
    2. Отправка письма подтверждения осуществляется через функцию: send_activate_email_message
    """
    return send_activate_email_message(user_id)


@shared_task
def send_contact_email_message_tasks(subject, email, content, ip, user_id):
    """
        1. Задача обрабатывается в представлении: FeedbackCreateView
        2. Отправка письма из формы обратной связи осуществляется через функцию: send_contact_email_message
        """
    return send_contact_email_message(subject, email, content, ip, user_id)


@shared_task()
def dbackup_task():
    """
    Выполнение резервного копирования базы данных
    """
    call_command('dbackup')
