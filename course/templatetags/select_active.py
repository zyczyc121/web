from django import template

register = template.Library()


@register.simple_tag
def select_active(current_entry, active_entry):
    if current_entry == active_entry:
        return "active"
    else:
        return ""
