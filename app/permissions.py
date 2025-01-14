from rest_framework.permissions import BasePermission

class IsAuthenticatedAndDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'

class IsAuthenticatedAndPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'

class CanUpdateOwnData(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id
