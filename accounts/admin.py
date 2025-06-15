from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """إدارة المستخدمين في لوحة الإدارة"""
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'preferred_language')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('معلومات شخصية'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'bio', 'date_of_birth', 'location')
        }),
        (_('الصلاحيات'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('إعدادات التخصيص'), {
            'fields': ('preferred_language', 'notifications_enabled', 'email_notifications')
        }),
        (_('إحصائيات'), {
            'fields': ('total_tasks', 'completed_tasks'),
            'classes': ('collapse',)
        }),
        (_('تواريخ مهمة'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
