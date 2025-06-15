from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def multiply(value, arg):
    """ضرب قيمتين"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """قسمة قيمتين"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """حساب النسبة المئوية"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def safe_widthratio(value, max_value, max_width):
    """نسخة آمنة من widthratio"""
    try:
        if not value or not max_value or float(max_value) == 0:
            return 0
        ratio = float(value) / float(max_value)
        return min(ratio * float(max_width), float(max_width))
    except (ValueError, TypeError):
        return 0
