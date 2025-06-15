"""
Context processors for making global variables available in templates
"""
from django.conf import settings


def site_settings(request):
    """
    Add site configuration to template context
    """
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'HSG Notes'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', 'نظام إدارة المهام الذكي'),
        'COMPANY_NAME': getattr(settings, 'COMPANY_NAME', 'HSG Company'),
        'COMPANY_WEBSITE': getattr(settings, 'COMPANY_WEBSITE', 'https://hsg-ashy.vercel.app/'),
        'COMPANY_LOGO': getattr(settings, 'COMPANY_LOGO', 'https://i.postimg.cc/6QW52R6Z/1000023429.png'),
        'SITE_ICON': getattr(settings, 'SITE_ICON', 'https://i.postimg.cc/90zyZYzP/note-1-1.png'),
        'COMPANY_EMAIL': getattr(settings, 'COMPANY_EMAIL', 'cpshzt@gmail.com'),
        'COMPANY_WHATSAPP': getattr(settings, 'COMPANY_WHATSAPP', 'https://wa.me/message/4TYV7IWEUNAXN1'),
        'COMPANY_YOUTUBE': getattr(settings, 'COMPANY_YOUTUBE', 'https://www.youtube.com/@HSG-NEW'),
        'COMPANY_TIKTOK': getattr(settings, 'COMPANY_TIKTOK', 'https://www.tiktok.com/@hsg_new'),
    }
