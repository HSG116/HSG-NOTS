"""
URL configuration for task_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard_redirect
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.contrib.sitemaps.views import sitemap
from .sitemaps import sitemaps

@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /about/",
        "Allow: /accounts/signup/",
        "Allow: /accounts/login/",
        "",
        "Disallow: /admin/",
        "Disallow: /accounts/logout/",
        "Disallow: /tasks/",
        "Disallow: /ai/",
        "Disallow: /media/",
        "",
        "# HSG Notes - نظام إدارة المهام الذكي",
        "# Developed by HSG Company",
        "# Website: https://hsg-ashy.vercel.app/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('accounts/', include('accounts.urls')),
    path('tasks/', include('tasks.urls')),
    path('ai/', include('ai_assistant.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
