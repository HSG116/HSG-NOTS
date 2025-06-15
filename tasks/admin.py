from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Category, Task, TaskComment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """إدارة التصنيفات"""
    
    list_display = ('name', 'name_en', 'icon', 'color', 'is_location_based', 'created_at')
    list_filter = ('is_location_based', 'created_at')
    search_fields = ('name', 'name_en', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'name_en', 'description')
        }),
        (_('التخصيص'), {
            'fields': ('icon', 'color', 'is_location_based')
        }),
    )


class TaskCommentInline(admin.TabularInline):
    """تعليقات المهام كـ inline"""
    model = TaskComment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """إدارة المهام"""
    
    list_display = (
        'title', 'user', 'category', 'priority', 'status', 
        'due_date', 'is_overdue', 'created_at'
    )
    list_filter = (
        'status', 'priority', 'category', 'created_at', 
        'due_date', 'user'
    )
    search_fields = ('title', 'description', 'notes', 'user__username', 'user__email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('user', 'title', 'description', 'category')
        }),
        (_('الحالة والأولوية'), {
            'fields': ('status', 'priority')
        }),
        (_('التواريخ'), {
            'fields': ('due_date', 'reminder_date', 'completed_at')
        }),
        (_('الموقع'), {
            'fields': ('location_name', 'latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        (_('الملفات'), {
            'fields': ('image', 'attachment'),
            'classes': ('collapse',)
        }),
        (_('معلومات إضافية'), {
            'fields': ('notes', 'estimated_duration', 'actual_duration'),
            'classes': ('collapse',)
        }),
        (_('معلومات النظام'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [TaskCommentInline]
    
    def is_overdue(self, obj):
        """عرض حالة التأخير"""
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = _('متأخرة')
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('user', 'category')


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """إدارة تعليقات المهام"""
    
    list_display = ('task', 'user', 'content_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'task__title', 'user__username')
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        """معاينة المحتوى"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('المحتوى')
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('task', 'user')


# تخصيص موقع الإدارة
admin.site.site_header = _('إدارة مدير المهام الذكي')
admin.site.site_title = _('مدير المهام')
admin.site.index_title = _('لوحة تحكم الإدارة')
