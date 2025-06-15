from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Conversation(models.Model):
    """محادثات المستخدم مع المساعد الذكي"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('المستخدم'))
    title = models.CharField(_('عنوان المحادثة'), max_length=200, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('محادثة')
        verbose_name_plural = _('المحادثات')
        ordering = ['-updated_at']
        
    def __str__(self):
        return self.title or f'محادثة {self.created_at.strftime("%Y-%m-%d")}'
    
    def save(self, *args, **kwargs):
        # حفظ الكائن أولاً للحصول على المفتاح الأساسي
        super().save(*args, **kwargs)

    def update_title_from_first_message(self):
        """تحديث عنوان المحادثة بناءً على أول رسالة"""
        if not self.title and self.pk:
            first_message = self.messages.first()
            if first_message:
                self.title = first_message.content[:50] + '...' if len(first_message.content) > 50 else first_message.content
                self.save(update_fields=['title'])


class Message(models.Model):
    """رسائل المحادثة"""
    
    MESSAGE_TYPES = [
        ('user', _('مستخدم')),
        ('assistant', _('مساعد')),
        ('system', _('نظام')),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name=_('المحادثة')
    )
    message_type = models.CharField(_('نوع الرسالة'), max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField(_('المحتوى'))
    
    # للرسائل التي تحتوي على صور
    image = models.ImageField(_('صورة'), upload_to='ai_messages/', blank=True, null=True)
    
    # معلومات إضافية
    tokens_used = models.PositiveIntegerField(_('الرموز المستخدمة'), default=0)
    response_time = models.FloatField(_('وقت الاستجابة (ثانية)'), default=0.0)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('رسالة')
        verbose_name_plural = _('الرسائل')
        ordering = ['created_at']
        
    def __str__(self):
        return f'{self.get_message_type_display()}: {self.content[:50]}...'


class AIUsageStats(models.Model):
    """إحصائيات استخدام المساعد الذكي"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('المستخدم'))
    total_conversations = models.PositiveIntegerField(_('إجمالي المحادثات'), default=0)
    total_messages = models.PositiveIntegerField(_('إجمالي الرسائل'), default=0)
    total_tokens_used = models.PositiveIntegerField(_('إجمالي الرموز المستخدمة'), default=0)
    total_images_analyzed = models.PositiveIntegerField(_('إجمالي الصور المحللة'), default=0)
    
    # إحصائيات يومية
    daily_messages_count = models.PositiveIntegerField(_('عدد الرسائل اليومية'), default=0)
    last_reset_date = models.DateField(_('تاريخ آخر إعادة تعيين'), auto_now_add=True)
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('إحصائيات الاستخدام')
        verbose_name_plural = _('إحصائيات الاستخدام')
        
    def __str__(self):
        return f'إحصائيات {self.user.username}'
    
    def reset_daily_count(self):
        """إعادة تعيين العداد اليومي"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.daily_messages_count = 0
            self.last_reset_date = today
            self.save()


class TaskSuggestion(models.Model):
    """اقتراحات المهام من المساعد الذكي"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('المستخدم'))
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_('المحادثة')
    )
    
    suggested_title = models.CharField(_('العنوان المقترح'), max_length=200)
    suggested_description = models.TextField(_('الوصف المقترح'), blank=True)
    suggested_category = models.CharField(_('التصنيف المقترح'), max_length=100, blank=True)
    suggested_priority = models.CharField(_('الأولوية المقترحة'), max_length=10, blank=True)
    suggested_due_date = models.DateTimeField(_('تاريخ الاستحقاق المقترح'), null=True, blank=True)
    
    is_accepted = models.BooleanField(_('تم القبول'), default=False)
    created_task = models.ForeignKey(
        'tasks.Task', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('المهمة المنشأة')
    )
    
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('اقتراح مهمة')
        verbose_name_plural = _('اقتراحات المهام')
        ordering = ['-created_at']
        
    def __str__(self):
        return self.suggested_title
