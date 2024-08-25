from django.contrib.auth.models import User
from rest_framework import serializers
from .models import NewBooking
from .models import BillingInformation


class UserSerializer(serializers.ModelSerializer):
    user_group = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'user_group')

    def get_user_group(self, obj):
        groups = obj.groups.values_list('name', flat=True)
        return list(groups)
    
class NewBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewBooking
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class BillingInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingInformation
        fields = ['id', 'booking', 'card_type', 'card_holder_name', 'card_number', 'expiry_date', 'card_cvv', 'gateway_source', 'billing_address']
        read_only_fields = ['id']

    def create(self, validated_data):
        booking_id = self.context.get('booking_id')
        if booking_id:
            booking = NewBooking.objects.get(booking_id=booking_id)
            validated_data['booking'] = booking
        return super().create(validated_data)