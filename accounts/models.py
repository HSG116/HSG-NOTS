from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """نموذج المستخدم المخصص"""
    
    LANGUAGE_CHOICES = [
        ('ar', 'العربية'),
        ('en', 'English'),
    ]
    

    
    email = models.EmailField(_('البريد الإلكتروني'), unique=True)
    phone = models.CharField(_('رقم الهاتف'), max_length=20, blank=True)
    avatar = models.ImageField(_('الصورة الشخصية'), upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(_('نبذة شخصية'), max_length=500, blank=True)
    
    # إعدادات التخصيص
    preferred_language = models.CharField(
        _('اللغة المفضلة'), 
        max_length=2, 
        choices=LANGUAGE_CHOICES, 
        default='ar'
    )

    notifications_enabled = models.BooleanField(_('تفعيل الإشعارات'), default=True)
    email_notifications = models.BooleanField(_('إشعارات البريد الإلكتروني'), default=True)
    
    # معلومات إضافية
    date_of_birth = models.DateField(_('تاريخ الميلاد'), blank=True, null=True)
    location = models.CharField(_('الموقع'), max_length=100, blank=True)
    
    # إحصائيات
    total_tasks = models.PositiveIntegerField(_('إجمالي المهام'), default=0)
    completed_tasks = models.PositiveIntegerField(_('المهام المكتملة'), default=0)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')
        
    def __str__(self):
        return self.email
    
    @property
    def completion_rate(self):
        """حساب معدل إنجاز المهام"""
        if self.total_tasks == 0:
            return 0
        return round((self.completed_tasks / self.total_tasks) * 100, 2)
    
    def get_full_name(self):
        """الحصول على الاسم الكامل"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
