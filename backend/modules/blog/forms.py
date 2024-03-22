from django import forms

from .models import Article


class ArticleCreateForm(forms.ModelForm):
    """
    Форма добавления статей на сайте
    """

    class Meta:
        model = Article
        fields = ('title', 'slug', 'category', 'short_description', 'full_description', 'thumbnail', 'status')

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы Bootstrap
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {'class': 'form-control',
                 'autocomplete': 'off'}
            )


class ArticleUpdateForm(ArticleCreateForm):
    """
    Форма обновления статьи на сайте
    """

    class Meta:
        model = Article
        fields = ArticleCreateForm.Meta.fields + ('updater', 'fixed')

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы под Bootstrap
        """
        super().__init__(*args, **kwargs)
        self.fields['fixed'].widget.attrs.update({
            'class': 'form-check-input'
        })