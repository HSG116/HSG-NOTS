from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Conversation, Message, AIUsageStats, TaskSuggestion


class MessageInline(admin.TabularInline):
    """رسائل المحادثة كـ inline"""
    model = Message
    extra = 0
    readonly_fields = ('created_at', 'response_time', 'tokens_used')
    fields = ('message_type', 'content', 'tokens_used', 'response_time', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """إدارة المحادثات"""
    
    list_display = ('title', 'user', 'message_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'user__username', 'user__email')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    
    inlines = [MessageInline]
    
    def message_count(self, obj):
        """عدد الرسائل في المحادثة"""
        return obj.messages.count()
    message_count.short_description = _('عدد الرسائل')
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('user').prefetch_related('messages')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """إدارة الرسائل"""
    
    list_display = (
        'conversation_title', 'user', 'message_type', 
        'content_preview', 'tokens_used', 'response_time', 'created_at'
    )
    list_filter = ('message_type', 'created_at', 'conversation__user')
    search_fields = ('content', 'conversation__title', 'conversation__user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'tokens_used', 'response_time')
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('conversation', 'message_type', 'content')
        }),
        (_('الوسائط'), {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        (_('إحصائيات'), {
            'fields': ('tokens_used', 'response_time', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def conversation_title(self, obj):
        """عنوان المحادثة"""
        return obj.conversation.title
    conversation_title.short_description = _('المحادثة')
    
    def user(self, obj):
        """المستخدم"""
        return obj.conversation.user
    user.short_description = _('المستخدم')
    
    def content_preview(self, obj):
        """معاينة المحتوى"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = _('المحتوى')
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('conversation__user')


@admin.register(AIUsageStats)
class AIUsageStatsAdmin(admin.ModelAdmin):
    """إدارة إحصائيات الاستخدام"""
    
    list_display = (
        'user', 'total_conversations', 'total_messages', 
        'daily_messages_count', 'total_tokens_used', 
        'total_images_analyzed', 'last_reset_date'
    )
    list_filter = ('last_reset_date', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-total_messages',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('إحصائيات عامة'), {
            'fields': (
                'total_conversations', 'total_messages', 
                'total_tokens_used', 'total_images_analyzed'
            )
        }),
        (_('إحصائيات يومية'), {
            'fields': ('daily_messages_count', 'last_reset_date')
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('user')


@admin.register(TaskSuggestion)
class TaskSuggestionAdmin(admin.ModelAdmin):
    """إدارة اقتراحات المهام"""
    
    list_display = (
        'suggested_title', 'user', 'suggested_priority', 
        'is_accepted', 'created_task_link', 'created_at'
    )
    list_filter = ('is_accepted', 'suggested_priority', 'created_at', 'user')
    search_fields = (
        'suggested_title', 'suggested_description', 
        'user__username', 'user__email'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('user', 'conversation')
        }),
        (_('الاقتراح'), {
            'fields': (
                'suggested_title', 'suggested_description', 
                'suggested_category', 'suggested_priority', 
                'suggested_due_date'
            )
        }),
        (_('الحالة'), {
            'fields': ('is_accepted', 'created_task')
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def created_task_link(self, obj):
        """رابط المهمة المنشأة"""
        if obj.created_task:
            return f'<a href="/admin/tasks/task/{obj.created_task.id}/change/">{obj.created_task.title}</a>'
        return '-'
    created_task_link.allow_tags = True
    created_task_link.short_description = _('المهمة المنشأة')
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related(
            'user', 'conversation', 'created_task'
        )
