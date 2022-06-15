import random

from django import template

register = template.Library()


@register.simple_tag
def uniform(a, b):
    return random.uniform(a, b)


@register.simple_tag
def randint(a, b):
    return random.randint(a, b)


@register.simple_tag
def choice(*choices):
    return random.choice(choices)
