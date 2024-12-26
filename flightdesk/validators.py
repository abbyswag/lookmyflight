from django.core.validators import RegexValidator
from django.forms import ValidationError
import datetime

class CardExpiryValidator(RegexValidator):
    regex = r'^(0[1-9]|1[0-2])(/)(([0-9]){2})$'
    message = 'Expiry date must be in MM/YY format'

    def validate(self, value):
        super().validate(value)
        today = datetime.date.today()
        expiry = datetime.datetime.strptime(value, '%m/%y')
        expiry_date = expiry.replace(year=today.year)
        if expiry_date < today.replace(day=1):
            raise ValidationError('Expiry date cannot be in the past')