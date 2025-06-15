"""
Sitemap configuration for HSG Notes
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages
    """
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        return ['home', 'about', 'accounts:login', 'accounts:signup']
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, obj):
        return None


class HomepageSitemap(Sitemap):
    """
    Sitemap for homepage with higher priority
    """
    priority = 1.0
    changefreq = 'daily'
    
    def items(self):
        return ['home']
    
    def location(self, item):
        return reverse(item)


# Sitemap registry
sitemaps = {
    'static': StaticViewSitemap,
    'homepage': HomepageSitemap,
}
