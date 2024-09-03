# from django import forms
# from django.conf import settings
# from django.utils.text import slugify
# from django.core.files.base import ContentFile
# from django.utils.safestring import mark_safe
# from .models import MyBooking

# class PictureWidget(forms.widgets.Widget):
#     def render(self, name, value, attrs=None):
#         if str(value) == '':
#             html1 = "<img id='id_image' style='display:block' class='rounded float-left d-block'/>"
#         else:
#             html1 = "<img id='id_image' style='display:block' class='rounded float-left d-block' src='" + settings.MEDIA_URL + str(value) + "'/>"
#         return mark_safe(html1)

# class MyForm(forms.ModelForm):

#     image_container = forms.ImageField(required=False, widget=forms.HiddenInput())
#     class Meta:
#         model = MyBooking
#         fields = '__all__'
#         widgets = {
#             'ticket_image': PictureWidget(),
#         }

# # forms.py

# class DateTimeInput(forms.DateTimeInput):
#     input_type = 'datetime-local'

# class YourModelForm(forms.ModelForm):
#     class Meta:
#         model = MyBooking
#         fields = ['departure_date', 'departure_time_hours', 'departure_time_minutes']
#         widgets = {
#             'departure_date': forms.DateInput(),
#             'departure_time_hours': forms.NumberInput(attrs={'min': 0, 'max': 23}),
#             'departure_time_minutes': forms.NumberInput(attrs={'min': 0, 'max': 59}),
#         }


from django import forms
from .models import CallLog, Campaign, BillingInformation, Booking, Email
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django_summernote.widgets import SummernoteWidget

class CallLogForm(forms.ModelForm):
    class Meta:
        model = CallLog
        fields = ['converted', 'name', 'phone', 'email', 'tag', 'concern']

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['code']

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['code']


class StaffCreationForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15)
    group = forms.ChoiceField(choices=[('agent', 'Agent'), ('supervisor', 'Supervisor')])
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'group', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.last_name = self.cleaned_data.get('phone_number')
        if commit:
            user.save()
            group_name = self.cleaned_data['group']
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return user

class BillingInformationForm(forms.ModelForm):
    class Meta:
        model = BillingInformation
        fields = [
            'card_type',
            'card_holder_name',
            'card_holder_number',
            'email',
            'card_number',
            'expiry_date',
            'card_cvv',
            'primary_address',
            'country',
            'zipcode',
        ]
        widgets = {
            'expiry_date': forms.TextInput(attrs={'placeholder': 'MM/YY'}),
        }

    # Custom validations can be added here if needed
    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        if len(card_number) != 16 or not card_number.isdigit():
            raise forms.ValidationError("Enter a valid 16-digit card number.")
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        # Assuming expiry date format is MM/YY
        if not expiry_date or len(expiry_date) != 5 or expiry_date[2] != '/':
            raise forms.ValidationError("Enter a valid expiry date in MM/YY format.")
        return expiry_date

    def clean_card_cvv(self):
        card_cvv = self.cleaned_data.get('card_cvv')
        if len(card_cvv) not in [3, 4] or not card_cvv.isdigit():
            raise forms.ValidationError("Enter a valid 3 or 4 digit CVV.")
        return card_cvv

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status', 'currency', 'mco', 'regarding_flight', 'regarding_hotel', 'regarding_vehicle', 'subcategory']
        # Add or remove fields as necessary

class EmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = ['subject', 'recipient', 'body']
        widgets = {
            'body': SummernoteWidget(),
        }