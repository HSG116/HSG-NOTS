from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """صفحة تسجيل الدخول"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('tasks:dashboard')

    def form_valid(self, form):
        """تسجيل نجاح تسجيل الدخول"""
        username = form.cleaned_data.get('username')
        logger.info(f'نجح تسجيل الدخول للمستخدم: {username}')
        messages.success(self.request, _('مرحباً بك! تم تسجيل دخولك بنجاح'))
        return super().form_valid(form)

    def form_invalid(self, form):
        """تسجيل فشل تسجيل الدخول"""
        username = form.data.get('username', 'غير محدد')
        logger.warning(f'فشل تسجيل الدخول للمستخدم: {username}')
        messages.error(self.request, _('خطأ في البيانات. يرجى التحقق من البريد الإلكتروني وكلمة المرور'))
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """تسجيل الخروج"""
    next_page = reverse_lazy('accounts:login')


class SignUpView(CreateView):
    """صفحة إنشاء حساب جديد"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('tasks:dashboard')

    def form_valid(self, form):
        # حفظ المستخدم
        response = super().form_valid(form)

        # تسجيل دخول المستخدم تلقائياً
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')

        # التأكد من أن المستخدم تم إنشاؤه بنجاح
        user = authenticate(self.request, username=username, password=password)
        if user is not None and user.is_active:
            login(self.request, user)
            messages.success(self.request, _('تم إنشاء حسابك بنجاح! مرحباً بك في مدير المهام الذكي'))
        else:
            messages.error(self.request, _('تم إنشاء الحساب ولكن حدث خطأ في تسجيل الدخول. يرجى تسجيل الدخول يدوياً.'))

        return response

    def form_invalid(self, form):
        """في حالة وجود أخطاء في النموذج"""
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


@login_required
def profile_view(request):
    """صفحة الملف الشخصي"""
    from tasks.models import Task

    user = request.user

    # إحصائيات المهام
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='completed').count()
    pending_tasks = Task.objects.filter(user=user, status='pending').count()
    overdue_tasks = Task.objects.filter(
        user=user,
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now()
    ).count()

    # المهام الحديثة
    recent_tasks = Task.objects.filter(user=user).order_by('-created_at')[:5]

    return render(request, 'accounts/profile.html', {
        'user': user,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
    })


@login_required
def edit_profile_view(request):
    """صفحة تحرير الملف الشخصي"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()

            # إذا كان الطلب AJAX، إرجاع JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': str(_('تم حفظ التغييرات تلقائياً')),
                    'user_data': {
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'email': request.user.email,
                        'phone': getattr(request.user, 'phone', ''),
                        'bio': getattr(request.user, 'bio', ''),
                        'location': getattr(request.user, 'location', ''),

                        'theme': getattr(request.user, 'theme', 'light'),
                        'notifications_enabled': getattr(request.user, 'notifications_enabled', True),
                        'email_notifications': getattr(request.user, 'email_notifications', True),
                    }
                })

            # إذا كان طلب عادي، إرجاع رسالة وإعادة توجيه
            messages.success(request, _('تم تحديث ملفك الشخصي بنجاح'))
            return redirect('accounts:profile')
        else:
            # في حالة وجود أخطاء
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0] if error_list else ''

                return JsonResponse({
                    'success': False,
                    'message': str(_('يرجى تصحيح الأخطاء في النموذج')),
                    'errors': errors
                })

            messages.error(request, _('يرجى تصحيح الأخطاء أدناه'))
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {
        'form': form
    })


@login_required
def settings_view(request):
    """صفحة الإعدادات"""
    if request.method == 'POST':
        try:
            # تحديث الإعدادات
            user = request.user





            # تحديث إعدادات الإشعارات
            user.notifications_enabled = 'notifications_enabled' in request.POST
            user.email_notifications = 'email_notifications' in request.POST

            # حفظ التغييرات
            user.save()

            # إذا كان الطلب AJAX، إرجاع JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': str(_('تم حفظ الإعدادات بنجاح'))
                })

            # إذا كان طلب عادي، إرجاع رسالة وإعادة توجيه
            messages.success(request, _('تم حفظ الإعدادات بنجاح'))
            return redirect('accounts:settings')

        except Exception as e:
            # في حالة حدوث خطأ
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': str(_('حدث خطأ في حفظ الإعدادات'))
                })

            messages.error(request, _('حدث خطأ في حفظ الإعدادات'))
            return redirect('accounts:settings')

    return render(request, 'accounts/settings.html', {
        'user': request.user
    })


def dashboard_redirect(request):
    """إعادة توجيه إلى لوحة التحكم أو صفحة تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    return redirect('accounts:login')
