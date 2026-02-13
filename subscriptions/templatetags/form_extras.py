from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class: str):
    attrs = field.field.widget.attrs.copy()
    existing = attrs.get("class", "")
    attrs["class"] = f"{existing} {css_class}".strip() if existing else css_class
    return field.as_widget(attrs=attrs)


@register.filter
def widget_input_type(field):
    return getattr(field.field.widget, "input_type", "")


@register.filter
def widget_class_name(field):
    return field.field.widget.__class__.__name__
