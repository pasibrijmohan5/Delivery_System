from rest_framework import serializers
from .models import CustomUser, DeliveryPerson, ShippingAddress
from django.contrib.auth import authenticate


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    shipping_address = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role', 'first_name', 'last_name', 'date_joined', 'shipping_address']
        read_only_fields = ['id', 'date_joined', 'role']

    def get_shipping_address(self, obj):
        address = obj.shipping_addresses.last() # Get the most recent one
        if address:
            return ShippingAddressSerializer(address).data
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=CustomUser.Roles.choices, default=CustomUser.Roles.CUSTOMER)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'first_name', 'last_name', 'role']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', CustomUser.Roles.CUSTOMER)
        )
        return user

class DeliveryPersonSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = DeliveryPerson
        fields = '__all__'
