from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics
from .models import NewBooking, Booking, BillingInformation
from .serializers import UserSerializer, NewBookingSerializer, BillingInformationSerializer
from django.contrib.auth import authenticate
from .permissions import IsAgentOrReadOnly, IsSupervisor

from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import Group
from .serializers import UserSerializer

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user)
            return Response({'token': token.key, 'user': serializer.data})
        else:
            return Response({'error': 'Invalid credentials'}, status=400)


# View bookings
class BookingListView(generics.ListAPIView):
    queryset = NewBooking.objects.all()
    serializer_class = NewBookingSerializer
    permission_classes = [IsAgentOrReadOnly | IsSupervisor]

# View a single NewBooking
class BookingDetailView(generics.RetrieveAPIView):
    queryset = NewBooking.objects.all()
    serializer_class = NewBookingSerializer
    permission_classes = [IsAgentOrReadOnly | IsSupervisor]

# Create a new NewBooking
class BookingCreateView(generics.CreateAPIView):
    queryset = NewBooking.objects.all()
    serializer_class = NewBookingSerializer
    permission_classes = [IsAgentOrReadOnly | IsSupervisor]

# Update a NewBooking
class BookingUpdateView(generics.UpdateAPIView):
    queryset = NewBooking.objects.all()
    serializer_class = NewBookingSerializer
    permission_classes = [IsAgentOrReadOnly | IsSupervisor]

# Delete a NewBooking
class BookingDeleteView(generics.DestroyAPIView):
    queryset = NewBooking.objects.all()
    serializer_class = NewBookingSerializer
    permission_classes = [IsAgentOrReadOnly | IsSupervisor]

# Create a new billing address
class BillingInformationCreateView(generics.CreateAPIView):
    queryset = BillingInformation.objects.all()
    serializer_class = BillingInformationSerializer
    permission_classes = [IsAuthenticated]

# View billing address for a specific booking
class BillingInformationDetailView(generics.RetrieveAPIView):
    queryset = BillingInformation.objects.all()
    serializer_class = BillingInformationSerializer
    lookup_field = 'booking__booking_id'  # Use booking_id as the lookup field
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    user = request.user
    agent_group = Group.objects.get(name='agent')
    supervisor_group = Group.objects.get(name='supervisor')

    if agent_group in user.groups.all():
        # Agent user
        agent_bookings = NewBooking.objects.filter(added_by=user)
        completed_bookings = agent_bookings.filter(status='confirmed')

        data = {
            'user_details': UserSerializer(user).data,
            'total_bookings': agent_bookings.count(),
            'completed_bookings': completed_bookings.count(),
        }
    elif supervisor_group in user.groups.all():
        # Supervisor user
        all_bookings = Booking.objects.all()
        completed_bookings = all_bookings.filter(status='confirmed')
        total_price = sum(booking.amount for booking in completed_bookings)

        data = {
            'user_details': UserSerializer(user).data,
            'total_bookings': all_bookings.count(),
            'completed_bookings': completed_bookings.count(),
            'total_price': total_price,
        }
    else:
        # User not in agent or supervisor group
        data = {
            'error': 'User group not authorized for this view.'
        }

    return Response(data)