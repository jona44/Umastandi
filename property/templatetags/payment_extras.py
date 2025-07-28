import datetime
from django import template

register = template.Library()

@register.filter
def format_month(value):
    """Converts 'YYYY-MM' string to 'Month Year' format"""
    try:
        date_obj = datetime.datetime.strptime(value, "%Y-%m")
        return date_obj.strftime("%B %Y")
    except (ValueError, TypeError):
        return value  # Fallback if invalid
