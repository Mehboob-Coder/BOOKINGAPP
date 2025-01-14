from django.shortcuts import render
from django.contrib.auth import authenticate
from django.utils.timezone import now
from django.db.models import Count, Avg, Q
from rest_framework import viewsets, status, permissions 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import ModelViewSet
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from DoctorPatient2.settings import GOOGLE_REDIRECT_URL
from .models import User, Categories, Appointment, DoctorPayment
from .serializers import *
from .filters import GenericSearchFilter
from .pagination import Pagination
from .permissions import CanUpdateOwnData
import stripe
from django.db.models.functions import Coalesce
from django.db.models import Count, Avg,  Value


class Signup(viewsets.ViewSet):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                phone=serializer.validated_data['phone'],
                password=serializer.validated_data['password'],
                specialty=serializer.validated_data['specialty'],
                profile=serializer.validated_data['profile'],
                role = serializer.validated_data['role'],
                about=serializer.validated_data['about'],
                fee = serializer.validated_data['fee']

            )
            

            stripe_customer = stripe.Customer.create(
                email=user.email,
                name=user.username,
                phone=user.phone,
                metadata={
                    'user_id': user.id
                }
            )
            
            user.stripe_customer_id = stripe_customer.id
            user.save()
            
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
                    'stripe_customer_id': user.stripe_customer_id
                },
                'message': 'Signup successful'
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserModelViewSet(ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination
    filter_backends = [GenericSearchFilter]
    search_fields = ['user__username', 'user__phone', 'user__specialty','categories__name']  
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [CanUpdateOwnData()]
        return super().get_permissions()
    def perform_update(self, serializer):
        user = self.request.user
        if serializer.instance != user:
            raise PermissionDenied("You can only update your own data.")
        serializer.save()

    def get_queryset(self):
        return UserModel.objects.select_related(
            'user',
            'categories'
        ).all()


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = GOOGLE_REDIRECT_URL
    client_class = OAuth2Client


class Login(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        phone_or_email = request.data.get("username")
        password = request.data.get("password")
        if not phone_or_email or not password:
            return Response(
                {"error": "phone or email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_query = User.objects.filter(Q(phone=phone_or_email) | Q(email=phone_or_email)).first()
        user = None
        if user_query:
            user = authenticate(username=user_query.username, password=password)  
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            serializer = SignupSerializer(user)
            return Response(
                {
                    "token": token.key,
                    "message": "Login successful.",
                    "user_data": {
                        "username": user.username,
                        "email": user.email,
                        "phone": user.phone,
                        "stripe_customer_id": user.stripe_customer_id
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class GenerateOTPViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = GenerateOTPSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriesViewSet(ModelViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategoriesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 
    pagination_class = Pagination 



class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination
    def perform_create(self, serializer):

        serializer.save()
    # def get_queryset(self):
    #     return self.queryset.annotate(
    #         review_count = Subquery(
    #             Review.objects.filter(doctor=OuterRef('doctor'))
    #             .values('doctor')
    #             .annotate(count = Count('id'))
    #             .values('count')[:1]  
    #         )
    #     )
    
    def get_queryset(self):
        return Review.objects.select_related('doctor', 'patient').annotate(
            review_count=Count(
                'doctor__reviews_as_doctor',
                distinct=True
            )
        ).order_by('-created_at')
    
class DoctorDetailViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='doctor')  
    serializer_class = DoctorDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination

    # def get_queryset(self):
    #     queryset = self.queryset.annotate(
    #         review_count=Count('reviews_as_doctor'),
    #         average_rating=Avg('reviews_as_doctor__rating') 
    #     ).order_by("-average_rating")  
    #     return queryset



    def get_queryset(self):
        return User.objects.prefetch_related('reviews_as_doctor').filter(
            role='doctor'
        ).annotate(
            review_count=Count('reviews_as_doctor', distinct=True),
            average_rating=Coalesce(
                Avg('reviews_as_doctor__rating'),
                Value(0.0)
            )).order_by('-average_rating')




class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # permission_classes = [AllowAny]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        queryset = Appointment.objects.select_related(
            'patient', 'doctor'
        ).filter(
            # patient=16
            patient=self.request.user
        ).order_by("time")

        search_date = self.request.query_params.get("date")
        search_time = self.request.query_params.get("time")
        search_status = self.request.query_params.get("status")

        if search_date:
            queryset = queryset.filter(date=search_date)
        if search_time:
            queryset = queryset.filter(time=search_time)
        if search_status:
            queryset = queryset.filter(status=search_status)

        return queryset

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

    @action(detail=False, methods=['get'])
    def approved(self, request):
        queryset = self.get_queryset().filter(status="approved")
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)



# class DoctorViewSet(viewsets.ViewSet):
#     permission_classes = [permissions.IsAuthenticated]
#     def list(self, request):
#         appointments = Appointment.objects.filter(doctor=request.user)
#         serializer = AppointmentSerializer(appointments, many=True)
#         return Response(serializer.data)

#     @action(detail=True, methods=['post'])
#     def manage(self, request, pk=None):

#         try:
#             appointment = Appointment.objects.get(pk=pk, doctor=request.user)
#         except Appointment.DoesNotExist:
#             return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

#         action = request.data.get("action")
#         if action == "approve":
#             appointment.status = "approved"
#             appointment.time = request.data.get("time", appointment.time)
#         elif action == "cancel":
#             appointment.status = "cancelled"
#         elif action == "complete":
#             if appointment.date < now().date() or (appointment.date == now().date() and appointment.time <= now().time()):
#                 appointment.status = "completed"
#             elif appointment.date is None or appointment.time is None:
#                 return Response({"error": "Appointment date or time is not set."},status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 return Response({"error": "Cannot mark future appointments as completed."}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({"error": "Invalid action. Use 'approve', 'cancel', or 'complete'."}, status=status.HTTP_400_BAD_REQUEST)

#         appointment.save()
#         return Response(AppointmentSerializer(appointment).data)


class DoctorViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        static_doctor = User.objects.get(id=19)  

        return Appointment.objects.select_related(
            'doctor', 'patient'
        ).filter(
            doctor=self.request.user
            # doctor=static_doctor
        )

    def list(self, request):
        appointments = self.get_queryset()
        serializer = self.serializer_class(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def manage(self, request, pk=None):
        VALID_ACTIONS = {
            "approve": "approved",
            "cancel": "cancelled",
            "complete": "completed"
        }
        
        try:
            appointment = self.get_queryset().get(pk=pk)
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get("action")
        if action not in VALID_ACTIONS:
            return Response(
                {"error": f"Invalid action. Use {', '.join(VALID_ACTIONS.keys())}."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if action == "complete":
            current_time = now()
            if appointment.date is None or appointment.time is None:
                return Response(
                    {"error": "Appointment date or time is not set."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if appointment.date > current_time.date() or (
                appointment.date == current_time.date() and 
                appointment.time > current_time.time()
            ):
                return Response(
                    {"error": "Cannot mark future appointments as completed."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        appointment.status = VALID_ACTIONS[action]
        if action == "approve":
            appointment.time = request.data.get("time", appointment.time)
        
        appointment.save()
        return Response(self.serializer_class(appointment).data)



stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def list(self, request):
        appointments = Appointment.objects.filter(
            patient=request.user
        ).exclude(stripe_payment_intent_id__isnull=True)
        
        payment_data = []
        for appointment in appointments:
            payment_data.append({
                'appointment_id': appointment.id,
                'doctor_name': appointment.doctor.username,
                'amount': appointment.payment_amount,
                'payment_status': appointment.payment_status,
                'payment_date': appointment.updated_at,
                'payment_intent_id': appointment.stripe_payment_intent_id
            })
        
        return Response(payment_data)

    @action(detail=False, methods=['post'])
    def create_payment_method(self, request):
        try:
            test_tokens = {
                'visa': 'tok_visa',
                'visa_debit': 'tok_visa_debit',
                'mastercard': 'tok_mastercard',
                'amex': 'tok_amex',
                'discover': 'tok_discover',
                'jcb': 'tok_jcb'
            }

            required_fields = {
                'card_type': 'card type',
                'card_number': '0000000000000000',
                'card_holder_name': 'holder name',
                'exp_month': 'expiry month',
                'exp_year': 'expiry year',
                'cvv': 'cvv or cvc'
            }
            
            missing_fields = {
                field: example for field, example in required_fields.items()
                if not request.data.get(field)
            }
            
            if missing_fields:
                return Response({
                    'status': 'failed',
                    'message': 'Missing required fields:',
                    'missing_fields': missing_fields
                }, status=400)

            card_type = request.data.get('card_type')
            card_holder_name = request.data.get('card_holder_name')
            token = test_tokens.get(card_type, 'tok_visa')

            card_number = request.data.get('card_number', '')
        
            if not card_number.isdigit() or len(card_number) != 16:
                return Response({
                    'status': 'failed',
                    'message': 'Please enter a valid 16-digit card number',
                    'format': {
                        'card_number': '1234567890123456'
                    }
                }, status=400)

            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={
                    'token': token
                },
                billing_details={
                    'name': card_holder_name
                }
            )

            return Response({
                'payment_method_id': payment_method.id,
                'card_type': payment_method.card.brand,
                'card_number': card_number,
                'card_holder_name': card_holder_name,
                'exp_month': request.data.get('exp_month'),
                'exp_year': request.data.get('exp_year'),
                'cvv': request.data.get('cvv'),
                'status': 'success'
            })

        except stripe.error.StripeError as e:
            return Response({
                'error': str(e),
                'status': 'failed'
            }, status=400)

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        appointment_id = request.data.get('appointment_id')
        payment_method_id = request.data.get('payment_method_id')

        appointment = Appointment.objects.get(
            id=appointment_id,
            patient=request.user
        )
        amount = int(appointment.doctor.fee * 100)
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            payment_method=payment_method_id,
            confirm=True,
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never'
            }
        )
        if intent.status == 'succeeded':
            DoctorPayment.objects.create(
                doctor=appointment.doctor,
                appointment=appointment,
                amount=amount / 100
            )
            appointment.status = 'approved'
            appointment.payment_status = 'paid'
            appointment.stripe_payment_intent_id = intent.id
            appointment.payment_amount = amount / 100
            appointment.save()
        return Response({
            'payment_intent_id': intent.id,
            'amount': amount / 100,
            'status': intent.status
        })


class DoctorPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorPaymentSerializer
    permission_classes = [IsAuthenticated]    

    def get_queryset(self):
        base_queryset = DoctorPayment.objects.select_related('doctor', 'appointment')
        if self.request.user.role == 'doctor':
            return base_queryset.filter(doctor=self.request.user)
        return base_queryset.filter(appointment__patient=self.request.user)

    def list(self, request):
        payments = self.get_queryset()
        data = [{
            'payment_id': payment.id,
            'doctor_name': payment.doctor.username,
            'amount': payment.amount,
            'payment_date': payment.payment_date,
            'appointment_date': payment.appointment.date,
        } for payment in payments]
        return Response(data)


