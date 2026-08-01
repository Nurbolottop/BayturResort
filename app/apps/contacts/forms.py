from django import forms
from django.utils.translation import gettext_lazy as _

from apps.contacts.models import ContactRequest, EventRequest, Subscriber


class HoneypotMixin(forms.Form):
    """Защита форм от спама без внешних сервисов (п. 10 ТЗ)."""

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError(_('Заявка отклонена.'))
        return ''


class ContactForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ('name', 'phone', 'email', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'field__input', 'placeholder': _('Ваше имя')}),
            'phone': forms.TextInput(attrs={'class': 'field__input', 'placeholder': '+996 ___ ______'}),
            'email': forms.EmailInput(attrs={'class': 'field__input', 'placeholder': 'email@example.com'}),
            'message': forms.Textarea(attrs={'class': 'field__input', 'rows': 4,
                                             'placeholder': _('Ваш вопрос')}),
        }


class EventRequestForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = EventRequest
        fields = (
            'name', 'company', 'phone', 'email', 'event_type', 'hall',
            'event_date', 'guests_count', 'need_accommodation', 'comment',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'field__input'}),
            'company': forms.TextInput(attrs={'class': 'field__input'}),
            'phone': forms.TextInput(attrs={'class': 'field__input', 'placeholder': '+996 ___ ______'}),
            'email': forms.EmailInput(attrs={'class': 'field__input'}),
            'event_type': forms.Select(attrs={'class': 'field__input'}),
            'hall': forms.Select(attrs={'class': 'field__input'}),
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'field__input'}),
            'guests_count': forms.NumberInput(attrs={'class': 'field__input', 'min': 1}),
            'comment': forms.Textarea(attrs={'class': 'field__input', 'rows': 3}),
        }


class SubscribeForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email', 'name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'field__input', 'placeholder': 'email@example.com'}),
            'name': forms.TextInput(attrs={'class': 'field__input', 'placeholder': _('Имя')}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # Повторную подписку не считаем ошибкой — просто реактивируем существующую.
        self.existing = Subscriber.objects.filter(email=email).first()
        return email

    def save(self, commit=True):
        existing = getattr(self, 'existing', None)
        if existing:
            existing.is_active = True
            existing.save(update_fields=['is_active', 'updated_at'])
            return existing
        return super().save(commit=commit)
