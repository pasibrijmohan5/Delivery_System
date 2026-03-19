from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
import uuid
import requests

from .models import Category, Product, Order, OrderItem, Payment
from accounts.models import CustomUser, DeliveryPerson, ShippingAddress
from .serializers import CategorySerializer, ProductSerializer, OrderSerializer


class IsAdminUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == CustomUser.Roles.ADMIN)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Roles.ADMIN:
            return Order.objects.all().order_by('-created_at')
        elif user.role == CustomUser.Roles.DELIVERY_PERSON:
            return Order.objects.filter(delivery_person__user=user).order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        try:
            items_data = request.data.get('items', [])
            if not items_data:
                return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            subtotal = 0
            order_items = []
            for item in items_data:
                try:
                    product = Product.objects.get(id=item['product_id'])
                    qty = item.get('quantity', 1)
                    price = product.price
                    subtotal += price * qty
                    order_items.append({
                        'product': product,
                        'product_name': product.name,
                        'price': price,
                        'quantity': qty
                    })
                except Product.DoesNotExist:
                    return Response({'error': f"Product {item['product_id']} not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            tax = 0
            shipping_cost = 50
            total = subtotal + tax + shipping_cost

            # Handle Shipping Address
            shipping_data = request.data.get('shipping_address')
            shipping_address = None
            if shipping_data:
                shipping_address, created = ShippingAddress.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'full_name': shipping_data.get('full_name', request.user.get_full_name()),
                        'phone': shipping_data.get('phone', ''),
                        'address_line': shipping_data.get('address_line', ''),
                        'location_name': shipping_data.get('location_name', ''),
                        'landmark': shipping_data.get('landmark', ''),
                        'city': shipping_data.get('city', ''),
                        'postal_code': shipping_data.get('postal_code', '00000'),
                    }
                )

            order = Order.objects.create(
                user=request.user,
                order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                subtotal=subtotal,
                tax=tax,
                shipping_cost=shipping_cost,
                total=total,
                shipping_address=shipping_address
            )

            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product_name'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            payment_method = request.data.get('payment_method', Payment.Method.COD)
            Payment.objects.create(
                order=order,
                method=payment_method,
                status=Payment.Status.PENDING if payment_method == Payment.Method.COD else Payment.Status.INITIATED,
                purchase_order_id=order.order_id,
                transaction_id=f"COD-{uuid.uuid4().hex[:8].upper()}" if payment_method == Payment.Method.COD else f"INIT-{uuid.uuid4().hex[:8].upper()}",
                pidx=f"PIDX-{uuid.uuid4().hex[:8].upper()}",
                amount=total
            )

            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
                
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'])
    def assign_rider(self, request, pk=None):
        if request.user.role != CustomUser.Roles.ADMIN:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        order = self.get_object()
        rider_id = request.data.get('rider_id')
        try:
            rider = DeliveryPerson.objects.get(id=rider_id)
            order.delivery_person = rider
            order.status = Order.Status.ON_THE_WAY
            order.save()
            return Response({'status': 'Rider assigned'}, status=status.HTTP_200_OK)
        except DeliveryPerson.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if request.user.role == CustomUser.Roles.DELIVERY_PERSON:
            if new_status in [Order.Status.DELIVERED]:
                order.status = new_status
                order.save()
                
                try:
                    payment = order.payment
                    if payment and payment.method == Payment.Method.COD:
                        payment.status = Payment.Status.SUCCESS
                        payment.save()
                except Payment.DoesNotExist:
                    pass

                return Response({'status': 'Order delivered'})
            return Response({'error': 'Invalid status update for rider'}, status=400)
            
        elif request.user.role == CustomUser.Roles.ADMIN:
            order.status = new_status
            order.save()
            return Response({'status': f'Order status updated to {new_status}'})
            
        return Response({'error': 'Unauthorized'}, status=403)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_khalti_payment(request):
    token = request.data.get('token')
    amount = request.data.get('amount')
    order_id = request.data.get('order_id')
    
    if not all([token, amount, order_id]):
        return Response({'error': 'Missing required fields'}, status=400)
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        payment = order.payment
        
        # In a real setup, you send a verification request to Khalti's API here.
        # But for this implementation, we will simulate a successful scenario.
        
        payment.status = Payment.Status.SUCCESS
        payment.transaction_id = token
        payment.pidx = request.data.get('pidx', f'PIDX-{uuid.uuid4().hex[:8].upper()}')
        payment.save()
        
        order.status = Order.Status.PAID
        order.save()
        
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True
        
        return Response({'status': 'Payment Verified successfully'})
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
