from rest_framework import serializers
from .models import Category, Product, Order, OrderItem, Payment
from accounts.serializers import UserSerializer, DeliveryPersonSerializer
from accounts.models import ShippingAddress

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['categories'] = CategorySerializer(instance.categories.all(), many=True).data
        return rep

class OrderItemSerializer(serializers.ModelSerializer):
    get_total_price = serializers.ReadOnlyField()
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'get_total_price']
        read_only_fields = ['id', 'product_name', 'price']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    delivery_person_details = DeliveryPersonSerializer(source='delivery_person', read_only=True)
    shipping_address_details = ShippingAddressSerializer(source='shipping_address', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'user', 'user_details', 'status', 
            'subtotal', 'tax', 'shipping_cost', 'total', 
            'created_at', 'updated_at', 'delivery_person', 'delivery_person_details',
            'shipping_address', 'shipping_address_details',
            'items', 'payment'
        ]
        read_only_fields = ['id', 'order_id', 'user', 'status', 'created_at', 'updated_at']
