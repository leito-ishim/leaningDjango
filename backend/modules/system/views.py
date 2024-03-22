from django.views.generic import DetailView, UpdateView, ListView
from django.db import transaction
from django.urls import reverse_lazy

from .models import Profile
from .forms import UserUpdateForm, ProfileUpdateForm

# Create your views here.

class ProfileDetailView(DetailView):
    """
    Представление для просмотра профиля
    """
    model = Profile
    template_name = 'system/profile_detail.html'
    context_object_name = 'profile'
    queryset = model.objects.all().select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Страница пользователя: {self.object.user.username}'
        return context


class ProfileUpdateView(UpdateView):
    """
    Представление для редактирования профиля
    """

    model = Profile
    template_name = 'system/profile_edit.html'
    form_class = ProfileUpdateForm

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование профиля пользователя: {self.object.user.username}'
        if self.request.method == 'POST':
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        with transaction.atomic():
            if all([form.is_valid(), user_form.is_valid()]):
                user_form.save()
                form.save()
            else:
                context.update({'user_form': user_form})
                return self.render_to_response(context)
        return super(ProfileUpdateView, self).form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('profile_detail', kwargs={'slug': self.object.slug})