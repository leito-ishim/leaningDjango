from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from django.db.models import ForeignKey
from django.urls import reverse
from mptt.fields import TreeManyToManyField
from django_ckeditor_5.fields import CKEditor5Field

from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager

from modules.services.utils import unique_slugify, image_compress


# Create your models here.

User = get_user_model()


class Article(models.Model):
    """
    Модель постов для сайта
    """

    class ArticleManager(models.Manager):
        """
        Кастомный менеджер для модели статей
        """

        def all(self):
            """
            Список статей (SQL запрос с фильтрацией для страницы списка статей)
            """
            return self.get_queryset().select_related('author', 'category').prefetch_related('ratings').filter(
                status='published')

        def detail(self):
            """
            Детальная статья (SQL запрос с фильтрацией для страницы со статьей)
            """
            return self.get_queryset().select_related('author', 'category').prefetch_related('comments',
                                                                                             'comments__author',
                                                                                             'comments__author__profile',
                                                                                             'tags',
                                                                                             'ratings').filter(
                status='published')

    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )

    title = models.CharField(verbose_name='Заголовок', max_length=255)
    slug = models.SlugField(verbose_name='URL', max_length=255, unique=True, blank=True)
    short_description = CKEditor5Field(verbose_name='Краткое описание', max_length=500, config_name='extends')
    full_description = CKEditor5Field(verbose_name='Полное описание', config_name='extends')
    thumbnail = models.ImageField(
        verbose_name='Превью поста',
        blank=True,
        upload_to='images/thumbnails/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'webp', 'jpeg', 'gif'])],
    )
    status = models.CharField(choices=STATUS_OPTIONS, default='published', max_length=10, verbose_name='Статус поста')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    author = models.ForeignKey(to=User, verbose_name='Автор', on_delete=models.SET_DEFAULT, related_name='author_posts',
                               default=1)
    updater = models.ForeignKey(to=User, verbose_name='Обновил', on_delete=models.SET_NULL, null=True,
                                related_name='updater_posts', blank=True)
    fixed = models.BooleanField(default=False, verbose_name='Зафиксировано')
    category = TreeForeignKey('Category', verbose_name='Категория', on_delete=models.PROTECT, related_name='articles')

    tags = TaggableManager()
    objects = ArticleManager()

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-fixed', '-time_create']
        db_table = 'app_articles'
        indexes = [models.Index(fields=['-fixed', '-time_create', 'status'])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('articles_detail', kwargs={'slug': self.slug})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__thumbnail = self.thumbnail if self.pk else None


    def save(self, *args, **kwargs):
        """
        Сохранение полей модели при отсутствии их заполнения
        """
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

        if self.__thumbnail != self.thumbnail and self.thumbnail:
            image_compress(self.thumbnail.path, width=500, height=500)

    def get_sum_rating(self):
        return sum([rating.value for rating in self.ratings.all()])


class Category(MPTTModel):
    """
    Модель категорий с вложенностью
    """

    title = models.CharField(verbose_name='Название категории', max_length=255)
    slug = models.SlugField(verbose_name='URL категории', max_length=255, blank=True)
    description = models.TextField(verbose_name='Описание категории', max_length=300)
    parent = TreeForeignKey(
        'self',
        verbose_name='родительская категория',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
        db_index=True,
    )

    class MPTTMeta:
        """
        Сортировка по вложенности
        """
        order_insertion_by = ('title',)

    class Meta:
        """
        Сортировка, название модели в админ панели, таблица с данными
        """
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'app_categories'

    def __str__(self):
        """
        Возвращение заголовка статьи
        """
        return self.title

    def get_absolute_url(self):
        return reverse('articles_by_category', kwargs={'slug': self.slug})


class Comment(MPTTModel):
    """
    Модель древовидных комментариев
    """

    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name='Статья')
    author = models.ForeignKey(User, verbose_name='Автор комментария', on_delete=models.CASCADE,
                               related_name='comments_author')
    content = models.TextField(verbose_name='Текст комментария', max_length=3000)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    status = models.CharField(choices=STATUS_OPTIONS, default='published', verbose_name='Статус поста', max_length=10)
    parent = TreeForeignKey('self', verbose_name='Родительский комментарий', null=True, blank=True,
                            related_name='children', on_delete=models.CASCADE)

    class MTTMeta:
        order_insertion_by = ('-time_create',)

    class Meta:
        db_table = 'app_comments'
        indexes = [models.Index(fields=['-time_create', 'time_update', 'status', 'parent'])]
        ordering = ['-time_create']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author}:{self.content}'


class Rating(models.Model):
    """
    Модель рейтинга: Лайк - Дизлайк
    """

    article = models.ForeignKey(to=Article, verbose_name='Статья', on_delete=models.CASCADE, related_name='ratings')
    user = ForeignKey(to=User, verbose_name='Пользователь', on_delete=models.CASCADE, blank=True, null=True)
    value = models.IntegerField(verbose_name='Значение', choices=[(1, 'Нравится'), (-1, 'Не нравится')])
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    ip_address = models.GenericIPAddressField(verbose_name='IP Адрес')

    class Meta:
        unique_together = ('article', 'ip_address')
        ordering = ('-time_create',)
        indexes = [models.Index(fields=['-time_create', 'value'])]
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'

    def __str__(self):
        return self.article.title
