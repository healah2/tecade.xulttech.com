# # trainee/templatetags/custom_filters.py
# from django import template

# register = template.Library()

# @register.filter
# def get_item(dictionary, key):
#     """
#     Custom filter to get an item from a dictionary by its key.
#     Usage: {{ submissions_dict|get_item:assignment.id }}
#     """
#     return dictionary.get(key)

# @register.filter
# def split(value, delimiter=','):
#     """Split a string by delimiter and return list"""
#     if value:
#         return [item.strip() for item in value.split(delimiter) if item.strip()]
#     return []    

# from django import template

# register = template.Library()

# @register.filter
# def dict_get(d, key):
#     """Safely get value from a dictionary by key."""
#     if not d:
#         return ''
#     try:
#         return d.get(key, '')
#     except AttributeError:
#         return ''

# @register.filter
# def split(value, separator=','):
#     """
#     Splits a string into a list using the given separator.
#     Usage: {{ value|split:"," }}
#     """
#     if not value:
#         return []
#     return [item.strip() for item in value.split(separator)]
# trainee/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get item from dictionary."""
    if not dictionary:
        return ''
    return dictionary.get(key, '')

@register.filter
def dict_get(d, key):
    """Safely get value from a dictionary by key."""
    if not d:
        return ''
    try:
        return d.get(key, '')
    except AttributeError:
        return ''

@register.filter
def split(value, separator=','):
    """
    Splits a string by separator.
    Usage: {{ value|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in value.split(separator)]
