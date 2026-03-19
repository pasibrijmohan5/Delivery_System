from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, DeliveryPerson, ShippingAddress

@admin.register(DeliveryPerson)
class DeliveryPersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'vehicle_plate_number', 'is_active')
    fields = ('user', 'phone_number', 'vehicle_type', 'vehicle_plate_number', 'is_active', 'is_verified')

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_staff']
    ordering = ['email']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ShippingAddress)
