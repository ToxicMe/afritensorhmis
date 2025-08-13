from django import template

register = template.Library()

@register.filter
def mask_phone(value):
    """Mask the middle 4 digits of a phone number."""
    if value and len(value) >= 7:
        return value[:2] + "****" + value[-4:]
    return value


@register.filter
def mask_email(value):
    """Mask part of an email address."""
    if value and "@" in value:
        name, domain = value.split("@", 1)
        if len(name) > 2:
            masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
        else:
            masked_name = name[0] + "*"
        return masked_name + "@" + domain
    return value