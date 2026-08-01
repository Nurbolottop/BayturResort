from django import forms
from django.utils.translation import gettext_lazy as _

from apps.booking.models import Booking


class AvailabilitySearchForm(forms.Form):
    """Блок поиска: даты, гости. Используется в шапке, на главной и в /booking/."""

    check_in = forms.DateField(
        label=_('Заезд'),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'field__input'}),
    )
    check_out = forms.DateField(
        label=_('Выезд'),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'field__input'}),
    )
    adults = forms.IntegerField(
        label=_('Взрослых'), min_value=1, max_value=20, initial=2,
        widget=forms.NumberInput(attrs={'class': 'field__input'}),
    )
    children = forms.IntegerField(
        label=_('Детей'), min_value=0, max_value=10, initial=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'field__input'}),
    )

    def clean_children(self):
        return self.cleaned_data.get('children') or 0

    def clean(self):
        data = super().clean()
        check_in, check_out = data.get('check_in'), data.get('check_out')
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', _('Дата выезда должна быть позже даты заезда.'))
        return data


class BookingGuestForm(forms.ModelForm):
    """Данные гостя на шаге оформления брони."""

    promo_code = forms.CharField(
        label=_('Промокод'), required=False,
        widget=forms.TextInput(attrs={'class': 'field__input', 'placeholder': _('Промокод')}),
    )
    agree = forms.BooleanField(
        label=_('Я согласен с правилами проживания и политикой конфиденциальности'),
        required=True,
    )
    # Ловушка для ботов: настоящие гости это поле не видят и не заполняют
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Booking
        fields = (
            'guest_first_name', 'guest_last_name', 'guest_phone',
            'guest_email', 'guest_country', 'children_ages', 'comment',
        )
        widgets = {
            'guest_first_name': forms.TextInput(attrs={'class': 'field__input'}),
            'guest_last_name': forms.TextInput(attrs={'class': 'field__input'}),
            'guest_phone': forms.TextInput(attrs={'class': 'field__input', 'placeholder': '+996 ___ ______'}),
            'guest_email': forms.EmailInput(attrs={'class': 'field__input'}),
            'guest_country': forms.TextInput(attrs={'class': 'field__input'}),
            'children_ages': forms.TextInput(attrs={'class': 'field__input', 'placeholder': '4, 9'}),
            'comment': forms.Textarea(attrs={'class': 'field__input', 'rows': 3}),
        }

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError(_('Заявка отклонена.'))
        return ''

    def guest_data(self):
        data = self.cleaned_data
        return {
            'first_name': data['guest_first_name'],
            'last_name': data.get('guest_last_name', ''),
            'phone': data['guest_phone'],
            'email': data['guest_email'],
            'country': data.get('guest_country', ''),
            'children_ages': data.get('children_ages', ''),
            'comment': data.get('comment', ''),
        }
