from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

User = get_user_model()


class Category(models.Model):
    """تصنيفات المهام"""
    
    name = models.CharField(_('اسم التصنيف'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100)
    icon = models.CharField(_('الأيقونة'), max_length=50, default='fas fa-tasks')
    color = models.CharField(_('اللون'), max_length=7, default='#007bff')
    description = models.TextField(_('الوصف'), blank=True)
    is_location_based = models.BooleanField(_('مرتبط بموقع'), default=False)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('تصنيف')
        verbose_name_plural = _('التصنيفات')
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Task(models.Model):
    """نموذج المهام"""
    
    PRIORITY_CHOICES = [
        ('low', _('منخفضة')),
        ('medium', _('متوسطة')),
        ('high', _('عالية')),
        ('urgent', _('عاجلة')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('معلقة')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتملة')),
        ('cancelled', _('ملغية')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('المستخدم'))
    title = models.CharField(_('عنوان المهمة'), max_length=200)
    description = models.TextField(_('الوصف'), blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name=_('التصنيف'))
    
    priority = models.CharField(_('الأولوية'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(_('الحالة'), max_length=15, choices=STATUS_CHOICES, default='pending')
    
    due_date = models.DateTimeField(_('تاريخ الاستحقاق'), null=True, blank=True)
    reminder_date = models.DateTimeField(_('تاريخ التذكير'), null=True, blank=True)
    
    # الموقع الجغرافي
    location_name = models.CharField(_('اسم الموقع'), max_length=200, blank=True)
    latitude = models.DecimalField(_('خط العرض'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('خط الطول'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # الملفات المرفقة
    image = models.ImageField(_('صورة'), upload_to='tasks/images/', blank=True, null=True)
    attachment = models.FileField(_('مرفق'), upload_to='tasks/attachments/', blank=True, null=True)
    
    # معلومات إضافية
    notes = models.TextField(_('ملاحظات'), blank=True)
    estimated_duration = models.PositiveIntegerField(_('المدة المقدرة (بالدقائق)'), null=True, blank=True)
    actual_duration = models.PositiveIntegerField(_('المدة الفعلية (بالدقائق)'), null=True, blank=True)
    
    # التواريخ
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('مهمة')
        verbose_name_plural = _('المهام')
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('tasks:detail', kwargs={'pk': self.pk})
    
    @property
    def is_overdue(self):
        """التحقق من تأخر المهمة"""
        if self.due_date and self.status != 'completed':
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False
    
    @property
    def priority_color(self):
        """لون الأولوية"""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        return colors.get(self.priority, '#6c757d')
    
    def save(self, *args, **kwargs):
        # تحديث إحصائيات المستخدم
        if self.pk:  # إذا كانت المهمة موجودة مسبقاً
            old_task = Task.objects.get(pk=self.pk)
            if old_task.status != 'completed' and self.status == 'completed':
                # المهمة تم إكمالها الآن
                self.user.completed_tasks += 1
                self.user.save()
                from django.utils import timezone
                self.completed_at = timezone.now()
        else:
            # مهمة جديدة
            self.user.total_tasks += 1
            self.user.save()
            
        super().save(*args, **kwargs)


class TaskComment(models.Model):
    """تعليقات المهام"""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name=_('المهمة'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('المستخدم'))
    content = models.TextField(_('المحتوى'))
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('تعليق')
        verbose_name_plural = _('التعليقات')
        ordering = ['-created_at']
        
    def __str__(self):
        return f'تعليق على {self.task.title}'
