from django import template

register = template.Library()

@register.filter
def get_item_name(dictionary, key):
    ret_list = []
    dict = dictionary.get(key)
    if dict:
        for item in dict:
            ret_list.append(item.name)
    return ret_list


@register.filter
def times(number, string):
    return string * number


@register.filter(name='format_access_level')
def format_access_level(value):
    if not value:
        return "N/A"
    if isinstance(value, str) and value.startswith('level-'):
        level_number = value.split('-')[1]
        return f"Level {level_number.capitalize()}"
    return value
