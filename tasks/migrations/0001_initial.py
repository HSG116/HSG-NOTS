# Generated by Django 4.2.7 on 2025-05-31 23:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='اسم التصنيف')),
                ('name_en', models.CharField(max_length=100, verbose_name='الاسم بالإنجليزية')),
                ('icon', models.CharField(default='fas fa-tasks', max_length=50, verbose_name='الأيقونة')),
                ('color', models.CharField(default='#007bff', max_length=7, verbose_name='اللون')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('is_location_based', models.BooleanField(default=False, verbose_name='مرتبط بموقع')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
            ],
            options={
                'verbose_name': 'تصنيف',
                'verbose_name_plural': 'التصنيفات',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان المهمة')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('priority', models.CharField(choices=[('low', 'منخفضة'), ('medium', 'متوسطة'), ('high', 'عالية'), ('urgent', 'عاجلة')], default='medium', max_length=10, verbose_name='الأولوية')),
                ('status', models.CharField(choices=[('pending', 'معلقة'), ('in_progress', 'قيد التنفيذ'), ('completed', 'مكتملة'), ('cancelled', 'ملغية')], default='pending', max_length=15, verbose_name='الحالة')),
                ('due_date', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الاستحقاق')),
                ('reminder_date', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ التذكير')),
                ('location_name', models.CharField(blank=True, max_length=200, verbose_name='اسم الموقع')),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='خط العرض')),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='خط الطول')),
                ('image', models.ImageField(blank=True, null=True, upload_to='tasks/images/', verbose_name='صورة')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='tasks/attachments/', verbose_name='مرفق')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('estimated_duration', models.PositiveIntegerField(blank=True, null=True, verbose_name='المدة المقدرة (بالدقائق)')),
                ('actual_duration', models.PositiveIntegerField(blank=True, null=True, verbose_name='المدة الفعلية (بالدقائق)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الإكمال')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tasks.category', verbose_name='التصنيف')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'مهمة',
                'verbose_name_plural': 'المهام',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='المحتوى')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tasks.task', verbose_name='المهمة')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'تعليق',
                'verbose_name_plural': 'التعليقات',
                'ordering': ['-created_at'],
            },
        ),
    ]
