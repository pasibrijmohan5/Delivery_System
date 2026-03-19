from django.contrib.auth import get_user_model
from main.models import Product, Order, OrderItem, Payment
from main.serializers import OrderSerializer
import uuid

User = get_user_model()
user = User.objects.first()
product = Product.objects.first()

order = Order.objects.create(
    user=user,
    order_id=f'ORD-{uuid.uuid4().hex[:8].upper()}',
    subtotal=product.price,
    tax=0,
    shipping_cost=50,
    total=product.price + 50
)

OrderItem.objects.create(
    order=order,
    product=product,
    product_name=product.name,
    price=product.price,
    quantity=1
)

Payment.objects.create(
    order=order,
    method='cod',
    status='pending',
    purchase_order_id=order.order_id,
    transaction_id=f'COD-{uuid.uuid4().hex[:8].upper()}',
    pidx=f'PIDX-{uuid.uuid4().hex[:8].upper()}',
    amount=order.total
)

serializer = OrderSerializer(order)
print('SUCCESS SERIALIZING')
print(serializer.data)
