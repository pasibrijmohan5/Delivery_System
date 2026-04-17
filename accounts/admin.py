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
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'role'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ShippingAddress)
