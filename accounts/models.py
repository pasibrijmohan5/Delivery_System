from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifiers for authentication instead of usernames."""

    def create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", self.model.Roles.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        DELIVERY_PERSON = "delivery_person", "Delivery Person"
        CUSTOMER = "customer", "Customer"

    username = None
    email = models.EmailField(_("email address"), unique=True)
    # avatar_url = models.URLField(blank=True, null=True)

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CUSTOMER)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        
        # Ensure riders are marked as staff so they appear in admin/dashboards as expected
        if self.role == self.Roles.DELIVERY_PERSON:
            self.is_staff = True
            
        super().save(*args, **kwargs)

        if self.role == self.Roles.DELIVERY_PERSON:
            # Avoid circular import if any, though it's in the same file
            DeliveryPerson.objects.get_or_create(
                user=self,
                defaults={
                    'phone_number': 'N/A',
                    'vehicle_type': DeliveryPerson.VehicleType.BICYCLE,
                    'vehicle_plate_number': 'N/A'
                }
            )


class DeliveryPerson(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="delivery_profile"
    )
    # contact information
    phone_number = models.CharField(max_length=15, help_text="Contact number")

    # location
    current_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    last_location_update = models.DateTimeField(null=True, blank=True)



    # vehicle info
    class VehicleType(models.TextChoices):
        BICYCLE = "bicycle", "Bicycle"
        MOTORCYCLE = "motorcycle", "Motorcycle"
        CAR = "car", "Car"
        VAN = "van", "Van"
        TRUCK = "truck", "Truck"

    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices)
    vehicle_plate_number = models.CharField(max_length=20)
    vehicle_color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        default="black",
        help_text="Color of the vehicle",
    )

    # account status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="shipping_addresses"
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    location_name = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Home, Office, Friend's House")
    landmark = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Near the big white gate")
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    last_location_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("latitude", "longitude")]

    def __str__(self):
        return self.full_name
