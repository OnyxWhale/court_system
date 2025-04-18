from django import template
from stats.utils import format_timedelta_to_hours

register = template.Library()

@register.filter
def format_timedelta(value):
    return format_timedelta_to_hours(value)