from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class SignInForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Incorrect credentials.",
    }


class SignUpForm(UserCreationForm):
    username_conflict_message = "Username already exists."

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].error_messages["unique"] = self.username_conflict_message

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and get_user_model()._default_manager.filter(username__iexact=username).exists():
            raise forms.ValidationError(self.username_conflict_message, code="unique")
        return username
