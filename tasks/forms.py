from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Task, Category


class TaskForm(forms.ModelForm):
    """نموذج إنشاء وتحرير المهام"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'category', 'priority', 'status',
            'due_date', 'reminder_date', 'location_name', 'latitude', 
            'longitude', 'image', 'attachment', 'notes', 'estimated_duration'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('عنوان المهمة'),
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف المهمة (اختياري)')
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'reminder_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الموقع (اختياري)')
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('ملاحظات إضافية')
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('المدة المقدرة بالدقائق'),
                'min': 1
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تخصيص خيارات التصنيف
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = _('اختر التصنيف')

        # إضافة placeholder للحقول المخفية
        self.fields['latitude'].widget.attrs.update({
            'placeholder': _('خط العرض')
        })
        self.fields['longitude'].widget.attrs.update({
            'placeholder': _('خط الطول')
        })

    def save(self, commit=True):
        """حفظ المهمة مع التأكد من حفظ جميع البيانات"""
        task = super().save(commit=False)

        # التأكد من أن جميع الحقول محفوظة
        if commit:
            # تحديث الطابع الزمني للتحديث
            from django.utils import timezone
            task.updated_at = timezone.now()

            # حفظ المهمة
            task.save()

            # حفظ العلاقات many-to-many
            self.save_m2m()

        return task

    def clean(self):
        """التحقق من صحة البيانات"""
        cleaned_data = super().clean()

        # التحقق من تاريخ الاستحقاق
        due_date = cleaned_data.get('due_date')
        reminder_date = cleaned_data.get('reminder_date')

        if due_date and reminder_date:
            if reminder_date > due_date:
                raise forms.ValidationError(_('تاريخ التذكير يجب أن يكون قبل تاريخ الاستحقاق'))

        # التحقق من الإحداثيات
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if latitude and not longitude:
            raise forms.ValidationError(_('يجب إدخال خط الطول مع خط العرض'))
        if longitude and not latitude:
            raise forms.ValidationError(_('يجب إدخال خط العرض مع خط الطول'))

        return cleaned_data


class TaskFilterForm(forms.Form):
    """نموذج فلترة المهام"""
    
    STATUS_CHOICES = [
        ('', _('جميع الحالات')),
        ('pending', _('معلقة')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتملة')),
        ('cancelled', _('ملغية')),
    ]
    
    PRIORITY_CHOICES = [
        ('', _('جميع الأولويات')),
        ('low', _('منخفضة')),
        ('medium', _('متوسطة')),
        ('high', _('عالية')),
        ('urgent', _('عاجلة')),
    ]
    
    search = forms.CharField(
        label=_('البحث'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('ابحث في المهام...')
        })
    )
    
    status = forms.ChoiceField(
        label=_('الحالة'),
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        label=_('الأولوية'),
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        label=_('التصنيف'),
        queryset=Category.objects.all(),
        required=False,
        empty_label=_('جميع التصنيفات'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class QuickTaskForm(forms.Form):
    """نموذج إضافة مهمة سريعة"""
    
    title = forms.CharField(
        label=_('عنوان المهمة'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('أضف مهمة جديدة...'),
            'required': True
        })
    )
    
    category = forms.ModelChoiceField(
        label=_('التصنيف'),
        queryset=Category.objects.all(),
        required=False,
        empty_label=_('اختر التصنيف'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        label=_('الأولوية'),
        choices=Task.PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TaskCommentForm(forms.Form):
    """نموذج إضافة تعليق على المهمة"""
    
    content = forms.CharField(
        label=_('التعليق'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('أضف تعليقاً...')
        })
    )
