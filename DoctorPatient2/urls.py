
from django.contrib import admin
from django.urls import path,include
from app.views import *
from rest_framework.routers import DefaultRouter


router=DefaultRouter()
router.register('signup',Signup,basename='signup')
router.register('login',Login,basename='login')
router.register('categories', CategoriesViewSet, basename='categories')
router.register('review', ReviewViewSet, basename='review')
router.register('user', UserModelViewSet, basename='user')
router.register('doctor_detail', DoctorDetailViewSet, basename='doctors')
router.register('appointment', AppointmentViewSet, basename='patient')
router.register('Doctor',DoctorViewSet, basename = 'Doctor')
router.register('payment', PaymentViewSet, basename='payment')
router.register('doctor_payment', DoctorPaymentViewSet, basename='doctor_payment')
router.register('generate-otp', GenerateOTPViewSet, basename='generate-otp')
router.register('reset-password', ResetPasswordViewSet, basename='reset-password')



urlpatterns = [
    path('',include(router.urls)),
    path('accounts/', include('allauth.urls'), name='socialaccount_signup'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('admin/', admin.site.urls),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    # path('forgot-password/', GenerateOTPView.as_view(), name='forgot-password'),
    # path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),



]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
