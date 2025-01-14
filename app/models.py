import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings

class User(AbstractUser):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=11, unique=True)
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES,blank=True,null=True)
    specialty = models.CharField(max_length=255, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    profile = models.ImageField(upload_to="profiles/", blank=True, null=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True,null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    def is_doctor(self):
        return self.role == 'doctor'
    def is_patient(self):
        return self.role == 'patient'
    def __str__(self):
        return f"{self.username} ({self.role})"
    

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    def is_valid(self):
        return now() < self.created_at + timedelta(minutes=200)


class Categories(models.Model):
    name = models.CharField(max_length=255, unique=True)
    pic = models.ImageField(upload_to="categories/", unique=True)
    def __str__(self):
        return self.name
    
    
class UserModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    categories=models.ForeignKey(Categories, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.username} - {self.categories.name}"
    

class Review(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_as_doctor')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_as_patient')
    rating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'Review by {self.patient.username} for {self.doctor.username}'
    
    
class Appointment(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_as_patient")
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_as_doctor")
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=15, choices=status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(max_length=15, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True)

    def __str__(self):
        return f"Appointment: {self.patient.username} with {self.doctor.username} on {self.date} at {self.time}"


class DoctorPayment(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of ${self.amount} from  Dr. {self.doctor.username}"



  