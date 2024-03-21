from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()


class Article(models.Model):
    """
    Модель постов для сайта
    """

    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )

    title = models.CharField(verbose_name='Заголовок', max_length=255)
    slug = models.SlugField(verbose_name='URL', max_length=255, unique=True, blank=True)
    short_description = models.TextField(verbose_name='Краткое описание', max_length=500)
    full_description = models.TextField(verbose_name='Полное описание')
    thumbnail = models.ImageField(
        verbose_name='Превью поста',
        blank=True,
        upload_to='images/thumbnails/',
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'webp', 'jpeg', 'gif'])]
    )
    status = models.CharField(choices=STATUS_OPTIONS, default='published', max_length=10, verbose_name='Статус поста')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    author = models.ForeignKey(to=User, verbose_name='Автор', on_delete=models.SET_DEFAULT, related_name='author_posts', default=1)
    updater = models.ForeignKey(to=User, verbose_name='Обновил', on_delete=models.SET_NULL, null=True, related_name='updater_posts', blank=True)
    fixed = models.BooleanField(default=False, verbose_name='Зафиксировано')

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-fixed', '-time_create']
        db_table = 'app_articles'
        indexes = [models.Index(fields=['-fixed', '-time_create', 'status'])]

    def __str__(self):
        return self.title



