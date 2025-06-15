from django.core.management.base import BaseCommand
from tasks.models import Category


class Command(BaseCommand):
    help = 'إنشاء التصنيفات الأساسية للمهام'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'دراسية',
                'name_en': 'Study',
                'icon': 'fas fa-graduation-cap',
                'color': '#007bff',
                'description': 'المهام المتعلقة بالدراسة والتعليم',
                'is_location_based': False
            },
            {
                'name': 'رياضية',
                'name_en': 'Sports',
                'icon': 'fas fa-dumbbell',
                'color': '#28a745',
                'description': 'الأنشطة الرياضية واللياقة البدنية',
                'is_location_based': True
            },
            {
                'name': 'اجتماعية',
                'name_en': 'Social',
                'icon': 'fas fa-users',
                'color': '#17a2b8',
                'description': 'المناسبات والأنشطة الاجتماعية',
                'is_location_based': True
            },
            {
                'name': 'ترفيه',
                'name_en': 'Entertainment',
                'icon': 'fas fa-gamepad',
                'color': '#ffc107',
                'description': 'الأنشطة الترفيهية والألعاب',
                'is_location_based': False
            },
            {
                'name': 'زيارات',
                'name_en': 'Visits',
                'icon': 'fas fa-map-marker-alt',
                'color': '#dc3545',
                'description': 'الزيارات والمواعيد',
                'is_location_based': True
            },
            {
                'name': 'مناسبات',
                'name_en': 'Events',
                'icon': 'fas fa-calendar-alt',
                'color': '#6f42c1',
                'description': 'المناسبات والاحتفالات',
                'is_location_based': True
            },
            {
                'name': 'سفر',
                'name_en': 'Travel',
                'icon': 'fas fa-plane',
                'color': '#fd7e14',
                'description': 'السفر والرحلات',
                'is_location_based': True
            },
            {
                'name': 'طوارئ',
                'name_en': 'Emergency',
                'icon': 'fas fa-exclamation-triangle',
                'color': '#e74c3c',
                'description': 'المهام العاجلة والطوارئ',
                'is_location_based': False
            },
            {
                'name': 'عمل تطوعي',
                'name_en': 'Volunteer',
                'icon': 'fas fa-hands-helping',
                'color': '#20c997',
                'description': 'الأعمال التطوعية والخيرية',
                'is_location_based': True
            },
            {
                'name': 'أدوية',
                'name_en': 'Medicine',
                'icon': 'fas fa-pills',
                'color': '#e83e8c',
                'description': 'تذكير بالأدوية والعلاج',
                'is_location_based': False
            },
            {
                'name': 'قراءة',
                'name_en': 'Reading',
                'icon': 'fas fa-book',
                'color': '#6c757d',
                'description': 'القراءة والكتب',
                'is_location_based': False
            },
            {
                'name': 'مشروعات',
                'name_en': 'Projects',
                'icon': 'fas fa-project-diagram',
                'color': '#495057',
                'description': 'المشروعات والأعمال',
                'is_location_based': False
            },
            {
                'name': 'مراجعة',
                'name_en': 'Review',
                'icon': 'fas fa-search',
                'color': '#6610f2',
                'description': 'مراجعة ومتابعة المهام',
                'is_location_based': False
            },
            {
                'name': 'تمارين ذهنية',
                'name_en': 'Mental Exercise',
                'icon': 'fas fa-brain',
                'color': '#e91e63',
                'description': 'التمارين الذهنية والتفكير',
                'is_location_based': False
            },
            {
                'name': 'ألعاب',
                'name_en': 'Games',
                'icon': 'fas fa-dice',
                'color': '#ff5722',
                'description': 'الألعاب والتسلية',
                'is_location_based': False
            },
            {
                'name': 'عمل',
                'name_en': 'Work',
                'icon': 'fas fa-briefcase',
                'color': '#795548',
                'description': 'مهام العمل والوظيفة',
                'is_location_based': True
            },
            {
                'name': 'صحة',
                'name_en': 'Health',
                'icon': 'fas fa-heartbeat',
                'color': '#f44336',
                'description': 'الصحة والعناية الطبية',
                'is_location_based': True
            },
            {
                'name': 'تسوق',
                'name_en': 'Shopping',
                'icon': 'fas fa-shopping-cart',
                'color': '#4caf50',
                'description': 'التسوق والمشتريات',
                'is_location_based': True
            },
            {
                'name': 'طبخ',
                'name_en': 'Cooking',
                'icon': 'fas fa-utensils',
                'color': '#ff9800',
                'description': 'الطبخ وإعداد الطعام',
                'is_location_based': False
            },
            {
                'name': 'تنظيف',
                'name_en': 'Cleaning',
                'icon': 'fas fa-broom',
                'color': '#607d8b',
                'description': 'التنظيف والترتيب',
                'is_location_based': False
            },
            {
                'name': 'مالية',
                'name_en': 'Finance',
                'icon': 'fas fa-dollar-sign',
                'color': '#4caf50',
                'description': 'الأمور المالية والمحاسبة',
                'is_location_based': False
            },
            {
                'name': 'شخصية',
                'name_en': 'Personal',
                'icon': 'fas fa-user',
                'color': '#9c27b0',
                'description': 'المهام الشخصية العامة',
                'is_location_based': False
            }
        ]

        created_count = 0
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'تم إنشاء التصنيف: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'التصنيف موجود مسبقاً: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'تم إنشاء {created_count} تصنيف جديد من أصل {len(categories)}')
        )
