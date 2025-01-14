from django.forms import ValidationError
from .models import *
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework import serializers
import random
from django.conf import settings
from django.apps import apps
from django.db.models import  Avg


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    specialty = serializers.CharField(required=False, allow_blank=True)  
    about = serializers.CharField(required=False, allow_blank=True)  
    profile = serializers.ImageField(required=False) 
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'role', 'specialty', 'about', 'profile','fee', 'stripe_customer_id']
        extra_kwargs = {
            'stripe_customer_id': {'read_only': True}
        }
    def validate(self, data):
        role = data.get('role')
        if role == 'doctor':
            if not data.get('specialty') or not data.get('about'):
                raise serializers.ValidationError({

                })
        return data
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'token': token.key,
            "message": "User registered successfully."
        }


class GenerateOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        otp = str(random.randint(0000, 9999))  
        OTP.objects.create(user=user, otp=otp)

        from django.core.mail import send_mail
        send_mail(
            'Password Reset OTP',
            f'Your OTP for password reset is {otp}. It is valid for 200 minutes.',
            'djangotesting5@gmail.com', 
            [email],
        )


# class ResetPasswordSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     otp = serializers.CharField(max_length=4)
#     new_password = serializers.CharField(write_only=True)
#     def validate(self, data):
#         email = data.get('email')
#         otp = data.get('otp')
#         try:
#             user = User.objects.get(email=email)
#             otp_entry = OTP.objects.filter(user=user, otp=otp).first()
#             if not otp_entry or not otp_entry.is_valid():
#                 raise serializers.ValidationError("Invalid or expired OTP.")
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Invalid email.")
#         return data
#     def save(self):
#         email = self.validated_data['email']
#         new_password = self.validated_data['new_password']
#         user = User.objects.get(email=email)
#         user.set_password(new_password)
#         user.save()
#         OTP.objects.filter(user=user).delete()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("Invalid email.")
            
        self.context['user'] = user
        
        otp_entry = OTP.objects.select_related('user').filter(
            user=user, 
            otp=otp
        ).first()
        
        if not otp_entry or not otp_entry.is_valid():
            raise serializers.ValidationError("Invalid or expired OTP.")
            
        return data
    def save(self):
        new_password = self.validated_data['new_password']
        user = self.context['user']
        user.set_password(new_password)
        user.save()
        OTP.objects.filter(user=user).delete()


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = '__all__'


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'specialty', 'about', 'profile']


class UserModelSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)  
    categories = CategoriesSerializer(read_only=True) 
    class Meta:
        model = UserModel
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)
    patient_name = serializers.CharField(source='patient.username', read_only=True)
    doctor = serializers.CharField(write_only=True)  
    patient = serializers.CharField(write_only=True)
    review_count = serializers.IntegerField()
    class Meta:
        model = Review
        fields = ['id', 'doctor', 'doctor_name', 'patient', 'patient_name',  'rating', 'comment', 'created_at','review_count']
        read_only_fields = ['created_at', 'doctor_name', 'patient_name', 'doctor_details', 'patient_details']
    def create(self, validated_data):
        doctor_username = validated_data.pop('doctor')
        patient_username = validated_data.pop('patient')

        User = apps.get_model(settings.AUTH_USER_MODEL)
        try:
            doctor = User.objects.get(username=doctor_username)
            patient = User.objects.get(username=patient_username)
        except User.DoesNotExist as e:
            raise serializers.ValidationError(str(e))

        return Review.objects.create(doctor=doctor, patient=patient, **validated_data)
    

class DoctorDetailSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'specialty', 'profile', 'average_rating', 'review_count']
    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     reviews = Review.objects.filter(doctor=instance)
    #     data['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    #     data['review_count'] = reviews.count()
    #     return data
    

class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.CharField(source='patient.username')
    doctor_specialty = serializers.CharField(source='doctor.specialty', read_only=True)
    doctor_profile_image = serializers.ImageField(source='doctor.profile', read_only=True)
    doctor = serializers.SlugRelatedField(
        slug_field='username',  
        queryset=User.objects.all(), 
    )

    class Meta:
        model = Appointment
        fields = ['id','doctor', 'patient', 'doctor_specialty', 'doctor_profile_image', 'status',"payment_status",'updated_at','created_at','date','time']

    def create(self, validated_data):
        patient = self.context['request'].user  
        validated_data['patient'] = patient
        return super().create(validated_data)


class PaymentProcessSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()
    payment_method_id = serializers.CharField(required=False)


class PaymentResponseSerializer(serializers.Serializer):
    client_secret = serializers.CharField()
    payment_intent_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class DoctorPaymentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.username', read_only=True)
    appointment_date = serializers.DateField(source='appointment.date', read_only=True)

    class Meta:
        model = DoctorPayment
        fields = ['id','doctor', 'doctor_name', 'patient_name', 'amount', 
                 'payment_date', 'appointment_date']

