from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'phone', 'role', 'specialty', 'about', 'profile']

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'otp', 'created_at']

@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'pic']

@admin.register(UserModel)
class UserModelAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'categories')
    search_fields =  ('user__username', 'user__email', 'user__phone', 'user__specialty','user__role','categories__name')
    list_filter = ('categories',)
    ordering = ('user',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'patient', 'rating', 'comment', 'created_at')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'patient', 'date', 'time',  'payment_status','status' )

   
@admin.register(DoctorPayment)
class DoctorPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor',"appointment","amount","payment_date")