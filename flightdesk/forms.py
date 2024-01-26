from django import forms
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe
from .models import MyBooking

class PictureWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if str(value) == '':
            html1 = "<img id='id_image' style='display:block' class='rounded float-left d-block'/>"
        else:
            html1 = "<img id='id_image' style='display:block' class='rounded float-left d-block' src='" + settings.MEDIA_URL + str(value) + "'/>"
        return mark_safe(html1)

class MyForm(forms.ModelForm):

    image_container = forms.ImageField(required=False, widget=forms.HiddenInput())
    class Meta:
        model = MyBooking
        fields = '__all__'
        widgets = {
            'ticket_image': PictureWidget(),
        }

# forms.py

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class YourModelForm(forms.ModelForm):
    class Meta:
        model = MyBooking
        fields = ['departure_date', 'departure_time_hours', 'departure_time_minutes']
        widgets = {
            'departure_date': forms.DateInput(),
            'departure_time_hours': forms.NumberInput(attrs={'min': 0, 'max': 23}),
            'departure_time_minutes': forms.NumberInput(attrs={'min': 0, 'max': 59}),
        }
