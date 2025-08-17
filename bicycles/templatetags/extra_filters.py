from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    try:
        if not key or str(key).strip() == "":
            return 0
        return d.get(int(key), 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def percent(value, total):
    try:
        return (int(value) / int(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0
