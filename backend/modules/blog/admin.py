from django.contrib import admin

from .models import Article, Category, Comment, Rating
from mptt.admin import DraggableMPTTAdmin


# Register your models here.

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    """
    Админ панель модели категорий
    """
    list_display = ('tree_actions', 'indented_title', 'id', 'title', 'slug')
    list_display_links = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Основная информация', {'fields': ('title', 'slug', 'parent')}),
        ('Описание', {'fields': ('description',)})
    )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


# admin.site.register(Article)


@admin.register(Comment)
class CommentAdminPage(DraggableMPTTAdmin):
    """
    Админ-панель модели комментариев
    """

    list_display = ('tree_actions', 'indented_title', 'article', 'author', 'time_create', 'status')
    mptt_level_indent = 2
    list_display_links = ('article',)
    list_filter = ('time_create', 'time_update', 'author')
    list_editable = ('status',)


@admin.register(Rating)
class RatingAdminPage(admin.ModelAdmin):
    list_display = ('article', 'user', 'value', 'time_create')

