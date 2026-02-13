from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class: str):
    """
    Return the form field rendered with additional CSS classes.
    Keeps existing widget attributes untouched.
    """

    attrs = field.field.widget.attrs.copy()
    existing = attrs.get("class", "")
    attrs["class"] = f"{existing} {css_class}".strip() if existing else css_class
    return field.as_widget(attrs=attrs)
