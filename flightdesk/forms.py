from django import forms
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe
from .models import Booking

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
        model = Booking
        fields = '__all__'
        widgets = {
            'ticket_image': PictureWidget(),
        }