from django.views.generic import DetailView, UpdateView, CreateView, TemplateView, View
from django.urls import reverse_lazy
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
# from django.utils.encoding import force_bytes
# from django.contrib.sites.models import Site
# from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, \
    PasswordResetConfirmView
from django.http import JsonResponse

from .models import Profile, Feedback
from .forms import UserUpdateForm, ProfileUpdateForm, UserRegisterForm, UserLoginForm, UserPasswordChangeForm, \
    UserForgotPasswordForm, UserSetNewPasswordForm, FeedbackCreateForm
from ..services.mixins import UserIsNotAuthenticated
# from ..services.email import send_contact_email_message
from ..services.utils import get_client_ip
from ..services.tasks import send_contact_email_message_tasks, send_activate_email_message_task

# Create your views here.

User = get_user_model()


class ProfileDetailView(DetailView):
    """
    Представление для просмотра профиля
    """
    model = Profile
    template_name = 'system/profile_detail.html'
    context_object_name = 'profile'
    queryset = model.objects.all().select_related('user').prefetch_related('followers', 'followers__user', 'following',
                                                                           'following__user')

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


class UserRegisterView(UserIsNotAuthenticated, CreateView):
    """
    Представление регистрации на сайте с формой регистрации
    """

    form_class = UserRegisterForm
    success_url = reverse_lazy('home')
    template_name = 'system/registration/user_register.html'

    # success_message = 'Вы успешно зарегистрировались. Можете войти на сайт!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация на сайте'
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        # Функционал для отправки письма и генерации токена
        send_activate_email_message_task.delay(user.id)
        return redirect('email_confirmation_sent')


class UserLoginView(SuccessMessageMixin, LoginView):
    """
    Авторизация на сайте
    """

    form_class = UserLoginForm
    template_name = 'system/registration/user_login.html'
    next_page = 'home'
    success_message = 'Добро пожаловать на сайт'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторизация на сайте'
        return context


class UserLogoutView(SuccessMessageMixin, LogoutView):
    """
    Выход с сайта
    """
    next_page = 'home'
    success_message = 'Вы успешно разлогинились'


class UserPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    """
    Изменение пароля пользователя
    """

    form_class = UserPasswordChangeForm
    template_name = 'system/registration/user_password_change.html'
    success_message = 'Ваш пароль успешно изменен!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Изменение пароля на сайте'
        return context

    def get_success_url(self):
        return reverse_lazy('profile_detail', kwargs={'slug': self.request.user.profile.slug})


class UserForgotPasswordView(SuccessMessageMixin, PasswordResetView):
    """
    Представление по сбросу пароля по почту
    """

    form_class = UserForgotPasswordForm
    template_name = 'system/registration/user_password_reset.html'
    success_message = 'Письмо с инструкцией по восстановлению пароля отправлено на ваш email адрес'
    success_url = reverse_lazy('home')
    subject_template_name = 'system/email/password_subject_reset_mail.txt'
    email_template_name = 'system/email/password_reset_mail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Запрос на восстановление пароля'
        return context


class UserPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    """
    Представление установки нового пароля
    """

    form_class = UserSetNewPasswordForm
    template_name = 'system/registration/user_password_set_new.html'
    success_message = 'Пароль успешно изменен. Можете авторизоваться на сайте.'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Установить новый пароль'
        return context


class UserConfirmEmailView(View):
    """
    Представление для обработки токена и подтверждения пользователя
    """

    def get(selfself, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('email_confirmed')
        else:
            return redirect('email_confirmation_failed')


class EmailConfirmationSentView(TemplateView):
    template_name = 'system/registration/email_confirmation_sent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Письмо активации отправлено'
        return context


class EmailConfirmedView(TemplateView):
    template_name = 'system/registration/email_confirmed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ваш электронный адрес активирован'
        return context


class EmailConfirmationFailedView(TemplateView):
    template_name = 'system/registration/email_confirmation_failed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ваш электронный адрес не активирован'
        return context


class FeedbackCreateView(SuccessMessageMixin, CreateView):
    model = Feedback
    form_class = FeedbackCreateForm
    template_name = 'system/feedback.html'
    success_message = 'Ваше письмо успешно отправлено администрации сайта'
    extra_context = {'title': 'Контактная форма'}
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.ip_address = get_client_ip(self.request)
            if self.request.user.is_authenticated:
                feedback.user = self.request.user
            send_contact_email_message_tasks.delay(feedback.subject, feedback.email, feedback.content,
                                                   feedback.ip_address, feedback.user_id)
        return super().form_valid(form)


def tr_handler500(request):
    """
    Обработка ошибки 500
    """
    return render(request=request, template_name='system/errors/error_page.html', status=500, context={
        'title': 'Ошибка сервера: 500',
        'error_message': 'Внутренняя ошибка сайта, вернитесь на главную страницу, отчет об ошибке мы направим администрации сайта.',
    })


def tr_handler403(request, exception):
    """
    Обработка ошибки 403
    """
    return render(request=request, template_name='system/errors/error_page.html', status=403, context={
        'title': 'Ошибка доступа: 403',
        'error_message': 'Доступ к этой странице ограничен',
    })


def tr_handler404(request, exception):
    """
    Обработка ошибки 404
    """
    return render(request=request, template_name='system/errors/error_page.html', status=404, context={
        'title': 'Страница не найдена',
        'error_message': 'К сожалению такая страница была не найдена, или перемещена',
    })


@method_decorator(login_required, name='dispatch')
class ProfileFollowingCreateView(View):
    """
    Создание подписки для пользователя
    """
    model = Profile

    def is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def post(self, request, slug):
        user = self.model.objects.get(slug=slug)
        profile = request.user.profile
        if profile in user.followers.all():
            user.followers.remove(profile)
            message = f'Подписаться на {user}'
            status = False
        else:
            user.followers.add(profile)
            message = f'Отписаться от {user}'
            status = True
        data = {
            'username': profile.user.username,
            'get_absolute_url': profile.get_absolute_url(),
            'slug': profile.slug,
            'avatar': profile.get_avatar,
            'message': message,
            'status': status,
        }
        return JsonResponse(data, status=200)
