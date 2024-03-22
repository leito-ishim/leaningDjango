from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Article, Category
from .forms import ArticleCreateForm, ArticleUpdateForm
from django.urls import reverse_lazy

from django.shortcuts import render
from django.core.paginator import Paginator


# Create your views here.
class ArticleListView(ListView):
    model = Article
    template_name = 'blog/articles_list.html'
    context_object_name = 'articles'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная страница'
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'blog/articles_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        return context


class ArticleByCategoryListView(ListView):
    model = Article
    template_name = 'blog/articles_list.html'
    context_object_name = 'articles'
    category = None
    paginate_by = 3

    def get_queryset(self):
        self.category = Category.objects.get(slug=self.kwargs['slug'])
        queryset = Article.objects.all().filter(category__slug=self.category.slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Статьи из категории: {self.category.title}'
        return context


class ArticleCreateView(CreateView):
    """
    Представление создание материалов на сайте
    """
    model = Article
    template_name = 'blog/articles_create.html'
    form_class = ArticleCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление статьи на сайт'
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)


class ArticleUpdateView(UpdateView):
    """
    Представление : обновление материала на сайте
    """

    model = Article
    template_name = 'blog/articles_update.html'
    form_class = ArticleUpdateForm
    context_object_name = 'article'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Обновление статьи: {self.object.title}'
        return context

    def form_valid(self, form):
        # form.instance.updater = self.request.user
        form.save()
        return super().form_valid(form)


class ArticleDeleteView(DeleteView):
    """
    Представление для удаления статьи
    """
    model = Article
    template_name = 'blog/articles_delete.html'
    success_url = reverse_lazy('home')
    context_object_name = 'article'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удаление статьи: {self.object.title}'
        return context


# Функция создавалась для реализации пагинации через функции. Сейчас не нужна, пагинация реализована в классах
# def articles_list(request):
#     articles = Article.objects.all()
#     paginator = Paginator(articles, per_page=2)
#     page_number = request.GET.get('page')
#     page_object = paginator.get_page(page_number)
#     context = {'page_obj': page_object}
#     return render(request, 'blog/articles_func_list.html', context)
